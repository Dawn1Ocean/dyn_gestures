"""
数字二手势检测器 - 静态手势
"""

from typing import List, Dict, Any, Optional

from hand_utils import HandUtils
from ..base import StaticGestureDetector


class FingerCountTwoDetector(StaticGestureDetector):
    """数字二手势检测器（食指和中指伸出）"""
    
    def __init__(self, distance_threshold_percent: float = 0.6, required_frames: int = 30, debounce_frames: int = 5):
        super().__init__("FingerCountTwo", required_frames, debounce_frames)
        self.distance_threshold_percent = distance_threshold_percent
    
    def detect(self, landmarks: List[List[int]], hand_id: str, hand_type: str) -> Optional[Dict[str, Any]]:
        """检测数字二手势 - 食指和中指伸出且朝上"""
        
        # 1. 检查食指和中指是否伸直且朝上 - 使用HandUtils的通用方法
        index_extended = HandUtils.is_finger_extended(
            landmarks, 8, 6, 5, self.distance_threshold_percent
        )
        middle_extended = HandUtils.is_finger_extended(
            landmarks, 12, 10, 9, self.distance_threshold_percent
        )
        
        # 2. 检查无名指和小指是否弯曲 - 使用HandUtils的通用方法
        ring_bent = HandUtils.is_finger_bent(landmarks, 16, 14)
        pinky_bent = HandUtils.is_finger_bent(landmarks, 20, 18)
        
        # 3. 检查食指和中指之间是否张开形成V字 - 使用HandUtils的通用方法
        fingers_spread = HandUtils.check_fingers_spread(landmarks, 8, 12, 0.3)
        
        # 4. 检查拇指是否靠近掌心（数字二手势时拇指通常收起）
        thumb_close_to_palm = HandUtils.is_thumb_close_to_palm(landmarks, 0.5)
        
        # 5. 基础判断
        if index_extended and middle_extended and ring_bent and pinky_bent and fingers_spread and thumb_close_to_palm:
            # 计算置信度
            confidence = self._calculate_confidence(landmarks)
            
            # 6. 检查连续检测帧数
            if self.check_continuous_detection(hand_id, "FingerCountTwo", confidence):
                return {
                    'gesture': 'FingerCountTwo',
                    'hand_type': hand_type,
                    'confidence': confidence,
                    'details': {
                        'description': '数字二手势',
                        'index_extended': index_extended,
                        'middle_extended': middle_extended,
                        'other_fingers_bent': ring_bent and pinky_bent,
                        'fingers_spread': fingers_spread,
                        'thumb_close_to_palm': thumb_close_to_palm,
                        'frames_detected': self.detection_history[hand_id]['count']
                    }
                }
        else:
            # 如果不满足基础条件，不要直接重置，让手势管理器处理结束逻辑
            pass
        
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
        
        # 根据食指和中指的高度加分
        index_height = wrist[1] - index_tip[1]
        middle_height = wrist[1] - middle_tip[1]
        
        if index_height > palm_base_length * 0.5 and middle_height > palm_base_length * 0.5:
            base_confidence += 10
        
        # 根据其他手指的弯曲程度加分
        ring_bend = max(0, ring_tip[1] - wrist[1])
        pinky_bend = max(0, pinky_tip[1] - wrist[1])
        
        if ring_bend > 0 and pinky_bend > 0:
            base_confidence += 5
        
        # 根据拇指是否收起加分
        if HandUtils.is_thumb_close_to_palm(landmarks, 0.5):
            base_confidence += 5
        
        return min(100, base_confidence)
    
    def reset(self, hand_id: Optional[str] = None):
        """重置静态手势检测状态"""
        self.reset_detection_history(hand_id)
    
    def get_display_message(self, gesture_result: Dict[str, Any]) -> str:
        """获取数字二手势的显示消息"""
        hand_type = gesture_result['hand_type']
        return f"{hand_type} Hand: Number Two"