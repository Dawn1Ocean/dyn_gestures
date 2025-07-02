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
                'distance_history': deque(maxlen=self.history_length)
            }
        
        # 使用HandUtils中的通用方法计算
        current_variance = HandUtils.calculate_fingertip_variance(landmarks)
        palm_center = HandUtils.calculate_palm_center(landmarks)
        current_distances = HandUtils.calculate_fingertip_distances(landmarks, palm_center)
        
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
            hand_is_open = self._is_hand_open(current_distances, baseline_distances)
            
            # 检查是否满足条件
            if variance_change_percent > self.variance_change_percent and hand_is_open:
                # 清空历史记录避免重复检测
                self.reset(hand_id)
                return {
                    'gesture': 'HandOpen',
                    'hand_type': hand_type,
                    'confidence': min(100, variance_change_percent),
                    'details': {
                        'variance_change': variance_change_percent,
                        'all_fingers_open': hand_is_open
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
    
    def _is_hand_open(self, current_distances: List[float], baseline_distances: List[float]) -> bool:
        """判断手是否张开"""
        if not baseline_distances or len(baseline_distances) != 5:
            return False
        
        exceeds_count = sum(1 for i, dist in enumerate(current_distances) 
                          if dist > baseline_distances[i] * self.distance_multiplier)
        return exceeds_count == 5
    
    def get_display_message(self, gesture_result: Dict[str, Any]) -> str:
        """获取握拳到张开手势的显示消息"""
        hand_type = gesture_result['hand_type']
        details = gesture_result.get('details', {})
        variance_change = details.get('variance_change', 0)
        return f"{hand_type} Hand: Opening (Var: {variance_change:.1f}%)"
