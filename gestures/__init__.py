"""
手势检测器包
导入所有可用的手势检测器
"""

from .base import GestureDetector, StaticGestureDetector, DynamicGestureDetector

# 导入动态手势检测器
from .dynamic.hand_open import HandOpenDetector
from .dynamic.hand_close import HandCloseDetector
from .dynamic.hand_swipe import HandSwipeDetector
from .dynamic.hand_flip import HandFlipDetector

# 导入静态手势检测器
from .static.finger_count_one import FingerCountOneDetector
from .static.finger_count_two import FingerCountTwoDetector
from .static.finger_count_three import FingerCountThreeDetector
from .static.thumbs import ThumbsDetector

__all__ = [
    'GestureDetector', 
    'StaticGestureDetector', 
    'DynamicGestureDetector',
    'HandOpenDetector',
    'HandCloseDetector',
    'HandSwipeDetector',
    'HandFlipDetector',
    'FingerCountOneDetector',
    'FingerCountTwoDetector',
    'FingerCountThreeDetector',
    'ThumbsDetector',
]