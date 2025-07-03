"""
手势管理器 - 统一管理所有手势检测器
"""

from typing import List, Dict, Any, Optional
from gestures import (
    GestureDetector, 
    StaticGestureDetector,
    HandOpenDetector, 
    PeaceSignDetector,
    ThumbsDetector
)
import config

class GestureManager:
    """手势管理器，负责管理和协调所有手势检测器"""
    
    def __init__(self):
        self.detectors: List[GestureDetector] = []
        self.setup_default_detectors()
    
    def setup_default_detectors(self):
        """设置默认的手势检测器"""
        # 添加动态手势检测器
        self.add_detector(HandOpenDetector())
        
        # 添加静态手势检测器
        peace_config = config.GESTURE_CONFIG['peace_sign']
        self.add_detector(PeaceSignDetector(
            distance_threshold_percent=peace_config['distance_threshold_percent'],
            required_frames=peace_config['required_frames']
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
