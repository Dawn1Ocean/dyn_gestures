"""
张开到握拳手势检测器 - 动态手势，支持轨迹追踪
"""

from collections import deque
from typing import List, Dict, Any, Optional

import numpy as np

from hand_utils import HandUtils
from trajectory_tracker import TrajectoryTracker
from ..base import DynamicGestureDetector


class HandCloseDetector(DynamicGestureDetector):
    """张开到握拳手势检测器，支持轨迹追踪"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("HandClose", config['history_length'], config['cooldown_frames'])
        self.variance_change_percent = config['variance_change_percent']  # 方差减少的百分比阈值
        self.distance_multiplier = config['distance_multiplier']  # 距离减少的倍数
        self.fist_hold_frames = config['fist_hold_frames']  # 握拳状态需要保持的帧数

        # 抗抖动配置
        self.jitter_tolerance_frames = config.get('jitter_tolerance_frames', 3)
        
        # 创建轨迹追踪器
        self.trajectory_tracker = TrajectoryTracker(
            config['tracking_config'],
            config.get('trajectory_smoothing', {})
        )
        
        # 抗抖动相关
        self.jitter_counters = {}     # {hand_id: int} - 抖动容忍计数器
    
    def detect(self, landmarks: List[List[int]], hand_id: str, hand_type: str) -> Optional[Dict[str, Any]]:
        """检测张开到握拳手势，支持轨迹追踪"""
        # 检查是否在冷却期内
        if self.is_in_cooldown(hand_id):
            return None
        
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
        self.trajectory_tracker.initialize_hand_tracking(hand_id)
        
        # 初始化抗抖动相关
        if hand_id not in self.jitter_counters:
            self.jitter_counters[hand_id] = 0
        
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
                # 重置抖动计数器
                self.jitter_counters[hand_id] = 0
                
                if hand_history['fist_frames'] >= self.fist_hold_frames:
                    # 握拳状态持续足够长时间，触发手势
                    confidence = min(100, 70 + hand_history['fist_frames'])
                    
                    # 标记手势已被触发，开始轨迹追踪
                    if not self.trajectory_tracker.is_gesture_triggered(hand_id):
                        self.trajectory_tracker.trigger_gesture(hand_id)
                    
                    # 重置状态但保持轨迹追踪
                    self._reset_detection_only(hand_id)
                    
                    # 开始冷却期
                    self.start_cooldown(hand_id)
                    
                    gesture_result = {
                        'gesture': 'HandClose',
                        'hand_type': hand_type,
                        'confidence': confidence,
                        'details': {
                            'tag': 'start',
                            'description': '张开到握拳',
                            'fist_hold_frames': hand_history['fist_frames'],
                            'required_frames': self.fist_hold_frames,
                            'tracking_active': self.trajectory_tracker.is_gesture_triggered(hand_id)
                        }
                    }
            else:
                # 失去握拳状态，使用抗抖动逻辑
                self.jitter_counters[hand_id] += 1
                
                if self.jitter_counters[hand_id] >= self.jitter_tolerance_frames:
                    # 抖动容忍时间到，重置检测
                    hand_history['closing_detected'] = False
                    hand_history['fist_state'] = False
                    hand_history['fist_frames'] = 0
                    self.jitter_counters[hand_id] = 0
        
        # 处理轨迹追踪（在状态机逻辑之后）
        self.trajectory_tracker.update_tracking(hand_id, palm_center, current_is_fist, hand_type)
        
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
            # 重置轨迹追踪器
            self.trajectory_tracker.reset_all_tracking()
            # 清空抗抖动相关
            self.jitter_counters.clear()
        elif hand_id in self.history:
            self.history[hand_id] = {
                'variance_history': deque(maxlen=self.history_length),
                'distance_history': deque(maxlen=self.history_length),
                'fist_state': False,
                'fist_frames': 0,
                'closing_detected': False
            }
            # 重置该手的轨迹追踪
            self.trajectory_tracker.reset_hand_tracking(hand_id)
            # 清空该手的抗抖动相关
            self.jitter_counters[hand_id] = 0
    
    def _reset_detection_only(self, hand_id: str):
        """只重置检测状态，保持轨迹追踪和平滑状态"""
        if hand_id in self.history:
            self.history[hand_id] = {
                'variance_history': deque(maxlen=self.history_length),
                'distance_history': deque(maxlen=self.history_length),
                'fist_state': False,
                'fist_frames': 0,
                'closing_detected': False
            }
            # 重置抗抖动计数器
            self.jitter_counters[hand_id] = 0
    
    def get_tracking_status(self) -> Dict[str, Dict]:
        """获取所有手的追踪状态"""
        return self.trajectory_tracker.get_tracking_status()
    
    def get_trail_data_for_drawing(self):
        """获取用于绘制的轨迹数据"""
        return self.trajectory_tracker.get_trail_data_for_drawing()
    
    def get_display_message(self, gesture_result: Dict[str, Any]) -> str:
        """获取张开到握拳手势的显示消息"""
        hand_type = gesture_result['hand_type']
        details = gesture_result.get('details', {})
        hold_frames = details.get('fist_hold_frames', 0)
        return f"{hand_type} Hand: Closing to Fist (Held: {hold_frames} frames)"
