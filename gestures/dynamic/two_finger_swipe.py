"""
双指滑动手势检测器 - 动态手势
食指和中指并拢朝上，其他手指弯曲，手左右滑动
"""

from collections import deque
from typing import List, Dict, Any, Optional

from hand_utils import HandUtils
from ..base import DynamicGestureDetector


class TwoFingerSwipeDetector(DynamicGestureDetector):
    """双指滑动手势检测器（食指和中指并拢朝上，其他手指弯曲）"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("TwoFingerSwipe", config['history_length'], config['cooldown_frames'])
        self.min_distance_percent = config['min_distance_percent']  # 最小移动距离百分比（相对于手掌基准长度）
        self.min_movement_frames = config['min_movement_frames']  # 最小连续移动帧数
        self.finger_distance_threshold = config['finger_distance_threshold']  # 食指中指并拢阈值

    def detect(self, landmarks: List[List[int]], hand_id: str, hand_type: str) -> Optional[Dict[str, Any]]:
        """检测双指滑动手势"""
        # 检查是否在冷却期内
        if self.is_in_cooldown(hand_id):
            return None
        
        # 初始化历史记录
        if hand_id not in self.history:
            self.history[hand_id] = {
                'palm_positions': deque(maxlen=self.history_length),
                'two_finger_states': deque(maxlen=self.history_length),
                'movement_direction': None,  # 'left' 或 'right'
                'movement_frames': 0,
                'total_distance': 0.0
            }
        
        hand_history = self.history[hand_id]
        
        # 计算当前手掌中心和基准长度
        palm_center = HandUtils.calculate_palm_center(landmarks)
        palm_base_length = HandUtils.calculate_palm_base_length(landmarks)
        
        # 检查是否为双指姿态
        is_two_finger_pose = HandUtils.check_two_finger_pose(landmarks, palm_base_length, self.finger_distance_threshold)

        # 添加到历史记录
        hand_history['palm_positions'].append(palm_center)
        hand_history['two_finger_states'].append(is_two_finger_pose)
        
        # 需要足够的历史数据且手必须为双指姿态
        if len(hand_history['palm_positions']) >= self.min_movement_frames and is_two_finger_pose:
            # 检查最近几帧中大部分是双指姿态（允许少量帧丢失）
            recent_pose_states = list(hand_history['two_finger_states'])[-self.min_movement_frames:]
            pose_success_rate = sum(recent_pose_states) / len(recent_pose_states)
            if pose_success_rate >= 0.7:  # 70%的帧符合双指姿态即可
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
        """分析滑动运动模式 - 改进的双向检测逻辑"""
        positions = list(hand_history['palm_positions'])
        
        if len(positions) < self.min_movement_frames:
            return None
        
        # 计算整体移动方向和距离
        start_pos = positions[0]
        end_pos = positions[-1]
        total_x_displacement = end_pos[0] - start_pos[0]
        total_y_displacement = end_pos[1] - start_pos[1]
        
        # 确保主要是水平移动（而非垂直移动）
        if abs(total_y_displacement) > abs(total_x_displacement):
            return None  # 主要是垂直移动，不是左右滑动
        
        # 计算累计水平移动距离和方向一致性
        total_horizontal_movement = 0.0
        movement_direction = None
        consistent_direction_frames = 0
        direction_changes = 0
        
        # 分析每一帧的移动
        for i in range(1, len(positions)):
            prev_pos = positions[i-1]
            curr_pos = positions[i]
            
            horizontal_movement = curr_pos[0] - prev_pos[0]
            total_horizontal_movement += abs(horizontal_movement)
            
            # 判断移动方向（忽略很小的移动）
            if abs(horizontal_movement) > palm_base_length * 0.03:  # 降低阈值从0.05到0.03
                current_direction = 'right' if horizontal_movement > 0 else 'left'
                
                if movement_direction is None:
                    movement_direction = current_direction
                    consistent_direction_frames = 1
                elif movement_direction == current_direction:
                    consistent_direction_frames += 1
                else:
                    direction_changes += 1
        
        # 如果没有确定的方向，用整体位移来判断
        if movement_direction is None and abs(total_x_displacement) > palm_base_length * 0.1:
            movement_direction = 'right' if total_x_displacement > 0 else 'left'
            consistent_direction_frames = self.min_movement_frames // 2
        
        # 计算移动距离（使用更好的距离计算）
        cumulative_distance = max(total_horizontal_movement, abs(total_x_displacement))
        min_distance = palm_base_length * self.min_distance_percent
        distance_sufficient = cumulative_distance >= min_distance
        
        # 放宽方向一致性要求
        direction_consistency_threshold = max(3, self.min_movement_frames * 0.4)  # 降低到40%
        direction_consistent = (consistent_direction_frames >= direction_consistency_threshold)
        
        # 检查方向变化不能太频繁
        max_allowed_direction_changes = self.min_movement_frames // 3
        direction_stable = direction_changes <= max_allowed_direction_changes
        
        if distance_sufficient and direction_consistent and direction_stable and movement_direction:
            # 计算移动速度（像素/帧）
            movement_speed = cumulative_distance / len(positions)
            
            # 计算置信度
            confidence = self._calculate_confidence(
                cumulative_distance, min_distance, 
                consistent_direction_frames, movement_speed,
                direction_changes, len(positions)
            )

            direction_text = "left" if movement_direction == 'left' else "right"

            return {
                'gesture': 'TwoFingerSwipe',
                'hand_type': hand_type,
                'confidence': confidence,
                'details': {
                    'description': f'双指向{direction_text}滑动',
                    'direction': movement_direction,
                    'total_distance': round(cumulative_distance, 1),
                    'distance_percent': round((cumulative_distance / palm_base_length) * 100, 1),
                    'movement_frames': consistent_direction_frames,
                    'movement_speed': round(movement_speed, 1),
                    'direction_changes': direction_changes,
                    'x_displacement': round(total_x_displacement, 1)
                }
            }
        
        return None
    
    def _calculate_confidence(self, total_distance: float, min_distance: float, 
                            consistent_frames: int, movement_speed: float,
                            direction_changes: int = 0, total_frames: int = 1) -> float:
        """计算双指滑动手势的置信度 - 改进版本"""
        base_confidence = 70  # 降低基础置信度，因为放宽了检测条件
        
        # 根据移动距离加分
        distance_ratio = total_distance / min_distance
        if distance_ratio > 2.5:
            base_confidence += 25
        elif distance_ratio > 2.0:
            base_confidence += 20
        elif distance_ratio > 1.5:
            base_confidence += 15
        elif distance_ratio > 1.0:
            base_confidence += 10
        
        # 根据方向一致性加分
        consistency_ratio = consistent_frames / total_frames
        if consistency_ratio > 0.8:
            base_confidence += 15
        elif consistency_ratio > 0.6:
            base_confidence += 10
        elif consistency_ratio > 0.4:
            base_confidence += 5
        
        # 根据方向变化频率减分
        change_ratio = direction_changes / total_frames
        if change_ratio > 0.3:
            base_confidence -= 10
        elif change_ratio > 0.2:
            base_confidence -= 5
        
        # 根据移动速度加分（适中的速度更好）
        if 3 <= movement_speed <= 20:  # 放宽速度范围
            base_confidence += 5
        elif movement_speed > 25:  # 太快减分
            base_confidence -= 5
        
        return max(50, min(100, base_confidence))  # 确保置信度在50-100之间
    
    def reset(self, hand_id: Optional[str] = None):
        """重置检测器状态"""
        if hand_id is None:
            self.history.clear()
        elif hand_id in self.history:
            self.history[hand_id] = {
                'palm_positions': deque(maxlen=self.history_length),
                'two_finger_states': deque(maxlen=self.history_length),
                'movement_direction': None,
                'movement_frames': 0,
                'total_distance': 0.0
            }
    
    def get_display_message(self, gesture_result: Dict[str, Any]) -> str:
        """获取双指滑动手势的显示消息"""
        hand_type = gesture_result['hand_type']
        details = gesture_result.get('details', {})
        direction = details.get('direction', 'unknown')
        distance_percent = details.get('distance_percent', 0)
        direction_text = "Left" if direction == 'left' else "Right"
        return f"{hand_type} Hand: Two-Finger Swipe {direction_text} ({distance_percent:.1f}%)"
