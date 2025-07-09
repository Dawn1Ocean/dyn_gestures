"""
大拇指手势检测器 - 静态手势
"""

from typing import List, Dict, Any, Optional

from hand_utils import HandUtils
from ..base import StaticGestureDetector


class ThumbsDetector(StaticGestureDetector):
    """大拇指手势检测器"""
    
    def __init__(self, config: Dict[str, Any], type: str = "ThumbsUp"):
        super().__init__(type, config['required_frames'], config['debounce_frames'])
        self.type = type  # 手势类型
        self.config = config

    def detect(self, landmarks: List[List[int]], hand_id: str, hand_type: str) -> Optional[Dict[str, Any]]:
        """检测竖大拇指手势 - 使用HandUtils的通用方法"""
        # 获取关键点
        thumb_tip, thumb_ip, thumb_mcp = landmarks[4], landmarks[3], landmarks[2]
        
        # 使用HandUtils的通用方法计算手掌中心和基准长度
        palm_center = HandUtils.calculate_palm_center(landmarks)
        palm_base_length = HandUtils.calculate_palm_base_length(landmarks)
        
        # 1. 检查大拇指是否朝上（Y坐标递减且角度合适）
        thumb_upward = thumb_tip[1] < thumb_ip[1] < thumb_mcp[1]
        thumb_downward = thumb_tip[1] > thumb_ip[1] > thumb_mcp[1]
        thumb_angle = HandUtils.calculate_thumb_angle(landmarks)
        thumb_angle_good = thumb_angle < self.config['thumb_angle_threshold']
        
        # 2. 检查大拇指指尖是否离掌心足够远（百分比判断）
        thumb_distance = HandUtils.calculate_distance(thumb_tip, list(palm_center))
        thumb_distance_ratio = thumb_distance / palm_base_length if palm_base_length > 0 else 0
        thumb_extended = thumb_distance_ratio > self.config['thumb_distance_threshold']
        
        # 3. 检查其他手指是否离掌心足够近（百分比判断）
        fingers_data = [
            (8, 6, 5, "食指"),    # 食指尖、PIP、MCP
            (12, 10, 9, "中指"),  # 中指尖、PIP、MCP
            (16, 14, 13, "无名指"), # 无名指尖、PIP、MCP
            (20, 18, 17, "小指")   # 小指尖、PIP、MCP
        ]
        
        fingers_close_to_palm = []
        finger_details = []
        
        for tip_idx, pip_idx, mcp_idx, name in fingers_data:
            # 检查手指尖是否贴近掌心（百分比判断）
            tip_distance = HandUtils.calculate_distance(landmarks[tip_idx], list(palm_center))
            tip_distance_ratio = tip_distance / palm_base_length if palm_base_length > 0 else 0
            is_close_to_palm = tip_distance_ratio < self.config['other_fingers_threshold']

            # 检查手指是否弯曲
            is_bent = HandUtils.is_finger_bent(landmarks, tip_idx, pip_idx)
            
            # 综合判断手指是否握紧
            is_gripped = is_bent and is_close_to_palm
            fingers_close_to_palm.append(is_close_to_palm)
            
            finger_details.append({
                'name': name,
                'is_bent': is_bent,
                'is_close': is_close_to_palm,
                'is_gripped': is_gripped,
                'distance_ratio': tip_distance_ratio
            })
        
        all_fingers_close = all(fingers_close_to_palm)
        
        # 4. 检查大拇指指尖到其他四个手指PIP距离的最小值是否足够远（百分比判断）
        other_finger_pips = [landmarks[6], landmarks[10], landmarks[14], landmarks[18]]  # 食指、中指、无名指、小指的PIP
        thumb_isolated = self._check_thumb_isolation_from_pips(thumb_tip, other_finger_pips, palm_base_length)
        
        # 5. 综合判断
        all_conditions = [thumb_upward if self.type == "ThumbsUp" else thumb_downward, thumb_angle_good, thumb_extended, all_fingers_close, thumb_isolated]

        if all(all_conditions):
            # 计算置信度
            confidence = self._calculate_confidence(thumb_distance_ratio, thumb_angle, finger_details)

            # 6. 检查连续检测帧数
            if self.check_continuous_detection(hand_id, self.type, confidence):
                return {
                    'gesture': self.type,
                    'hand_type': hand_type,
                    'confidence': confidence,
                    'details': {
                        'description': self.type,
                        'thumb_angle': thumb_angle,
                        'frames_detected': self.detection_history[hand_id]['count']
                    }
                }
        
        return None
    
    def _check_thumb_isolation_from_pips(self, thumb_tip: List[int], other_finger_pips: List[List[int]], palm_base_length: float) -> bool:
        """检查大拇指指尖到其他手指PIP距离的最小值是否足够远（百分比判断）"""
        if palm_base_length <= 0:
            return False
        
        min_distance = float('inf')
        for pip_point in other_finger_pips:
            distance = HandUtils.calculate_distance(thumb_tip, pip_point)
            min_distance = min(min_distance, distance)
        
        # 使用百分比判断
        min_distance_ratio = min_distance / palm_base_length
        return min_distance_ratio > self.config['thumb_isolation_threshold']

    def _calculate_confidence(self, thumb_distance_ratio: float, thumb_angle: float, 
                            finger_details: List[Dict]) -> float:
        """计算手势置信度"""
        base_confidence = 80
        
        # 根据大拇指伸出程度加分（使用已计算的比例）
        if thumb_distance_ratio > self.config['thumb_distance_threshold'] * 1.3:
            base_confidence += 15
        elif thumb_distance_ratio > self.config['thumb_distance_threshold'] * 1.1:
            base_confidence += 10
        elif thumb_distance_ratio > self.config['thumb_distance_threshold']:
            base_confidence += 5
        
        # 根据大拇指角度加分
        if thumb_angle < 15:
            base_confidence += 10
        elif thumb_angle < 25:
            base_confidence += 5
        
        # 根据其他手指贴近掌心程度加分
        close_count = sum(1 for detail in finger_details if detail['is_close'])
        base_confidence += close_count * 3
        
        # 根据手指距离比例加分
        avg_finger_ratio = sum(detail['distance_ratio'] for detail in finger_details) / len(finger_details)
        if avg_finger_ratio < self.config['other_fingers_threshold'] * 0.8:
            base_confidence += 8
        elif avg_finger_ratio < self.config['other_fingers_threshold'] * 0.9:
            base_confidence += 5
        
        return min(100, base_confidence)
    
    def get_display_message(self, gesture_result: Dict[str, Any]) -> str:
        """获取大拇指手势的显示消息"""
        hand_type = gesture_result['hand_type']
        return f"{hand_type} Hand: " + self.type
