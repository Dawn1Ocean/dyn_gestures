"""
手左右挥动手势检测器 - 动态手势
"""

from collections import deque
from typing import List, Dict, Any, Optional

from hand_utils import HandUtils
from ..base import DynamicGestureDetector


class HandSwipeDetector(DynamicGestureDetector):
    """手左右挥动手势检测器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("HandSwipe", config['history_length'], config['cooldown_frames'])
        self.min_distance_percent = config['min_distance_percent']  # 最小移动距离百分比（相对于手掌基准长度）
        self.min_movement_frames = config['min_movement_frames']  # 最小连续移动帧数

    def detect(self, landmarks: List[List[int]], hand_id: str, hand_type: str) -> Optional[Dict[str, Any]]:
        """检测手左右挥动手势"""
        # 检查是否在冷却期内
        if self.is_in_cooldown(hand_id):
            return None
        
        # 初始化历史记录
        if hand_id not in self.history:
            self.history[hand_id] = {
                'palm_positions': deque(maxlen=self.history_length),
                'hand_open_states': deque(maxlen=self.history_length),
                'movement_direction': None,  # 'left' 或 'right'
                'movement_frames': 0,
                'total_distance': 0.0
            }
        
        hand_history = self.history[hand_id]
        
        # 计算当前手掌中心和基准长度
        palm_center = HandUtils.calculate_palm_center(landmarks)
        palm_base_length = HandUtils.calculate_palm_base_length(landmarks)
        
        # 检查手是否张开
        is_hand_open = HandUtils.is_hand_open(landmarks)
        
        # 添加到历史记录
        hand_history['palm_positions'].append(palm_center)
        hand_history['hand_open_states'].append(is_hand_open)
        
        # 需要足够的历史数据且手必须张开
        if len(hand_history['palm_positions']) >= self.min_movement_frames and is_hand_open:
            # 检查最近几帧手是否都是张开的
            recent_open_states = list(hand_history['hand_open_states'])[-self.min_movement_frames:]
            if all(recent_open_states):
                # 分析移动模式
                result = self._analyze_swipe_movement(hand_history, palm_base_length, hand_type)
                if result:
                    # 开始冷却期
                    self.start_cooldown(hand_id)
                    # 重置历史以避免重复检测
                    self.reset(hand_id)
                    return result
        
        return None
    
    def _analyze_swipe_movement(self, hand_history: dict, palm_base_length: float, 
                              hand_type: str) -> Optional[Dict[str, Any]]:
        """分析挥动运动模式"""
        positions = list(hand_history['palm_positions'])
        
        if len(positions) < self.min_movement_frames:
            return None
        
        # 计算总的水平移动距离
        total_horizontal_movement = 0.0
        movement_direction = None
        consistent_direction_frames = 0
        
        for i in range(1, len(positions)):
            prev_pos = positions[i-1]
            curr_pos = positions[i]
            
            horizontal_movement = curr_pos[0] - prev_pos[0]
            total_horizontal_movement += abs(horizontal_movement)
            
            # 判断移动方向
            if abs(horizontal_movement) > palm_base_length * 0.05:  # 忽略小幅度移动
                current_direction = 'right' if horizontal_movement > 0 else 'left'
                
                if movement_direction is None:
                    movement_direction = current_direction
                    consistent_direction_frames = 1
                elif movement_direction == current_direction:
                    consistent_direction_frames += 1
        
        # 检查移动距离是否足够
        min_distance = palm_base_length * self.min_distance_percent
        distance_sufficient = total_horizontal_movement >= min_distance
        
        # 检查方向是否一致
        direction_consistent = (consistent_direction_frames >= self.min_movement_frames * 0.6)
        
        if distance_sufficient and direction_consistent and movement_direction:
            # 计算移动速度（像素/帧）
            movement_speed = total_horizontal_movement / len(positions)
            
            # 计算置信度
            confidence = self._calculate_confidence(
                total_horizontal_movement, min_distance, 
                consistent_direction_frames, movement_speed
            )
            
            return {
                'gesture': 'HandSwipe',
                'hand_type': hand_type,
                'confidence': confidence,
                'details': {
                    'description': f'手向{movement_direction}挥动' if movement_direction == 'left' else f'手向{movement_direction}挥动',
                    'direction': movement_direction,
                    'total_distance': round(total_horizontal_movement, 1),
                    'distance_percent': round((total_horizontal_movement / palm_base_length) * 100, 1),
                    'movement_frames': consistent_direction_frames,
                    'movement_speed': round(movement_speed, 1)
                }
            }
        
        return None
    
    def _calculate_confidence(self, total_distance: float, min_distance: float, 
                            consistent_frames: int, movement_speed: float) -> float:
        """计算挥动手势的置信度"""
        base_confidence = 70
        
        # 根据移动距离加分
        distance_ratio = total_distance / min_distance
        if distance_ratio > 2.0:
            base_confidence += 20
        elif distance_ratio > 1.5:
            base_confidence += 15
        elif distance_ratio > 1.0:
            base_confidence += 10
        
        # 根据方向一致性加分
        if consistent_frames >= self.min_movement_frames:
            base_confidence += 10
        
        # 根据移动速度加分（适中的速度更好）
        if 5 <= movement_speed <= 15:
            base_confidence += 5
        
        return min(100, base_confidence)
    
    def reset(self, hand_id: Optional[str] = None):
        """重置检测器状态"""
        if hand_id is None:
            self.history.clear()
        elif hand_id in self.history:
            self.history[hand_id] = {
                'palm_positions': deque(maxlen=self.history_length),
                'hand_open_states': deque(maxlen=self.history_length),
                'movement_direction': None,
                'movement_frames': 0,
                'total_distance': 0.0
            }
    
    def get_display_message(self, gesture_result: Dict[str, Any]) -> str:
        """获取手左右挥动手势的显示消息"""
        hand_type = gesture_result['hand_type']
        details = gesture_result.get('details', {})
        direction = details.get('direction', 'unknown')
        distance_percent = details.get('distance_percent', 0)
        direction_text = "left" if direction == 'left' else "right"
        return f"{hand_type} Hand: Swipe {direction_text} ({distance_percent:.1f}%)"
