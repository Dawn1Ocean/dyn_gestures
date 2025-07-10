"""
手势管理器 - 统一管理所有手势检测器
"""

from typing import List, Dict, Any, Optional

import config
from gestures.base import GestureDetector, StaticGestureDetector, TrackerGestureDetector
from gestures.dynamic.hand_open import HandOpenDetector
from gestures.dynamic.hand_close import HandCloseDetector
from gestures.dynamic.hand_swipe import HandSwipeDetector
from gestures.dynamic.hand_flip import HandFlipDetector
from gestures.dynamic.two_finger_swipe import TwoFingerSwipeDetector
from gestures.static.finger_count_one import FingerCountOneDetector
from gestures.static.finger_count_two import FingerCountTwoDetector
from gestures.static.finger_count_three import FingerCountThreeDetector
from gestures.static.thumbs import ThumbsDetector

class GestureManager:
    """手势管理器，负责管理和协调所有手势检测器"""
    
    def __init__(self):
        self.detectors: List[GestureDetector] = []
        self.setup_default_detectors()
    
    def setup_default_detectors(self):
        """设置默认的手势检测器"""
        # 添加动态手势检测器
        self.add_detector(HandOpenDetector(config = config.GESTURE_CONFIG['hand_open']))
        self.add_detector(HandCloseDetector(config = config.GESTURE_CONFIG['hand_close']))
        self.add_detector(HandSwipeDetector(config = config.GESTURE_CONFIG['hand_swipe']))
        self.add_detector(TwoFingerSwipeDetector(config = config.GESTURE_CONFIG['two_finger_swipe']))
        self.add_detector(HandFlipDetector(config = config.GESTURE_CONFIG['hand_flip']))
        
        # 添加静态手势检测器
        self.add_detector(FingerCountOneDetector(config = config.GESTURE_CONFIG['finger_count_one']))
        self.add_detector(FingerCountTwoDetector(config = config.GESTURE_CONFIG['finger_count_two']))
        self.add_detector(FingerCountThreeDetector(config = config.GESTURE_CONFIG['finger_count_three']))
        self.add_detector(ThumbsDetector(config = config.GESTURE_CONFIG['thumbs_up'], type="ThumbsUp"))
        self.add_detector(ThumbsDetector(config = config.GESTURE_CONFIG['thumbs_down'], type="ThumbsDown"))
    
    def add_detector(self, detector: GestureDetector):
        """添加新的手势检测器"""
        self.detectors.append(detector)
    
    def remove_detector(self, detector_name: str):
        """移除手势检测器"""
        self.detectors = [d for d in self.detectors if d.name != detector_name]
    
    def detect_gestures(self, landmarks: List[List[int]], hand_id: str, hand_type: str) -> List[Dict[str, Any]]:
        """
        使用所有检测器检测手势
        Returns:
            检测到的手势列表，每个手势包含显示消息
        """
        results = []
        
        # 先检测静态手势
        for detector in self.detectors:
            if isinstance(detector, StaticGestureDetector):
                try:
                    # 检测当前手势
                    result = detector.detect(landmarks, hand_id, hand_type)
                    
                    # 如果检测到手势且满足输出条件，添加到结果并直接发送
                    if result and detector.should_output_gesture(hand_id):
                        # 添加显示消息
                        result['display_message'] = detector.get_display_message(result)
                        results.append(result)
                        
                        # 直接发送手势检测结果
                        from gestures.output import output_gesture_detection
                        output_gesture_detection(result, hand_id)

                except Exception as e:
                    print(f"静态手势检测器 {detector.name} 出错: {e}")
            
            # 然后检测动态手势
            else:
                try:
                    result = detector.detect(landmarks, hand_id, hand_type)
                    if result:
                        # 添加显示消息到结果中
                        result['display_message'] = detector.get_display_message(result)
                        results.append(result)
                        
                        # 直接发送手势检测结果
                        from gestures.output import output_gesture_detection
                        output_gesture_detection(result, hand_id)
                except Exception as e:
                    print(f"动态手势检测器 {detector.name} 出错: {e}")
        
        return results
    
    def reset_all_detectors(self, hand_id: Optional[str] = None):
        """重置所有检测器"""
        for detector in self.detectors:
            detector.reset(hand_id)
    
    def get_detector_by_name(self, name: str) -> Optional[GestureDetector]:
        """根据名称获取检测器"""
        for detector in self.detectors:
            if detector.name == name:
                return detector
        return None
    
    def get_all_tracker_detectors(self) -> List[TrackerGestureDetector]:
        """获取所有轨迹检测器"""
        return [d for d in self.detectors if isinstance(d, TrackerGestureDetector)]

    def on_hand_lost(self, hand_id: str):
        """
        当手部丢失时调用，重置相关的检测历史
        Args:
            hand_id: 丢失的手部ID
        """
        for detector in self.detectors:
            if isinstance(detector, StaticGestureDetector):
                # 重置检测历史
                detector.reset_detection_history(hand_id)
    
    def on_all_hands_lost(self):
        """
        当所有手部都丢失时调用，重置所有检测历史
        """
        for detector in self.detectors:
            if isinstance(detector, StaticGestureDetector):
                # 重置检测历史
                detector.reset_detection_history()
