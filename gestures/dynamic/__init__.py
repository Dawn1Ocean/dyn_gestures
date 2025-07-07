"""
动态手势检测器包
"""

from .hand_open import HandOpenDetector
from .hand_close import HandCloseDetector

__all__ = ['HandOpenDetector', 'HandCloseDetector']