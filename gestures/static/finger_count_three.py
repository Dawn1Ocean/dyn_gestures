"""
数字三手势检测器 - 静态手势
"""

from typing import List, Dict, Any, Optional

from hand_utils import HandUtils
from ..base import StaticGestureDetector


class FingerCountThreeDetector(StaticGestureDetector):
    """数字三手势检测器（食指、中指、无名指伸出且朝上）"""
    
    def __init__(self, distance_threshold_percent: float = 0.6, required_frames: int = 30, debounce_frames: int = 5):
        super().__init__("FingerCountThree", required_frames, debounce_frames)
        self.distance_threshold_percent = distance_threshold_percent
    
    def detect(self, landmarks: List[List[int]], hand_id: str, hand_type: str) -> Optional[Dict[str, Any]]:
        """检测数字三手势 - 食指、中指、无名指伸出且朝上"""
        
        # 1. 检查食指、中指、无名指是否伸直且朝上 - 使用HandUtils的通用方法
        index_extended = HandUtils.is_finger_extended(
            landmarks, 8, 6, 5, self.distance_threshold_percent
        )
        middle_extended = HandUtils.is_finger_extended(
            landmarks, 12, 10, 9, self.distance_threshold_percent
        )
        ring_extended = HandUtils.is_finger_extended(
            landmarks, 16, 14, 13, self.distance_threshold_percent
        )
        
        # 2. 检查小指是否弯曲 - 使用HandUtils的通用方法
        pinky_bent = HandUtils.is_finger_bent(landmarks, 20, 18)
        
        # 3. 检查拇指是否靠近掌心（数字三手势时拇指通常收起）
        thumb_close_to_palm = HandUtils.is_thumb_close_to_palm(landmarks, 0.5)
        
        # 4. 基础判断
        if index_extended and middle_extended and ring_extended and pinky_bent and thumb_close_to_palm:
            # 计算置信度
            confidence = self._calculate_confidence(landmarks)
            
            # 5. 检查连续检测帧数
            if self.check_continuous_detection(hand_id, "FingerCountThree", confidence):
                return {
                    'gesture': 'FingerCountThree',
                    'hand_type': hand_type,
                    'confidence': confidence,
                    'details': {
                        'description': '数字三手势',
                        'index_extended': index_extended,
                        'middle_extended': middle_extended,
                        'ring_extended': ring_extended,
                        'pinky_bent': pinky_bent,
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
        
        # 根据三个手指的高度加分
        index_height = wrist[1] - index_tip[1]
        middle_height = wrist[1] - middle_tip[1]
        ring_height = wrist[1] - ring_tip[1]
        
        extended_fingers = 0
        if index_height > palm_base_length * 0.5:
            extended_fingers += 1
        if middle_height > palm_base_length * 0.5:
            extended_fingers += 1
        if ring_height > palm_base_length * 0.5:
            extended_fingers += 1
        
        base_confidence += extended_fingers * 3
        
        # 根据小指的弯曲程度加分
        pinky_bend = max(0, pinky_tip[1] - wrist[1])
        
        if pinky_bend > 0:
            base_confidence += 5
        
        # 根据拇指是否收起加分
        if HandUtils.is_thumb_close_to_palm(landmarks, 0.5):
            base_confidence += 5
        
        # 检查三个手指的排列是否整齐
        finger_tips_y = [index_tip[1], middle_tip[1], ring_tip[1]]
        y_variance = max(finger_tips_y) - min(finger_tips_y)
        if y_variance < palm_base_length * 0.2:  # 如果三个手指高度相近
            base_confidence += 5
        
        return min(100, base_confidence)
    
    def reset(self, hand_id: Optional[str] = None):
        """重置静态手势检测状态"""
        self.reset_detection_history(hand_id)
    
    def get_display_message(self, gesture_result: Dict[str, Any]) -> str:
        """获取数字三手势的显示消息"""
        hand_type = gesture_result['hand_type']
        return f"{hand_type} Hand: Number Three"
