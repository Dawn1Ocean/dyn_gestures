"""
手势检测器基类
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from gestures.trajectory_tracker import TrajectoryTracker


class GestureDetector(ABC):
    """手势检测器抽象基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.history = {}  # 存储每只手的历史数据
    
    @abstractmethod
    def detect(self, landmarks: List[List[int]], hand_id: str, hand_type: str) -> Optional[Dict[str, Any]]:
        """
        检测手势
        Args:
            landmarks: 手部关键点列表
            hand_id: 手部ID
            hand_type: 手部类型 ("Left" 或 "Right")
        Returns:
            检测结果字典或None
        """
        pass
    
    @abstractmethod
    def reset(self, hand_id: Optional[str] = None):
        """重置检测器状态"""
        pass
    
    def get_display_message(self, gesture_result: Dict[str, Any]) -> str:
        """
        获取手势的显示消息
        Args:
            gesture_result: 手势检测结果
        Returns:
            显示消息字符串
        """
        gesture_name = gesture_result['gesture']
        hand_type = gesture_result['hand_type']
        confidence = gesture_result.get('confidence', 0)
        
        # 默认显示格式
        return f"{hand_type} Hand: {gesture_name} (Confidence: {confidence:.1f}%)"


class StaticGestureDetector(GestureDetector):
    """静态手势检测器基类"""
    
    def __init__(self, name: str, required_frames: int = 30, debounce_frames: int = 5):
        super().__init__(name)
        self.required_frames = required_frames  # 需要连续检测的帧数
        self.debounce_frames = debounce_frames  # 去抖帧数
        self.detection_history = {}  # 存储每只手的检测历史 {hand_id: {'gesture': str, 'count': int, 'last_confidence': float}}
        
        # 输出频率控制
        import config
        output_config = config.DISPLAY_CONFIG.get('gesture_output', {})
        self.output_interval_frames = output_config.get('static_gesture_output_interval', 30)
        self.output_counters = {}  # {hand_id: int} 输出计数器
    
    def check_continuous_detection(self, hand_id: str, gesture_name: str, confidence: float) -> bool:
        """
        检查是否连续检测到足够帧数
        Args:
            hand_id: 手部ID
            gesture_name: 手势名称
            confidence: 置信度
        Returns:
            是否满足连续检测条件
        """
        if hand_id not in self.detection_history:
            self.detection_history[hand_id] = {'gesture': None, 'count': 0, 'last_confidence': 0}
            self.output_counters[hand_id] = 0
        
        history = self.detection_history[hand_id]
        
        # 如果检测到相同手势，增加计数
        if history['gesture'] == gesture_name:
            history['count'] += 1
            history['last_confidence'] = confidence
        else:
            # 检测到不同手势，重置计数
            history['gesture'] = gesture_name
            history['count'] = 1
            history['last_confidence'] = confidence
            # 重置输出计数器
            self.output_counters[hand_id] = 0
        
        # 检查是否达到所需帧数
        return history['count'] >= self.required_frames
    
    def should_output_gesture(self, hand_id: str) -> bool:
        """
        检查是否应该输出手势（基于输出间隔控制）
        Args:
            hand_id: 手部ID
        Returns:
            是否应该输出
        """
        if hand_id not in self.output_counters:
            # 第一次满足连续检测条件时立即输出
            self.output_counters[hand_id] = 0
            return True
        
        self.output_counters[hand_id] += 1
        
        if self.output_counters[hand_id] >= self.output_interval_frames:
            self.output_counters[hand_id] = 0
            return True
        
        return False
    
    def reset_detection_history(self, hand_id: Optional[str] = None):
        """重置检测历史"""
        if hand_id is None:
            self.detection_history.clear()
            self.output_counters.clear()
        else:
            if hand_id in self.detection_history:
                del self.detection_history[hand_id]
            if hand_id in self.output_counters:
                del self.output_counters[hand_id]

    def reset(self, hand_id: Optional[str] = None):
        """重置静态手势检测状态"""
        self.reset_detection_history(hand_id)


class DynamicGestureDetector(GestureDetector):
    """动态手势检测器基类"""
    
    def __init__(self, name: str, history_length: int = 10, cooldown_frames: int = 30):
        super().__init__(name)
        self.history_length = history_length
        self.cooldown_frames = cooldown_frames  # 冷却期帧数
        self.cooldown_counters = {}  # 存储每只手的冷却计数器 {hand_id: remaining_frames}
    
    def is_in_cooldown(self, hand_id: str) -> bool:
        """
        检查指定手是否在冷却期内
        Args:
            hand_id: 手部ID
        Returns:
            是否在冷却期内
        """
        if hand_id not in self.cooldown_counters:
            return False
        
        # 减少冷却计数器
        self.cooldown_counters[hand_id] = max(0, self.cooldown_counters[hand_id] - 1)
        
        # 如果冷却期结束，移除计数器
        if self.cooldown_counters[hand_id] <= 0:
            del self.cooldown_counters[hand_id]
            return False
        
        return True
    
    def start_cooldown(self, hand_id: str):
        """
        为指定手开始冷却期
        Args:
            hand_id: 手部ID
        """
        self.cooldown_counters[hand_id] = self.cooldown_frames
    
    def reset_cooldown(self, hand_id: Optional[str] = None):
        """
        重置冷却期
        Args:
            hand_id: 手部ID，如果为None则重置所有
        """
        if hand_id is None:
            self.cooldown_counters.clear()
        elif hand_id in self.cooldown_counters:
            del self.cooldown_counters[hand_id]

class TrackerGestureDetector(DynamicGestureDetector):
    """轨迹追踪检测器基类"""
    
    def __init__(self, name: str, tracking_config, smoothing_config, history_length: int = 10, cooldown_frames: int = 30):
        super().__init__(name, history_length, cooldown_frames)
        self.trajectory_tracker = TrajectoryTracker(tracking_config, smoothing_config)

    def get_trajectory_tracker(self) -> TrajectoryTracker:
        """获取轨迹追踪器实例"""
        return self.trajectory_tracker
