"""
手势检测器包
导入所有可用的手势检测器
"""

from .base import GestureDetector, StaticGestureDetector, DynamicGestureDetector

# 导入动态手势检测器
from .dynamic.hand_open import HandOpenDetector

# 导入静态手势检测器
from .static.peace_sign import PeaceSignDetector
from .static.thumbs import ThumbsDetector

__all__ = [
    'GestureDetector', 
    'StaticGestureDetector', 
    'DynamicGestureDetector',
    'HandOpenDetector',
    'PeaceSignDetector',
    'ThumbsDetector',
]