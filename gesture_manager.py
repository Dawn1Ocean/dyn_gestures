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
            required_frames=finger_one_config['required_frames'],
            debounce_frames=finger_one_config['debounce_frames']
        ))
        
        finger_two_config = config.GESTURE_CONFIG['finger_count_two']
        self.add_detector(FingerCountTwoDetector(
            distance_threshold_percent=finger_two_config['distance_threshold_percent'],
            required_frames=finger_two_config['required_frames'],
            debounce_frames=finger_two_config['debounce_frames']
        ))
        
        finger_three_config = config.GESTURE_CONFIG['finger_count_three']
        self.add_detector(FingerCountThreeDetector(
            distance_threshold_percent=finger_three_config['distance_threshold_percent'],
            required_frames=finger_three_config['required_frames'],
            debounce_frames=finger_three_config['debounce_frames']
        ))
        
        thumbs_up_config = config.GESTURE_CONFIG['thumbs_up']
        self.add_detector(ThumbsDetector(
            thumb_distance_threshold=thumbs_up_config['thumb_distance_threshold'],
            other_fingers_threshold=thumbs_up_config['other_fingers_threshold'],
            thumb_angle_threshold=thumbs_up_config['thumb_angle_threshold'],
            thumb_isolation_threshold=thumbs_up_config['thumb_isolation_threshold'],
            required_frames=thumbs_up_config['required_frames'],
            debounce_frames=thumbs_up_config['debounce_frames'],
            type="ThumbsUp"
        ))

        thumbs_down_config = config.GESTURE_CONFIG['thumbs_down']
        self.add_detector(ThumbsDetector(
            thumb_distance_threshold=thumbs_down_config['thumb_distance_threshold'],
            other_fingers_threshold=thumbs_down_config['other_fingers_threshold'],
            thumb_angle_threshold=thumbs_down_config['thumb_angle_threshold'],
            thumb_isolation_threshold=thumbs_down_config['thumb_isolation_threshold'],
            required_frames=thumbs_down_config['required_frames'],
            debounce_frames=thumbs_down_config['debounce_frames'],
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
        
        # 首先检查静态手势是否结束
        static_gesture_ended = False
        for detector in self.detectors:
            if isinstance(detector, StaticGestureDetector):
                try:
                    # 先检测当前手势
                    current_result = detector.detect(landmarks, hand_id, hand_type)
                    current_gesture = current_result['gesture'] if current_result else None
                    
                    # 检查是否有手势结束
                    end_result = detector.check_gesture_end(hand_id, current_gesture)
                    if end_result:
                        end_result['hand_type'] = hand_type
                        end_result['display_message'] = detector.get_display_message(end_result) + " [ENDED]"
                        results.append(end_result)
                        static_gesture_ended = True
                    
                    # 如果检测到新手势，添加到结果
                    if current_result:
                        # 检查是否是新手势（避免重复发送开始信息）
                        if hand_id not in detector.active_gestures or detector.active_gestures[hand_id]['gesture'] != current_result['gesture']:
                            # 标记为活跃手势
                            detector.mark_gesture_active(hand_id, current_result['gesture'], current_result['confidence'])
                            # 添加开始标记
                            current_result['details'] = current_result.get('details', {})
                            current_result['details']['tag'] = 'start'
                            # 添加显示消息
                            current_result['display_message'] = detector.get_display_message(current_result)
                            results.append(current_result)
                        
                except Exception as e:
                    print(f"静态手势检测器 {detector.name} 出错: {e}")
        
        # 然后检测动态手势
        for detector in self.detectors:
            if not isinstance(detector, StaticGestureDetector):
                try:
                    result = detector.detect(landmarks, hand_id, hand_type)
                    if result:
                        # 添加显示消息到结果中
                        result['display_message'] = detector.get_display_message(result)
                        results.append(result)
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
    
    def on_hand_lost(self, hand_id: str):
        """
        当手部丢失时调用，重置相关的静态手势检测历史并发送结束信息
        Args:
            hand_id: 丢失的手部ID
        """
        for detector in self.detectors:
            if isinstance(detector, StaticGestureDetector):
                # 检查是否有活跃的静态手势需要结束
                if hand_id in detector.active_gestures:
                    active_gesture = detector.active_gestures[hand_id]
                    end_result = {
                        'gesture': active_gesture['gesture'],
                        'hand_type': 'Unknown',  # 手部已丢失，无法确定类型
                        'confidence': active_gesture['confidence'],
                        'details': {'tag': 'end'},
                        'display_message': detector.get_display_message({
                            'gesture': active_gesture['gesture'],
                            'hand_type': 'Unknown',
                            'confidence': active_gesture['confidence']
                        }) + " [ENDED - HAND LOST]"
                    }
                    
                    # 发送结束信息
                    from gesture_output import output_gesture_detection
                    output_gesture_detection(end_result, hand_id)
                
                # 重置检测历史
                detector.reset_detection_history(hand_id)
    
    def on_all_hands_lost(self):
        """
        当所有手部都丢失时调用，重置所有静态手势检测历史并发送结束信息
        """
        for detector in self.detectors:
            if isinstance(detector, StaticGestureDetector):
                # 为所有活跃的静态手势发送结束信息
                for hand_id, active_gesture in detector.active_gestures.items():
                    end_result = {
                        'gesture': active_gesture['gesture'],
                        'hand_type': 'Unknown',  # 手部已丢失，无法确定类型
                        'confidence': active_gesture['confidence'],
                        'details': {'tag': 'end'},
                        'display_message': detector.get_display_message({
                            'gesture': active_gesture['gesture'],
                            'hand_type': 'Unknown',
                            'confidence': active_gesture['confidence']
                        }) + " [ENDED - ALL HANDS LOST]"
                    }
                    
                    # 发送结束信息
                    from gesture_output import output_gesture_detection
                    output_gesture_detection(end_result, hand_id)
                
                # 重置检测历史
                detector.reset_detection_history()
