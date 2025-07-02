"""
配置文件 - 存储所有配置参数
"""

# 摄像头配置
CAMERA_INDEX = 0

# 手势检测配置
HAND_DETECTION_CONFIG = {
    'static_mode': False,      # 是否使用静态模式
    'max_hands': 2,           # 最大检测手数
    'model_complexity': 1,    # 模型复杂度 (0-2)
    'detection_confidence': 0.5,        # 检测置信度
    'min_tracking_confidence': 0.5      # 最小跟踪置信度
}

# 手势识别参数
GESTURE_CONFIG = {
    # 握拳到张开手势
    'hand_open': {
        'history_length': 10,
        'variance_change_percent': 50,
        'distance_multiplier': 1.5
    },
    
    # V字手势
    'peace_sign': {
        'distance_threshold_percent': 0.6,  # 手指伸展阈值（相对于手掌基准长度）
        'required_frames': 15  # 需要连续检测的帧数
    },
    
    # 竖大拇指
    'thumbs_up': {
        'thumb_distance_threshold': 0.6,        # 大拇指指尖距离掌心阈值（百分比）
        'other_fingers_threshold': 0.45,        # 其他手指指尖距离掌心阈值（百分比）
        'thumb_angle_threshold': 45.0,          # 大拇指角度阈值（度）
        'thumb_isolation_threshold': 0.5,       # 大拇指与其他手指PIP最小距离阈值（百分比）
        'required_frames': 15                   # 需要连续检测的帧数
    }
}

# 手势类型定义
GESTURE_TYPES = {
    'static_gestures': ['PeaceSign', 'ThumbsUp'],  # 静态手势列表
    'dynamic_gestures': ['HandOpen'],  # 动态手势列表
    'confidence_threshold_for_update': 5.0  # 静态手势置信度变化阈值
}

# 显示配置
DISPLAY_CONFIG = {
    'window_name': 'Hand Gesture Detection',
    'show_palm_center': True,
    'show_landmarks': True,
    'flip_image': True,                 # cvzone的flipType参数
    'show_camera_window': True,         # 是否显示摄像头识别画面
    'gesture_message_duration': 15      # 帧数
}

# 颜色配置 (BGR格式)
COLORS = {
    'palm_center': (0, 255, 255),      # 黄色
    'text_primary': (255, 0, 0),       # 蓝色
    'text_secondary': (0, 0, 255),     # 红色
    'gesture_message': (0, 255, 0),    # 绿色
    'palm_info': (0, 255, 255)         # 青色
}
