"""
通用轨迹追踪模块 - 支持多种手势的轨迹追踪和平滑
"""

from collections import deque
from typing import Dict, Any, Optional, Tuple

from gestures.output import output_trail_change_with_threshold


class TrajectoryTracker:
    """通用轨迹追踪器，支持多种手势的轨迹追踪和平滑"""
    
    def __init__(self, tracking_config: Dict[str, Any], smoothing_config: Dict[str, Any]):
        """
        初始化轨迹追踪器
        Args:
            tracking_config: 追踪配置
            smoothing_config: 平滑配置
        """
        self.tracking_config = tracking_config
        self.smoothing_config = smoothing_config
        
        # 轨迹存储
        self.trail_points = {}  # {hand_id: deque of points}
        self.tracking_active = {}  # {hand_id: bool} - 追踪每只手的活动状态
        self.debounce_counters = {}  # {hand_id: int} - 去抖计数器
        self.gesture_triggered = {}  # {hand_id: bool} - 手势是否已被触发
        
        # 轨迹平滑相关
        self.smoothed_positions = {}  # {hand_id: (x, y)} - 平滑后的位置
        self.position_history = {}    # {hand_id: deque} - 位置历史用于窗口平滑
        
        # 命令行输出相关
        self.last_output_positions = {}  # {hand_id: (x, y)} - 上次输出的位置
        self.output_frame_counters = {}  # {hand_id: int} - 输出帧计数器
    
    def initialize_hand_tracking(self, hand_id: str):
        """初始化手部追踪状态"""
        if hand_id not in self.trail_points:
            self.trail_points[hand_id] = deque(maxlen=self.tracking_config['max_trail_points'])
            self.tracking_active[hand_id] = False
            self.debounce_counters[hand_id] = 0
            self.gesture_triggered[hand_id] = False
            # 初始化轨迹平滑相关
            self.smoothed_positions[hand_id] = None
            self.position_history[hand_id] = deque(maxlen=self.smoothing_config.get('smoothing_window', 5))
            # 初始化命令行输出相关
            self.last_output_positions[hand_id] = None
            self.output_frame_counters[hand_id] = 0
    
    def trigger_gesture(self, hand_id: str):
        """触发手势，开始轨迹追踪"""
        self.initialize_hand_tracking(hand_id)
        self.gesture_triggered[hand_id] = True
        self.trail_points[hand_id].clear()  # 清空之前的轨迹
        print(f"[TRACKING] 手势触发，开始轨迹追踪 {hand_id}")
    
    def update_tracking(self, hand_id: str, position: Tuple[int, int], is_active: bool, hand_type: str = "Unknown") -> Optional[Dict[str, Any]]:
        """
        更新轨迹追踪状态
        Args:
            hand_id: 手部ID
            position: 当前位置
            is_active: 是否处于活动状态（如握拳状态）
            hand_type: 手部类型
        Returns:
            轨迹结束信息（如果有）
        """
        if not self.tracking_config.get('enable_tracking', True):
            return None
        
        # 只有手势被触发后才开始追踪
        if not self.gesture_triggered.get(hand_id, False):
            return None
        
        was_active = self.tracking_active.get(hand_id, False)
        
        if is_active:
            # 当前是活动状态
            if not was_active:
                # 开始显示轨迹
                self.tracking_active[hand_id] = True
                self.debounce_counters[hand_id] = 0
                # 重置命令行输出状态
                self._reset_console_output(hand_id)
                print(f"[TRACKING] 开始显示 {hand_id} 的轨迹")
            
            # 应用轨迹平滑
            smoothed_position = self._apply_trajectory_smoothing(hand_id, position)
            
            # 添加平滑后的位置到轨迹
            self.trail_points[hand_id].append(smoothed_position)
            self.debounce_counters[hand_id] = 0
            
            # 输出轨迹变化，使用统一的输出管理器
            output_trail_change_with_threshold(
                hand_id, smoothed_position, hand_type,
                self.last_output_positions, self.output_frame_counters,
                self.tracking_config['output_interval_frames'], self.tracking_config['movement_threshold'],
            )
            
        else:
            # 当前不是活动状态
            if was_active:
                # 之前是活动状态，进入去抖阶段
                self.debounce_counters[hand_id] += 1

                if self.debounce_counters[hand_id] >= self.tracking_config['debounce_frames']:
                    # 去抖时间到，停止追踪并清除轨迹
                    self.tracking_active[hand_id] = False
                    self.trail_points[hand_id].clear()
                    self.debounce_counters[hand_id] = 0
                    self.gesture_triggered[hand_id] = False  # 重置手势触发状态
                    # 重置轨迹平滑状态
                    self._reset_smoothing_state(hand_id)
                    # 重置命令行输出状态
                    self._reset_console_output(hand_id)
                    
                    print(f"[TRACKING] 停止追踪 {hand_id} 的轨迹，清除显示")
        
        return None
    
    def _apply_trajectory_smoothing(self, hand_id: str, new_position: Tuple[int, int]) -> Tuple[int, int]:
        """应用轨迹平滑算法"""
        if not self.smoothing_config.get('enable_smoothing', True):
            return new_position
        
        # 添加新位置到历史记录
        self.position_history[hand_id].append(new_position)
        
        # 如果这是第一个位置，直接返回
        if self.smoothed_positions[hand_id] is None:
            self.smoothed_positions[hand_id] = new_position
            return new_position
        
        # 使用低通滤波器进行平滑
        prev_x, prev_y = self.smoothed_positions[hand_id]
        new_x, new_y = new_position
        
        # 应用加权平均
        smoothing_weight = self.smoothing_config.get('smoothing_weight', 0.3)
        smoothed_x = int(prev_x * (1 - smoothing_weight) + new_x * smoothing_weight)
        smoothed_y = int(prev_y * (1 - smoothing_weight) + new_y * smoothing_weight)

        smoothed_position = (smoothed_x, smoothed_y)
        self.smoothed_positions[hand_id] = smoothed_position
        
        return smoothed_position
    
    def _reset_smoothing_state(self, hand_id: str):
        """重置轨迹平滑状态"""
        if hand_id in self.smoothed_positions:
            self.smoothed_positions[hand_id] = None
        if hand_id in self.position_history:
            self.position_history[hand_id].clear()
    
    def _reset_console_output(self, hand_id: str):
        """重置命令行输出相关状态"""
        if hand_id in self.last_output_positions:
            self.last_output_positions[hand_id] = None
        if hand_id in self.output_frame_counters:
            self.output_frame_counters[hand_id] = 0
    
    def reset_hand_tracking(self, hand_id: str):
        """重置指定手部的追踪状态"""
        if hand_id in self.trail_points:
            self.trail_points[hand_id].clear()
            self.tracking_active[hand_id] = False
            self.debounce_counters[hand_id] = 0
            self.gesture_triggered[hand_id] = False
            # 清空该手的轨迹平滑相关
            self._reset_smoothing_state(hand_id)
            # 清空该手的命令行输出相关
            self._reset_console_output(hand_id)
    
    def reset_all_tracking(self):
        """重置所有手部的追踪状态"""
        self.trail_points.clear()
        self.tracking_active.clear()
        self.debounce_counters.clear()
        self.gesture_triggered.clear()
        # 清空轨迹平滑相关
        self.smoothed_positions.clear()
        self.position_history.clear()
        # 清空命令行输出相关
        self.last_output_positions.clear()
        self.output_frame_counters.clear()
    
    def get_tracking_status(self) -> Dict[str, Dict]:
        """获取所有手的追踪状态"""
        return {
            hand_id: {
                'active': self.tracking_active.get(hand_id, False),
                'trail_points': list(self.trail_points.get(hand_id, [])),
                'debounce_counter': self.debounce_counters.get(hand_id, 0),
                'gesture_triggered': self.gesture_triggered.get(hand_id, False),
                'smoothed_position': self.smoothed_positions.get(hand_id),
                'smoothing_enabled': self.smoothing_config.get('enable_smoothing', True)
            }
            for hand_id in self.trail_points.keys()
        }
    
    def get_trail_data_for_drawing(self):
        """获取用于绘制的轨迹数据"""
        return {
            'trail_points': self.trail_points,
            'tracking_active': self.tracking_active,
            'trail_thickness': self.tracking_config['trail_thickness']
        }
    
    def is_tracking_active(self, hand_id: str) -> bool:
        """检查指定手部是否正在追踪"""
        return self.tracking_active.get(hand_id, False)
    
    def is_gesture_triggered(self, hand_id: str) -> bool:
        """检查指定手部的手势是否已被触发"""
        return self.gesture_triggered.get(hand_id, False)
