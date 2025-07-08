"""
动态手势检测器包
"""

from .hand_open import HandOpenDetector
from .hand_close import HandCloseDetector
from .hand_swipe import HandSwipeDetector
from .hand_flip import HandFlipDetector
from .two_finger_swipe import TwoFingerSwipeDetector

__all__ = ['HandOpenDetector', 'HandCloseDetector', 'HandSwipeDetector', 'HandFlipDetector', 'TwoFingerSwipeDetector']