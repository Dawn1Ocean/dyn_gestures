"""
张开到握拳手势检测器 - 动态手势，支持轨迹追踪
"""

import numpy as np
from collections import deque
from typing import List, Dict, Any, Optional, Tuple
from ..base import DynamicGestureDetector
from hand_utils import HandUtils
import config


class HandCloseDetector(DynamicGestureDetector):
    """张开到握拳手势检测器，支持轨迹追踪"""
    
    def __init__(self, variance_change_percent: float = 40, distance_multiplier: float = 0.7, 
                 history_length: int = 10, fist_hold_frames: int = 10):
        super().__init__("HandClose", history_length)
        self.variance_change_percent = variance_change_percent  # 方差减少的百分比阈值
        self.distance_multiplier = distance_multiplier  # 距离减少的倍数
        self.fist_hold_frames = fist_hold_frames  # 握拳状态需要保持的帧数
        
        # 轨迹追踪配置
        tracking_config = config.GESTURE_CONFIG['hand_close']['tracking_config']
        self.enable_tracking = tracking_config['enable_tracking']
        self.debounce_frames = tracking_config['debounce_frames']
        self.max_trail_points = tracking_config['max_trail_points']
        self.trail_thickness = tracking_config['trail_thickness']
        
        # 命令行输出配置
        self.enable_console_output = tracking_config['enable_console_output']
        self.output_interval_frames = tracking_config['output_interval_frames']
        self.movement_threshold = tracking_config['movement_threshold']
        self.output_format = tracking_config['output_format']
        
        # 全局轨迹存储（所有手共享）
        self.trail_points = {}  # {hand_id: deque of points}
        self.fist_active = {}   # {hand_id: bool} - 追踪每只手的握拳状态
        self.debounce_counters = {}  # {hand_id: int} - 去抖计数器
        self.gesture_triggered = {}  # {hand_id: bool} - 手势是否已被触发，用于控制轨迹显示
        
        # 命令行输出相关
        self.last_output_positions = {}  # {hand_id: (x, y)} - 上次输出的位置
        self.output_frame_counters = {}  # {hand_id: int} - 输出帧计数器
    
    def detect(self, landmarks: List[List[int]], hand_id: str, hand_type: str) -> Optional[Dict[str, Any]]:
        """检测张开到握拳手势，支持轨迹追踪"""
        # 初始化历史记录
        if hand_id not in self.history:
            self.history[hand_id] = {
                'variance_history': deque(maxlen=self.history_length),
                'distance_history': deque(maxlen=self.history_length),
                'fist_state': False,  # 是否处于握拳状态
                'fist_frames': 0,  # 握拳状态持续的帧数
                'closing_detected': False  # 是否已检测到闭合动作
            }
        
        # 初始化轨迹追踪相关
        if hand_id not in self.trail_points:
            self.trail_points[hand_id] = deque(maxlen=self.max_trail_points)
            self.fist_active[hand_id] = False
            self.debounce_counters[hand_id] = 0
            self.gesture_triggered[hand_id] = False
            # 初始化命令行输出相关
            self.last_output_positions[hand_id] = None
            self.output_frame_counters[hand_id] = 0
        
        hand_history = self.history[hand_id]
        
        # 使用HandUtils中的通用方法计算
        current_variance = HandUtils.calculate_fingertip_variance(landmarks)
        palm_center = HandUtils.calculate_palm_center(landmarks)
        current_distances = HandUtils.calculate_fingertip_distances(landmarks, palm_center)
        
        # 添加到历史记录
        hand_history['variance_history'].append(current_variance)
        hand_history['distance_history'].append(current_distances)
        
        # 检查当前是否为握拳状态
        current_is_fist = HandUtils.is_hand_closed(landmarks, current_distances)
        
        # 处理轨迹追踪（只有手势被触发后才记录轨迹）
        gesture_result = None
        
        # 状态机逻辑
        if not hand_history['closing_detected']:
            # 还未检测到闭合动作，检查是否从张开变为握拳
            if len(hand_history['variance_history']) >= self.history_length:
                # 计算基线（排除当前帧）
                baseline_variance = np.mean(list(hand_history['variance_history'])[:-1])
                
                baseline_distances = []
                distance_history = list(hand_history['distance_history'])[:-1]
                if distance_history:
                    for finger_idx in range(5):
                        finger_distances = [frame_distances[finger_idx] for frame_distances in distance_history]
                        baseline_distances.append(np.mean(finger_distances))
                
                # 计算变化（方差和距离都应该减少）
                variance_change_percent = ((baseline_variance - current_variance) / (baseline_variance + 1e-6)) * 100
                hand_is_closing = self._is_hand_closing(current_distances, baseline_distances)
                
                # 检查是否满足从张开到握拳的条件
                if (variance_change_percent > self.variance_change_percent and 
                    hand_is_closing and current_is_fist):
                    hand_history['closing_detected'] = True
                    hand_history['fist_state'] = True
                    hand_history['fist_frames'] = 1
                    # print(f"[DEBUG] 检测到握拳动作开始，方差减少: {variance_change_percent:.1f}%")
        
        else:
            # 已检测到闭合动作，现在检查握拳状态是否持续
            if current_is_fist:
                hand_history['fist_frames'] += 1
                if hand_history['fist_frames'] >= self.fist_hold_frames:
                    # 握拳状态持续足够长时间，触发手势
                    confidence = min(100, 70 + hand_history['fist_frames'])
                    
                    # 标记手势已被触发，开始轨迹追踪
                    if not self.gesture_triggered.get(hand_id, False):
                        self.gesture_triggered[hand_id] = True
                        self.trail_points[hand_id].clear()  # 清空之前的轨迹
                        # print(f"[TRACKING] HandClose手势触发，开始轨迹追踪 {hand_id}")
                    
                    # 重置状态但保持轨迹追踪
                    self._reset_detection_only(hand_id)
                    
                    gesture_result = {
                        'gesture': 'HandClose',
                        'hand_type': hand_type,
                        'confidence': confidence,
                        'details': {
                            'description': '张开到握拳',
                            'fist_hold_frames': hand_history['fist_frames'],
                            'required_frames': self.fist_hold_frames,
                            'tracking_active': self.gesture_triggered.get(hand_id, False)
                        }
                    }
            else:
                # 失去握拳状态，重置
                # print(f"[DEBUG] 失去握拳状态，重置检测")
                hand_history['closing_detected'] = False
                hand_history['fist_state'] = False
                hand_history['fist_frames'] = 0
        
        # 处理轨迹追踪（在状态机逻辑之后）
        self._update_tracking(hand_id, palm_center, current_is_fist, hand_type)
        
        return gesture_result
    
    def _is_hand_closing(self, current_distances: List[float], baseline_distances: List[float]) -> bool:
        """判断手是否正在闭合（距离是否显著减少）"""
        if not baseline_distances or len(baseline_distances) != 5:
            return False
        
        # 检查所有手指的距离是否都显著减少
        closing_count = sum(1 for i, dist in enumerate(current_distances) 
                          if dist < baseline_distances[i] * self.distance_multiplier)
        return closing_count == 5  # 所有5根手指的距离都必须减少
    
    def reset(self, hand_id: Optional[str] = None):
        """重置检测器状态"""
        if hand_id is None:
            self.history.clear()
            # 清空所有轨迹
            self.trail_points.clear()
            self.fist_active.clear()
            self.debounce_counters.clear()
            self.gesture_triggered.clear()
            # 清空命令行输出相关
            self.last_output_positions.clear()
            self.output_frame_counters.clear()
        elif hand_id in self.history:
            self.history[hand_id] = {
                'variance_history': deque(maxlen=self.history_length),
                'distance_history': deque(maxlen=self.history_length),
                'fist_state': False,
                'fist_frames': 0,
                'closing_detected': False
            }
            # 清空该手的轨迹
            if hand_id in self.trail_points:
                self.trail_points[hand_id].clear()
                self.fist_active[hand_id] = False
                self.debounce_counters[hand_id] = 0
                self.gesture_triggered[hand_id] = False
                # 清空该手的命令行输出相关
                self._reset_console_output(hand_id)
    
    def _reset_detection_only(self, hand_id: str):
        """只重置检测状态，保持轨迹追踪"""
        if hand_id in self.history:
            self.history[hand_id] = {
                'variance_history': deque(maxlen=self.history_length),
                'distance_history': deque(maxlen=self.history_length),
                'fist_state': False,
                'fist_frames': 0,
                'closing_detected': False
            }
    
    def _update_tracking(self, hand_id: str, palm_center: Tuple[int, int], current_is_fist: bool, hand_type: str = "Unknown"):
        """更新轨迹追踪状态"""
        if not self.enable_tracking:
            return
        
        # 只有手势被触发后才开始追踪
        if not self.gesture_triggered.get(hand_id, False):
            return
        
        was_active = self.fist_active.get(hand_id, False)
        
        if current_is_fist:
            # 当前是握拳状态
            if not was_active:
                # 开始显示轨迹
                self.fist_active[hand_id] = True
                self.debounce_counters[hand_id] = 0
                # 重置命令行输出状态
                self._reset_console_output(hand_id)
                print(f"[TRACKING] 开始显示 {hand_id} 的握拳轨迹")
            
            # 添加当前位置到轨迹
            self.trail_points[hand_id].append(palm_center)
            self.debounce_counters[hand_id] = 0
            
            # 输出轨迹变化到命令行
            if self.enable_console_output:
                HandUtils.output_trail_change(
                    hand_id, palm_center, hand_type,
                    self.last_output_positions, self.output_frame_counters,
                    self.output_interval_frames, self.movement_threshold,
                    self.output_format
                )
            
        else:
            # 当前不是握拳状态
            if was_active:
                # 之前是握拳状态，进入去抖阶段
                self.debounce_counters[hand_id] += 1
                
                if self.debounce_counters[hand_id] >= self.debounce_frames:
                    # 去抖时间到，停止追踪并清除轨迹
                    self.fist_active[hand_id] = False
                    self.trail_points[hand_id].clear()
                    self.debounce_counters[hand_id] = 0
                    self.gesture_triggered[hand_id] = False  # 重置手势触发状态
                    # 重置命令行输出状态
                    self._reset_console_output(hand_id)
                    print(f"[TRACKING] 停止追踪 {hand_id} 的握拳轨迹，清除显示")
    
    def get_tracking_status(self) -> Dict[str, Dict]:
        """获取所有手的追踪状态"""
        return {
            hand_id: {
                'active': self.fist_active.get(hand_id, False),
                'trail_points': list(self.trail_points.get(hand_id, [])),
                'debounce_counter': self.debounce_counters.get(hand_id, 0),
                'gesture_triggered': self.gesture_triggered.get(hand_id, False)
            }
            for hand_id in self.trail_points.keys()
        }
    
    def get_trail_data_for_drawing(self):
        """获取用于绘制的轨迹数据"""
        return {
            'trail_points': self.trail_points,
            'fist_active': self.fist_active,
            'trail_thickness': self.trail_thickness
        }
    
    def get_display_message(self, gesture_result: Dict[str, Any]) -> str:
        """获取张开到握拳手势的显示消息"""
        hand_type = gesture_result['hand_type']
        details = gesture_result.get('details', {})
        hold_frames = details.get('fist_hold_frames', 0)
        return f"{hand_type} Hand: Closing to Fist (Held: {hold_frames} frames)"
    
    def _reset_console_output(self, hand_id: str):
        """重置命令行输出相关状态"""
        if hand_id in self.last_output_positions:
            self.last_output_positions[hand_id] = None
        if hand_id in self.output_frame_counters:
            self.output_frame_counters[hand_id] = 0
