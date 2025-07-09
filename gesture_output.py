"""
手势输出管理器 - 统一管理手势信息的输出方式
支持命令行打印和Socket网络发送
"""

import json
import time
from typing import Dict, Any, Optional

import config
from socket_client import send_message_to_server


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
        self.socket_host = config.SOCKET_HOST
        self.socket_port = config.SOCKET_PORT
        self.socket_format = output_config.get('socket_format', 'simple')

    def output_gesture_detection(self, gesture_result: Dict[str, Any], hand_id: str):
        """输出手势检测结果"""
        if not gesture_result:
            return
        
        gesture_info = self._extract_gesture_info(gesture_result, hand_id)
        
        # 直接输出，不进行重复检测
        self._output_to_console(gesture_info)
        self._output_to_socket(gesture_info)
    
    def _extract_gesture_info(self, gesture_result: Dict[str, Any], hand_id: str) -> Dict[str, Any]:
        """提取手势信息"""
        return {
            'hand_id': hand_id,
            'gesture': gesture_result['gesture'],
            'hand_type': gesture_result['hand_type'],
            'confidence': gesture_result['confidence'],
            'details': gesture_result.get('details', {}),
            'gesture_key': f"{gesture_result['hand_type']}_{gesture_result['gesture']}"
        }
    
    def _output_to_console(self, gesture_info: Dict[str, Any]):
        """输出到命令行"""
        if not self.enable_console_output:
            return
            
        message = self._create_gesture_message(gesture_info, self.console_format)
        print(f"[GESTURE_DETECTED] {message}")
    
    def _output_to_socket(self, gesture_info: Dict[str, Any]):
        """输出到Socket"""
        if not self.enable_socket_output:
            return
            
        try:
            if self.socket_format == 'json':
                message = self._create_gesture_message(gesture_info, self.socket_format)
            else:
                # 简单格式保持原有的GESTURE|信息格式以保持向后兼容
                base_message = self._create_gesture_message(gesture_info, self.socket_format)
                message = f"GESTURE|{base_message}"
            send_message_to_server(message, self.socket_host, self.socket_port)
        except Exception as e:
            self._handle_socket_error(e)
    
    def _handle_socket_error(self, error: Exception):
        """处理Socket错误"""
        if self.enable_console_output:
            print(f"[GESTURE_OUTPUT] Socket发送失败: {error}")
    
    def output_trail_change(self, hand_id: str, position: tuple, hand_type: str, 
                           movement_data: Optional[Dict] = None):
        """输出轨迹变化信息"""
        trail_info = self._create_trail_info(hand_id, position, hand_type, movement_data)
        
        self._output_trail_to_console(trail_info)
        self._output_trail_to_socket(trail_info)
    
    def _create_trail_info(self, hand_id: str, position: tuple, hand_type: str, 
                          movement_data: Optional[Dict] = None) -> Dict[str, Any]:
        """创建轨迹信息"""
        return {
            'hand_id': hand_id,
            'hand_type': hand_type,
            'position': position,
            'movement_data': movement_data or {}
        }
    
    def _output_trail_to_console(self, trail_info: Dict[str, Any]):
        """输出轨迹到命令行"""
        if not self.enable_console_output:
            return
            
        message = self._create_trail_message(trail_info, self.console_format)
        print(f"[TRAIL_UPDATE] {message}")
    
    def _output_trail_to_socket(self, trail_info: Dict[str, Any]):
        """输出轨迹到Socket"""
        if not self.enable_socket_output:
            return
            
        try:
            if self.socket_format == 'json':
                message = self._create_trail_message(trail_info, self.socket_format)
            else:
                # 简单格式保持原有的TRAIL|hand_id|x|y格式以保持向后兼容
                position = trail_info['position']
                message = f"TRAIL|{trail_info['hand_id']}|{position[0]}|{position[1]}"
            send_message_to_server(message, self.socket_host, self.socket_port)
        except Exception as e:
            self._handle_socket_error(e)
    
    def _create_status_info(self, hand_id: str, status: str, details: Optional[Dict] = None) -> Dict[str, Any]:
        """创建状态信息"""
        return {
            'hand_id': hand_id,
            'status': status,
            'details': details or {}
        }
    
    def output_trail_change_with_threshold(self, hand_id: str, current_pos: tuple, hand_type: str,
                                         last_output_positions: dict, output_frame_counters: dict,
                                         output_interval_frames: int, movement_threshold: float,
                                         output_format: str) -> bool:
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
                # 构建移动数据
                movement_data = {
                    'movement': {
                        'dx': dx,
                        'dy': dy,
                        'distance': round(distance, 2)
                    },
                    'previous_position': {
                        'x': last_pos[0],
                        'y': last_pos[1]
                    }
                }
                
                # 创建轨迹信息对象
                trail_info = {
                    'hand_id': hand_id,
                    'hand_type': hand_type,
                    'position': current_pos,
                    'movement_data': movement_data
                }
                
                # 输出到命令行
                if self.enable_console_output:
                    message = self._create_trail_message(trail_info, output_format)
                    print(f"[TRAIL_UPDATE] {message}")
                
                # 输出到Socket
                self._output_trail_to_socket(trail_info)
                
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
            output_data = {
                'timestamp': time.time(),
                'hand_type': gesture_info['hand_type'].lower(),
                'confidence': gesture_info['confidence'],
                'gesture': gesture_info['gesture'],
                'details': gesture_info['details'],
                'type': 'gesture_detection',
            }
            return json.dumps(output_data, ensure_ascii=False)
        else:
            return (f"{gesture_info['hand_type']} {gesture_info['hand_id']}: "
                   f"{gesture_info['gesture']} (置信度: {gesture_info['confidence']:.1f}%)")
    
    def _create_trail_message(self, trail_info: Dict[str, Any], format_type: str) -> str:
        """创建轨迹变化消息（统一格式）"""
        if format_type == 'json':
            # 轨迹变化作为动态手势的一部分
            details = {}
            if trail_info['movement_data'] and 'movement' in trail_info['movement_data']:
                movement = trail_info['movement_data']['movement']
                details.update({
                    'dx': int(movement.get('dx', 0)),
                    'dy': int(movement.get('dy', 0)),
                    'distance': movement.get('distance', 0)
                })
                # 添加位置信息
                details.update({
                    'position': {'x': trail_info['position'][0], 'y': trail_info['position'][1]}
                })
            
            output_data = {
                'timestamp': time.time(),
                'hand_type': trail_info['hand_type'].lower(),
                'confidence': 100,  # 轨迹追踪时置信度为100
                'gesture': 'hand_close',  # 轨迹追踪对应hand_close手势
                'gesture_type': 'dynamic',
                'details': details
            }
            return json.dumps(output_data, ensure_ascii=False)
        else:
            position = trail_info['position']
            movement_info = ""
            if trail_info['movement_data'] and 'movement' in trail_info['movement_data']:
                mov = trail_info['movement_data']['movement']
                movement_info = f" 移动=({mov.get('dx', 0):+d},{mov.get('dy', 0):+d}) " \
                              f"距离={mov.get('distance', 0):.1f}"
            return (f"{trail_info['hand_type']}_{trail_info['hand_id']}: "
                   f"位置=({position[0]},{position[1]}){movement_info}")


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

def output_trail_change(hand_id: str, position: tuple, hand_type: str, movement_data: Optional[Dict] = None):
    """便捷函数：输出轨迹变化"""
    get_output_manager().output_trail_change(hand_id, position, hand_type, movement_data)

def output_trail_change_with_threshold(hand_id: str, current_pos: tuple, hand_type: str,
                                     last_output_positions: dict, output_frame_counters: dict,
                                     output_interval_frames: int, movement_threshold: float,
                                     output_format: str) -> bool:
    """便捷函数：输出轨迹变化到命令行和Socket（带阈值控制）"""
    return get_output_manager().output_trail_change_with_threshold(
        hand_id, current_pos, hand_type, last_output_positions, output_frame_counters,
        output_interval_frames, movement_threshold, output_format
    )
