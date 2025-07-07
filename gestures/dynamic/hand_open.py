"""
握拳到张开手势检测器 - 动态手势
"""

import numpy as np
from collections import deque
from typing import List, Dict, Any, Optional
from ..base import DynamicGestureDetector
from hand_utils import HandUtils


class HandOpenDetector(DynamicGestureDetector):
    """握拳到张开手势检测器"""
    
    def __init__(self, variance_change_percent: float = 50, distance_multiplier: float = 1.5, history_length: int = 10):
        super().__init__("HandOpen", history_length)
        self.variance_change_percent = variance_change_percent
        self.distance_multiplier = distance_multiplier
    
    def detect(self, landmarks: List[List[int]], hand_id: str, hand_type: str) -> Optional[Dict[str, Any]]:
        """检测握拳到张开手势"""
        # 初始化历史记录
        if hand_id not in self.history:
            self.history[hand_id] = {
                'variance_history': deque(maxlen=self.history_length),
                'distance_history': deque(maxlen=self.history_length),
                'initial_fist_detected': False  # 添加初始握拳状态标记
            }
        
        # 使用HandUtils中的通用方法计算
        current_variance = HandUtils.calculate_fingertip_variance(landmarks)
        palm_center = HandUtils.calculate_palm_center(landmarks)
        current_distances = HandUtils.calculate_fingertip_distances(landmarks, palm_center)
        
        # 检查初始握拳状态
        is_currently_closed = HandUtils.is_hand_closed(landmarks, current_distances)
        
        # 如果还没有检测到初始握拳状态，先检测握拳
        if not self.history[hand_id]['initial_fist_detected']:
            if is_currently_closed:
                self.history[hand_id]['initial_fist_detected'] = True
            # 没有检测到初始握拳，不进行张开检测
            return None
        
        # 添加到历史记录
        self.history[hand_id]['variance_history'].append(current_variance)
        self.history[hand_id]['distance_history'].append(current_distances)
        
        # 检查是否有足够的历史数据
        if len(self.history[hand_id]['variance_history']) >= self.history_length:
            # 计算基线
            baseline_variance = np.mean(list(self.history[hand_id]['variance_history'])[:-1])
            
            baseline_distances = []
            distance_history = list(self.history[hand_id]['distance_history'])[:-1]
            if distance_history:
                for finger_idx in range(5):
                    finger_distances = [frame_distances[finger_idx] for frame_distances in distance_history]
                    baseline_distances.append(np.mean(finger_distances))
            
            # 计算变化
            variance_change_percent = ((current_variance - baseline_variance) / (baseline_variance + 1e-6)) * 100
            hand_is_open = HandUtils.is_hand_open(landmarks)
            
            # 检查是否满足条件：从握拳状态变为张开状态
            if variance_change_percent > self.variance_change_percent and hand_is_open and not is_currently_closed:
                # 清空历史记录避免重复检测
                self.reset(hand_id)
                return {
                    'gesture': 'HandOpen',
                    'hand_type': hand_type,
                    'confidence': min(100, variance_change_percent),
                    'details': {
                        'variance_change': variance_change_percent,
                        'all_fingers_open': hand_is_open,
                        'initial_fist_was_detected': True
                    }
                }
        
        return None
    
    def reset(self, hand_id: Optional[str] = None):
        """重置检测器状态"""
        if hand_id is None:
            self.history.clear()
        elif hand_id in self.history:
            self.history[hand_id]['variance_history'].clear()
            self.history[hand_id]['distance_history'].clear()
            self.history[hand_id]['initial_fist_detected'] = False
    
    def get_display_message(self, gesture_result: Dict[str, Any]) -> str:
        """获取握拳到张开手势的显示消息"""
        hand_type = gesture_result['hand_type']
        details = gesture_result.get('details', {})
        variance_change = details.get('variance_change', 0)
        return f"{hand_type} Hand: Opening (Var: {variance_change:.1f}%)"
