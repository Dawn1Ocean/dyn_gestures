"""
数字一手势检测器 - 静态手势
"""

from typing import List, Dict, Any, Optional
from ..base import StaticGestureDetector
from hand_utils import HandUtils


class FingerCountOneDetector(StaticGestureDetector):
    """数字一手势检测器（仅食指伸出且朝上）"""
    
    def __init__(self, distance_threshold_percent: float = 0.6, required_frames: int = 30):
        super().__init__("FingerCountOne", required_frames)
        self.distance_threshold_percent = distance_threshold_percent
    
    def detect(self, landmarks: List[List[int]], hand_id: str, hand_type: str) -> Optional[Dict[str, Any]]:
        """检测数字一手势 - 仅食指伸出且朝上"""
        
        # 1. 检查食指是否伸直且朝上 - 使用HandUtils的通用方法
        index_extended = HandUtils.is_finger_extended(
            landmarks, 8, 6, 5, self.distance_threshold_percent
        )
        
        # 2. 检查中指、无名指和小指是否弯曲 - 使用HandUtils的通用方法
        middle_bent = HandUtils.is_finger_bent(landmarks, 12, 10)
        ring_bent = HandUtils.is_finger_bent(landmarks, 16, 14)
        pinky_bent = HandUtils.is_finger_bent(landmarks, 20, 18)
        
        # 3. 检查拇指是否靠近掌心（数字一手势时拇指通常收起）
        thumb_close_to_palm = HandUtils.is_thumb_close_to_palm(landmarks, 0.5)
        
        # 4. 基础判断
        if index_extended and middle_bent and ring_bent and pinky_bent and thumb_close_to_palm:
            # 计算置信度
            confidence = self._calculate_confidence(landmarks)
            
            # 5. 检查连续检测帧数
            if self.check_continuous_detection(hand_id, "FingerCountOne", confidence):
                return {
                    'gesture': 'FingerCountOne',
                    'hand_type': hand_type,
                    'confidence': confidence,
                    'details': {
                        'description': '数字一手势',
                        'index_extended': index_extended,
                        'other_fingers_bent': middle_bent and ring_bent and pinky_bent,
                        'thumb_close_to_palm': thumb_close_to_palm,
                        'frames_detected': self.detection_history[hand_id]['count']
                    }
                }
        else:
            # 如果不满足基础条件，重置该手的检测历史
            self.reset_detection_history(hand_id)
        
        return None
    
    def _calculate_confidence(self, landmarks: List[List[int]]) -> float:
        """计算手势置信度"""
        base_confidence = 85
        
        # 获取关键点
        wrist = landmarks[0]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        
        # 计算手掌基准长度
        palm_base_length = HandUtils.calculate_palm_base_length(landmarks)
        
        # 根据食指的高度加分
        index_height = wrist[1] - index_tip[1]
        
        if index_height > palm_base_length * 0.6:
            base_confidence += 10
        
        # 根据其他手指的弯曲程度加分
        middle_bend = max(0, middle_tip[1] - wrist[1])
        ring_bend = max(0, ring_tip[1] - wrist[1])
        pinky_bend = max(0, pinky_tip[1] - wrist[1])
        
        if middle_bend > 0 and ring_bend > 0 and pinky_bend > 0:
            base_confidence += 10
        
        # 根据拇指是否收起加分
        if HandUtils.is_thumb_close_to_palm(landmarks, 0.5):
            base_confidence += 5
        
        return min(100, base_confidence)
    
    def reset(self, hand_id: Optional[str] = None):
        """重置静态手势检测状态"""
        self.reset_detection_history(hand_id)
    
    def get_display_message(self, gesture_result: Dict[str, Any]) -> str:
        """获取数字一手势的显示消息"""
        hand_type = gesture_result['hand_type']
        return f"{hand_type} Hand: Number One"
