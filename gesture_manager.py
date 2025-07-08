"""
手势管理器 - 统一管理所有手势检测器
"""

from typing import List, Dict, Any, Optional

import config
from gestures import (
    GestureDetector, 
    StaticGestureDetector,
    HandOpenDetector,
    HandCloseDetector,
    HandSwipeDetector,
    HandFlipDetector,
    TwoFingerSwipeDetector,
    FingerCountOneDetector,
    FingerCountTwoDetector,
    FingerCountThreeDetector,
    ThumbsDetector
)

class GestureManager:
    """手势管理器，负责管理和协调所有手势检测器"""
    
    def __init__(self):
        self.detectors: List[GestureDetector] = []
        self.setup_default_detectors()
    
    def setup_default_detectors(self):
        """设置默认的手势检测器"""
        # 添加动态手势检测器
        hand_open_config = config.GESTURE_CONFIG['hand_open']
        self.add_detector(HandOpenDetector(
            variance_change_percent=hand_open_config['variance_change_percent'],
            distance_multiplier=hand_open_config['distance_multiplier'],
            history_length=hand_open_config['history_length'],
            cooldown_frames=hand_open_config['cooldown_frames']
        ))
        
        hand_close_config = config.GESTURE_CONFIG['hand_close']
        self.add_detector(HandCloseDetector(
            variance_change_percent=hand_close_config['variance_change_percent'],
            distance_multiplier=hand_close_config['distance_multiplier'],
            history_length=hand_close_config['history_length'],
            fist_hold_frames=hand_close_config['fist_hold_frames'],
            cooldown_frames=hand_close_config['cooldown_frames']
        ))
        
        hand_swipe_config = config.GESTURE_CONFIG['hand_swipe']
        self.add_detector(HandSwipeDetector(
            min_distance_percent=hand_swipe_config['min_distance_percent'],
            min_movement_frames=hand_swipe_config['min_movement_frames'],
            history_length=hand_swipe_config['history_length'],
            cooldown_frames=hand_swipe_config['cooldown_frames']
        ))
        
        two_finger_swipe_config = config.GESTURE_CONFIG['two_finger_swipe']
        self.add_detector(TwoFingerSwipeDetector(
            min_distance_percent=two_finger_swipe_config['min_distance_percent'],
            min_movement_frames=two_finger_swipe_config['min_movement_frames'],
            history_length=two_finger_swipe_config['history_length'],
            finger_distance_threshold=two_finger_swipe_config['finger_distance_threshold'],
            cooldown_frames=two_finger_swipe_config['cooldown_frames']
        ))
        
        hand_flip_config = config.GESTURE_CONFIG['hand_flip']
        self.add_detector(HandFlipDetector(
            max_movement_percent=hand_flip_config['max_movement_percent'],
            min_flip_frames=hand_flip_config['min_flip_frames'],
            history_length=hand_flip_config['history_length'],
            cooldown_frames=hand_flip_config['cooldown_frames']
        ))
        
        # 添加静态手势检测器
        finger_one_config = config.GESTURE_CONFIG['finger_count_one']
        self.add_detector(FingerCountOneDetector(
            distance_threshold_percent=finger_one_config['distance_threshold_percent'],
            required_frames=finger_one_config['required_frames']
        ))
        
        finger_two_config = config.GESTURE_CONFIG['finger_count_two']
        self.add_detector(FingerCountTwoDetector(
            distance_threshold_percent=finger_two_config['distance_threshold_percent'],
            required_frames=finger_two_config['required_frames']
        ))
        
        finger_three_config = config.GESTURE_CONFIG['finger_count_three']
        self.add_detector(FingerCountThreeDetector(
            distance_threshold_percent=finger_three_config['distance_threshold_percent'],
            required_frames=finger_three_config['required_frames']
        ))
        
        thumbs_up_config = config.GESTURE_CONFIG['thumbs_up']
        self.add_detector(ThumbsDetector(
            thumb_distance_threshold=thumbs_up_config['thumb_distance_threshold'],
            other_fingers_threshold=thumbs_up_config['other_fingers_threshold'],
            thumb_angle_threshold=thumbs_up_config['thumb_angle_threshold'],
            thumb_isolation_threshold=thumbs_up_config['thumb_isolation_threshold'],
            required_frames=thumbs_up_config['required_frames'],
            type="ThumbsUp"
        ))

        thumbs_down_config = config.GESTURE_CONFIG['thumbs_down']
        self.add_detector(ThumbsDetector(
            thumb_distance_threshold=thumbs_down_config['thumb_distance_threshold'],
            other_fingers_threshold=thumbs_down_config['other_fingers_threshold'],
            thumb_angle_threshold=thumbs_down_config['thumb_angle_threshold'],
            thumb_isolation_threshold=thumbs_down_config['thumb_isolation_threshold'],
            required_frames=thumbs_down_config['required_frames'],
            type="ThumbsDown"
        ))
    
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
        
        for detector in self.detectors:
            try:
                result = detector.detect(landmarks, hand_id, hand_type)
                if result:
                    # 添加显示消息到结果中
                    result['display_message'] = detector.get_display_message(result)
                    results.append(result)
            except Exception as e:
                print(f"检测器 {detector.name} 出错: {e}")
        
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
    
    def on_hand_lost(self, hand_id: str):
        """
        当手部丢失时调用，重置相关的静态手势检测历史
        Args:
            hand_id: 丢失的手部ID
        """
        for detector in self.detectors:
            if isinstance(detector, StaticGestureDetector):
                detector.reset_detection_history(hand_id)
    
    def on_all_hands_lost(self):
        """
        当所有手部都丢失时调用，重置所有静态手势检测历史
        """
        for detector in self.detectors:
            if isinstance(detector, StaticGestureDetector):
                detector.reset_detection_history()
