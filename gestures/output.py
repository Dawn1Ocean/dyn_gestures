"""
手势输出管理器 - 统一管理手势信息的输出方式
支持命令行打印和Socket网络发送
"""

import json
import time
from typing import Dict, Any

import config
from connect.socket_client import send_message_to_server


class GestureOutputManager:
    """手势输出管理器"""
    
    def __init__(self):
        """初始化输出管理器"""
        output_config = config.DISPLAY_CONFIG.get('gesture_output', {})
        
        # 命令行输出配置
        self.enable_console_output = output_config.get('enable_console_output', True)
        self.console_format = output_config.get('console_format', 'simple')
        
        # Socket输出配置
        self.enable_socket_output = output_config.get('enable_socket_output', False)
        self.socket_format = output_config.get('socket_format', 'simple')

    def output_gesture_detection(self, gesture_result: Dict[str, Any], hand_id: str):
        """输出手势检测结果"""
        if not gesture_result:
            return
        
        gesture_info = {
            'hand_id': hand_id,
            'gesture': gesture_result['gesture'],
            'hand_type': gesture_result['hand_type'],
            'confidence': gesture_result['confidence'],
            'details': gesture_result.get('details', {}),
            'gesture_key': f"{gesture_result['hand_type']}_{gesture_result['gesture']}",
            'type': gesture_result.get('type', 'gesture_detection'),
            'movement_data': gesture_result.get('movement_data', {}),
            'position': gesture_result.get('position', (0, 0))
        }
        
        # 直接输出，不进行重复检测
        message = self._create_gesture_message(gesture_info, self.console_format)
        if self.enable_console_output:
            if gesture_info['type'] == 'trail_change':
                print(f"[TRAIL_UPDATE] {message}")
            else:
                print(f"[GESTURE_DETECTED] {message}")

        if self.enable_socket_output:
            try:
                message = self._create_gesture_message(gesture_info, self.socket_format)
                if self.socket_format != 'json':
                    if gesture_info['type'] == 'trail_change':
                        # 对于轨迹变化，保持向后兼容的格式
                        position = gesture_info['position']
                        message = f"TRAIL|{gesture_info['hand_id']}|{position[0]}|{position[1]}"
                    else:
                        message = "GESTURE|" + message
                send_message_to_server(message, config.SOCKET_HOST, config.SOCKET_PORT)
            except Exception as e:
                if self.enable_console_output:
                    print(f"[GESTURE_OUTPUT] Socket发送失败: {e}")   
    
    def output_trail_change_with_threshold(self, hand_id: str, current_pos: tuple, hand_type: str,
                                         last_output_positions: dict, output_frame_counters: dict,
                                         output_interval_frames: int, movement_threshold: float) -> bool:
        # 检查输出间隔
        output_frame_counters[hand_id] = output_frame_counters.get(hand_id, 0) + 1
        if output_frame_counters[hand_id] < output_interval_frames:
            return False
        
        # 重置帧计数器
        output_frame_counters[hand_id] = 0
        
        last_pos = last_output_positions.get(hand_id)
        
        if last_pos is not None:
            # 计算移动距离
            dx = current_pos[0] - last_pos[0]
            dy = current_pos[1] - last_pos[1]
            distance = (dx**2 + dy**2)**0.5
            
            # 检查是否超过移动阈值
            if distance >= movement_threshold:
                # 创建轨迹信息对象
                trail_info = {
                    'hand_id': hand_id,
                    'hand_type': hand_type,
                    'confidence': 100,
                    'gesture': '',
                    'position': current_pos,
                    'movement_data': {
                        'movement': {
                            'dx': dx,
                            'dy': dy,
                            'distance': round(distance, 2)
                        },
                        'previous_position': {
                            'x': last_pos[0],
                            'y': last_pos[1]
                        }
                    },
                    'type': 'trail_change'
                }

                self.output_gesture_detection(trail_info, hand_id)
                
                # 更新上次输出位置
                last_output_positions[hand_id] = current_pos
                return True
        else:
            # 第一次输出，记录位置但不输出
            last_output_positions[hand_id] = current_pos
        
        return False

    def _create_gesture_message(self, gesture_info: Dict[str, Any], format_type: str) -> str:
        """创建手势检测消息（统一格式）"""
        if format_type == 'json':
            details = {}
            if gesture_info['type'] == 'trail_change' and gesture_info['movement_data'] and 'movement' in gesture_info['movement_data']:
                movement = gesture_info['movement_data']['movement']
                details.update({
                    'dx': int(movement.get('dx', 0)),
                    'dy': int(movement.get('dy', 0)),
                    'distance': movement.get('distance', 0)
                })
                # 添加位置信息
                details.update({'position': {'x': gesture_info['position'][0], 'y': gesture_info['position'][1]}})
            output_data = {
                'timestamp': time.time(),
                'hand_type': gesture_info['hand_type'].lower(),
                'confidence': gesture_info['confidence'],
                'gesture': gesture_info['gesture'],
                'details': details if details else gesture_info['details'],
                'type': gesture_info['type'],
            }
            return json.dumps(output_data, ensure_ascii=False)
        else:
            if gesture_info['type'] == 'trail_change':
                position = gesture_info['position']
                movement_info = ""
                if gesture_info['movement_data'] and 'movement' in gesture_info['movement_data']:
                    mov = gesture_info['movement_data']['movement']
                    movement_info = f" 移动=({mov.get('dx', 0):+d},{mov.get('dy', 0):+d}) " \
                                    f"距离={mov.get('distance', 0):.1f}"
                return (f"{gesture_info['hand_type']}_{gesture_info['hand_id']}: "
                        f"位置=({position[0]},{position[1]}){movement_info}")
            return (f"{gesture_info['hand_type']} {gesture_info['hand_id']}: "
                   f"{gesture_info['gesture']} (置信度: {gesture_info['confidence']:.1f}%)")

# 全局输出管理器实例
_output_manager = None

def get_output_manager() -> GestureOutputManager:
    """获取全局输出管理器实例"""
    global _output_manager
    if _output_manager is None:
        _output_manager = GestureOutputManager()
    return _output_manager

def output_gesture_detection(gesture_result: Dict[str, Any], hand_id: str):
    """便捷函数：输出手势检测结果"""
    get_output_manager().output_gesture_detection(gesture_result, hand_id)

def output_trail_change_with_threshold(hand_id: str, current_pos: tuple, hand_type: str,
                                     last_output_positions: dict, output_frame_counters: dict,
                                     output_interval_frames: int, movement_threshold: float) -> bool:
    """便捷函数：输出轨迹变化到命令行和Socket（带阈值控制）"""
    return get_output_manager().output_trail_change_with_threshold(
        hand_id, current_pos, hand_type, last_output_positions, output_frame_counters,
        output_interval_frames, movement_threshold
    )
