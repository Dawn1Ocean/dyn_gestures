"""
配置文件 - 存储所有配置参数
"""

# 摄像头配置
CAMERA_INDEX = 0
CAMERA_FPS = 60  # 摄像头帧率设置
CAMERA_FRAME_WIDTH = 640  # 摄像头帧宽度
CAMERA_FRAME_HEIGHT = 360  # 摄像头帧高度

# 手势检测配置
HAND_DETECTION_CONFIG = {
    'static_mode': False,      # 是否使用静态模式
    'max_hands': 1,           # 最大检测手数
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
    
    # 张开到握拳手势
    'hand_close': {
        'history_length': 10,
        'variance_change_percent': 40,
        'distance_multiplier': 0.7,
        'fist_hold_frames': 30,  # 握拳状态需要保持的帧数
        'tracking_config': {
            'enable_tracking': True,        # 启用轨迹追踪
            'debounce_frames': 5,          # 去抖帧数
            'max_trail_points': 100,       # 最大轨迹点数
            'trail_thickness': 3,          # 轨迹线粗细
            'trail_alpha': 0.7,            # 轨迹透明度
            # 命令行轨迹输出配置
            'enable_console_output': True, # 启用命令行轨迹变化输出
            'output_interval_frames': 3,   # 输出间隔帧数（回报率控制）
            'movement_threshold': 5,       # 移动阈值（像素），小于此值不输出
            'output_format': 'simple',       # 输出格式：'json' 或 'simple'
        }
    },
    
    # 手左右挥动手势
    'hand_swipe': {
        'history_length': 15,
        'min_distance_percent': 0.5,      # 最小移动距离百分比（相对于手掌基准长度）
        'min_movement_frames': 15           # 最小连续移动帧数
    },
    
    # 手掌翻转手势
    'hand_flip': {
        'history_length': 20,
        'max_movement_percent': 0.15,      # 最大移动距离百分比（相对于手掌基准长度）
        'min_flip_frames': 10              # 翻转检测的最小帧数
    },
    
    # 数字一手势
    'finger_count_one': {
        'distance_threshold_percent': 0.6,  # 手指伸展阈值（相对于手掌基准长度）
        'required_frames': 15  # 需要连续检测的帧数
    },
    
    # 数字二手势
    'finger_count_two': {
        'distance_threshold_percent': 0.6,  # 手指伸展阈值（相对于手掌基准长度）
        'required_frames': 15  # 需要连续检测的帧数
    },
    
    # 数字三手势
    'finger_count_three': {
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
    },

    # 倒竖大拇指
    'thumbs_down': {
        'thumb_distance_threshold': 0.6,        # 大拇指指尖距离掌心阈值（百分比）
        'other_fingers_threshold': 0.45,        # 其他手指指尖距离掌心阈值（百分比）
        'thumb_angle_threshold': 45.0,          # 大拇指角度阈值（度）
        'thumb_isolation_threshold': 0.5,       # 大拇指与其他手指PIP最小距离阈值（百分比）
        'required_frames': 15                   # 需要连续检测的帧数
    }
}

# 手势类型定义
GESTURE_TYPES = {
    'static_gestures': ['FingerCountOne', 'FingerCountTwo', 'FingerCountThree', 'ThumbsUp', 'ThumbsDown'],  # 静态手势列表
    'dynamic_gestures': ['HandOpen', 'HandClose', 'HandSwipe', 'HandFlip'],  # 动态手势列表
    'confidence_threshold_for_update': 5.0  # 静态手势置信度变化阈值
}

# 显示配置
DISPLAY_CONFIG = {
    'window_name': 'Hand Gesture Detection',
    'show_palm_center': True,
    'show_landmarks': True,
    'flip_image': True,                 # cvzone的flipType参数
    'show_camera_window': True,         # 是否显示摄像头识别画面
    'gesture_message_duration': 15,     # 帧数
    'show_fps': True,                   # 显示FPS
    'fps_update_interval': 10           # FPS更新间隔（帧数）
}

# 颜色配置 (BGR格式)
COLORS = {
    'palm_center': (0, 255, 255),      # 黄色
    'text_primary': (255, 0, 0),       # 蓝色
    'text_secondary': (0, 0, 255),     # 红色
    'gesture_message': (0, 255, 0),    # 绿色
    'palm_info': (0, 255, 255),        # 青色
    'fps_text': (255, 255, 255),       # 白色 - FPS文本颜色
    'fist_trail': (0, 255, 255),       # 青色 - 握拳轨迹颜色
    'fist_center': (0, 0, 255),        # 红色 - 握拳时掌心颜色
}
