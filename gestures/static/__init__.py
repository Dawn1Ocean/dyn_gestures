"""
静态手势检测器包
"""

from .finger_count_one import FingerCountOneDetector
from .finger_count_two import FingerCountTwoDetector
from .finger_count_three import FingerCountThreeDetector
from .thumbs import ThumbsDetector

__all__ = ['FingerCountOneDetector', 'FingerCountTwoDetector', 'FingerCountThreeDetector', 'ThumbsDetector']