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
        self._load_config()
        self._init_state()
    
    def _load_config(self):
        """加载配置"""
        output_config = config.DISPLAY_CONFIG.get('gesture_output', {})
        
        # 命令行输出配置
        self.enable_console_output = output_config.get('enable_console_output', True)
        self.console_format = output_config.get('console_format', 'simple')
        
        # Socket输出配置
        self.enable_socket_output = output_config.get('enable_socket_output', False)
        self.socket_host = output_config.get('socket_host', '127.0.0.1')
        self.socket_port = output_config.get('socket_port', None) or config.SOCKET_PORT
        self.socket_format = output_config.get('socket_format', 'simple')
    
    def _init_state(self):
        """初始化状态变量"""
        # 静态手势重复输出控制
        self.last_printed_gesture = {}  # {hand_id: gesture_key}
    
    def output_gesture_detection(self, gesture_result: Dict[str, Any], hand_id: str):
        """输出手势检测结果"""
        if not gesture_result:
            return
        
        gesture_info = self._extract_gesture_info(gesture_result, hand_id)
        
        # 检查是否需要跳过重复输出
        if self._should_skip_console_output(gesture_info):
            return
        
        # 执行输出
        self._output_to_console(gesture_info)
        self._output_to_socket(gesture_info)
        
        # 更新状态
        self._update_gesture_history(gesture_info)
    
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
    
    def _should_skip_console_output(self, gesture_info: Dict[str, Any]) -> bool:
        """检查是否应该跳过命令行输出"""
        if not self.enable_console_output:
            return True
            
        gesture_name = gesture_info['gesture']
        hand_id = gesture_info['hand_id']
        gesture_key = gesture_info['gesture_key']
        
        is_static_gesture = gesture_name in config.GESTURE_TYPES['static_gestures']
        return (is_static_gesture and 
                hand_id in self.last_printed_gesture and 
                self.last_printed_gesture[hand_id] == gesture_key)
    
    def _output_to_console(self, gesture_info: Dict[str, Any]):
        """输出到命令行"""
        if not self.enable_console_output or self._should_skip_console_output(gesture_info):
            return
            
        if self.console_format == 'json':
            self._print_json_format(gesture_info)
        else:
            self._print_simple_format(gesture_info)
    
    def _print_json_format(self, gesture_info: Dict[str, Any]):
        """打印JSON格式"""
        output_data = {
            'timestamp': time.time(),
            'event_type': 'gesture_detection',
            'hand_id': gesture_info['hand_id'],
            'gesture': gesture_info['gesture'],
            'hand_type': gesture_info['hand_type'],
            'confidence': gesture_info['confidence'],
            'details': gesture_info['details']
        }
        print(f"[GESTURE_DETECTED] {json.dumps(output_data, ensure_ascii=False)}")
    
    def _print_simple_format(self, gesture_info: Dict[str, Any]):
        """打印简单格式"""
        print(f"[GESTURE_DETECTED] {gesture_info['hand_type']} {gesture_info['hand_id']}: "
              f"{gesture_info['gesture']} (置信度: {gesture_info['confidence']:.1f}%)")
    
    def _output_to_socket(self, gesture_info: Dict[str, Any]):
        """输出到Socket"""
        if not self.enable_socket_output:
            return
            
        try:
            message = self._create_socket_message(gesture_info)
            send_message_to_server(message, self.socket_host, self.socket_port, silent=True)
        except Exception as e:
            self._handle_socket_error(e)
    
    def _create_socket_message(self, gesture_info: Dict[str, Any]) -> str:
        """创建Socket消息"""
        if self.socket_format == 'json':
            output_data = {
                'timestamp': time.time(),
                'event_type': 'gesture_detection',
                'hand_id': gesture_info['hand_id'],
                'gesture': gesture_info['gesture'],
                'hand_type': gesture_info['hand_type'],
                'confidence': gesture_info['confidence'],
                'details': gesture_info['details']
            }
            return json.dumps(output_data, ensure_ascii=False)
        else:
            return f"GESTURE|{gesture_info['hand_id']}|{gesture_info['gesture']}|{gesture_info['confidence']:.1f}"
    
    def _handle_socket_error(self, error: Exception):
        """处理Socket错误"""
        if self.enable_console_output:
            print(f"[GESTURE_OUTPUT] Socket发送失败: {error}")
    
    def _update_gesture_history(self, gesture_info: Dict[str, Any]):
        """更新手势历史"""
        if self.enable_console_output:
            self.last_printed_gesture[gesture_info['hand_id']] = gesture_info['gesture_key']
    
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
            
        if self.console_format == 'json':
            self._print_trail_json(trail_info)
        else:
            self._print_trail_simple(trail_info)
    
    def _print_trail_json(self, trail_info: Dict[str, Any]):
        """打印轨迹JSON格式"""
        output_data = {
            'timestamp': time.time(),
            'event_type': 'trail_change',
            'hand_id': trail_info['hand_id'],
            'hand_type': trail_info['hand_type'],
            'position': {'x': trail_info['position'][0], 'y': trail_info['position'][1]}
        }
        if trail_info['movement_data']:
            output_data.update(trail_info['movement_data'])
        print(f"[TRAIL_UPDATE] {json.dumps(output_data, ensure_ascii=False)}")
    
    def _print_trail_simple(self, trail_info: Dict[str, Any]):
        """打印轨迹简单格式"""
        position = trail_info['position']
        movement_info = ""
        if trail_info['movement_data'] and 'movement' in trail_info['movement_data']:
            mov = trail_info['movement_data']['movement']
            movement_info = f" 移动=({mov.get('dx', 0):+d},{mov.get('dy', 0):+d}) " \
                          f"距离={mov.get('distance', 0):.1f}"
        print(f"[TRAIL_UPDATE] {trail_info['hand_type']}_{trail_info['hand_id']}: "
              f"位置=({position[0]},{position[1]}){movement_info}")
    
    def _output_trail_to_socket(self, trail_info: Dict[str, Any]):
        """输出轨迹到Socket"""
        if not self.enable_socket_output:
            return
            
        try:
            message = self._create_trail_socket_message(trail_info)
            send_message_to_server(message, self.socket_host, self.socket_port, silent=True)
        except Exception as e:
            self._handle_socket_error(e)
    
    def _create_trail_socket_message(self, trail_info: Dict[str, Any]) -> str:
        """创建轨迹Socket消息"""
        if self.socket_format == 'json':
            output_data = {
                'timestamp': time.time(),
                'event_type': 'trail_change',
                'hand_id': trail_info['hand_id'],
                'hand_type': trail_info['hand_type'],
                'position': {'x': trail_info['position'][0], 'y': trail_info['position'][1]}
            }
            if trail_info['movement_data']:
                output_data.update(trail_info['movement_data'])
            return json.dumps(output_data, ensure_ascii=False)
        else:
            position = trail_info['position']
            return f"TRAIL|{trail_info['hand_id']}|{position[0]}|{position[1]}"
    
    def output_tracking_status(self, hand_id: str, status: str, details: Optional[Dict] = None):
        """输出追踪状态信息"""
        status_info = self._create_status_info(hand_id, status, details)
        
        self._output_status_to_console(status_info)
        self._output_status_to_socket(status_info)
    
    def _create_status_info(self, hand_id: str, status: str, details: Optional[Dict] = None) -> Dict[str, Any]:
        """创建状态信息"""
        return {
            'hand_id': hand_id,
            'status': status,
            'details': details or {}
        }
    
    def _output_status_to_console(self, status_info: Dict[str, Any]):
        """输出状态到命令行"""
        if not self.enable_console_output:
            return
            
        if self.console_format == 'json':
            self._print_status_json(status_info)
        else:
            self._print_status_simple(status_info)
    
    def _print_status_json(self, status_info: Dict[str, Any]):
        """打印状态JSON格式"""
        output_data = {
            'timestamp': time.time(),
            'event_type': 'tracking_status',
            'hand_id': status_info['hand_id'],
            'status': status_info['status'],
            'details': status_info['details']
        }
        print(f"[TRACKING_STATUS] {json.dumps(output_data, ensure_ascii=False)}")
    
    def _print_status_simple(self, status_info: Dict[str, Any]):
        """打印状态简单格式"""
        print(f"[TRACKING_STATUS] {status_info['hand_id']}: {status_info['status']}")
    
    def _output_status_to_socket(self, status_info: Dict[str, Any]):
        """输出状态到Socket"""
        if not self.enable_socket_output:
            return
            
        try:
            message = self._create_status_socket_message(status_info)
            send_message_to_server(message, self.socket_host, self.socket_port, silent=True)
        except Exception as e:
            self._handle_socket_error(e)
    
    def _create_status_socket_message(self, status_info: Dict[str, Any]) -> str:
        """创建状态Socket消息"""
        if self.socket_format == 'json':
            output_data = {
                'timestamp': time.time(),
                'event_type': 'tracking_status',
                'hand_id': status_info['hand_id'],
                'status': status_info['status'],
                'details': status_info['details']
            }
            return json.dumps(output_data, ensure_ascii=False)
        else:
            return f"STATUS|{status_info['hand_id']}|{status_info['status']}"
    
    def reset_hand_gesture_history(self, hand_id: str):
        """重置指定手的手势历史记录"""
        if hand_id in self.last_printed_gesture:
            del self.last_printed_gesture[hand_id]
    
    def reset_all_gesture_history(self):
        """重置所有手的手势历史记录"""
        self.last_printed_gesture.clear()
    
    def output_trail_change_with_threshold(self, hand_id: str, current_pos: tuple, hand_type: str,
                                         last_output_positions: dict, output_frame_counters: dict,
                                         output_interval_frames: int, movement_threshold: float,
                                         output_format: str) -> bool:
        """
        输出轨迹变化到命令行和Socket（带阈值控制）
        Args:
            hand_id: 手部ID
            current_pos: 当前位置 (x, y)
            hand_type: 手部类型 (Left/Right)
            last_output_positions: 上次输出位置字典 {hand_id: (x, y)}
            output_frame_counters: 输出帧计数器字典 {hand_id: int}
            output_interval_frames: 输出间隔帧数
            movement_threshold: 移动阈值（像素）
            output_format: 输出格式 ('json' 或 'simple')
        Returns:
            是否输出了轨迹变化
        """
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
                    if output_format == 'json':
                        self._print_trail_json(trail_info)
                    else:
                        self._print_trail_simple(trail_info)
                
                # 输出到Socket
                self._output_trail_to_socket(trail_info)
                
                # 更新上次输出位置
                last_output_positions[hand_id] = current_pos
                return True
        else:
            # 第一次输出，记录位置但不输出
            last_output_positions[hand_id] = current_pos
        
        return False


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

def output_tracking_status(hand_id: str, status: str, details: Optional[Dict] = None):
    """便捷函数：输出追踪状态"""
    get_output_manager().output_tracking_status(hand_id, status, details)

def reset_hand_gesture_history(hand_id: str):
    """便捷函数：重置指定手的手势历史记录"""
    get_output_manager().reset_hand_gesture_history(hand_id)

def reset_all_gesture_history():
    """便捷函数：重置所有手的手势历史记录"""
    get_output_manager().reset_all_gesture_history()
