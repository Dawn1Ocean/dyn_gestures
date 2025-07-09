import cv2
from typing import Tuple

import config
from hand_utils import HandUtils

class Display:

    @staticmethod
    def draw_palm_center(img, palm_center: Tuple[int, int], color: Tuple[int, int, int] = (0, 255, 255)):
        """
        在图像上绘制手掌中心
        Args:
            img: 图像
            palm_center: 手掌中心坐标
            color: 颜色 (B, G, R)
        """
        cv2.circle(img, palm_center, 8, color, -1)  # 填充圆
        cv2.circle(img, palm_center, 12, (0, 0, 0), 2)  # 黑色边框

    @staticmethod
    def draw_text_info(img, hand_type: str, info_dict: dict, position_offset: int = 0):
        """
        在图像上绘制手部信息
        Args:
            img: 图像
            hand_type: 手部类型
            info_dict: 信息字典
            position_offset: Y轴位置偏移
        """
        y_start = 50 + position_offset
        line_height = 20
        
        # 绘制手部类型
        cv2.putText(img, f'{hand_type} Hand:', 
                    (50, y_start), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # 绘制详细信息
        for i, (key, value) in enumerate(info_dict.items()):
            y_pos = y_start + (i + 1) * line_height
            text = f'  {key}: {value}'
            cv2.putText(img, text, 
                        (50, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    @staticmethod
    def draw_gesture_message(img, message: str, color: Tuple[int, int, int] = (0, 255, 0)):
        """
        在图像底部绘制手势消息
        Args:
            img: 图像
            message: 消息文本
            color: 文本颜色
        """
        cv2.putText(img, message, (50, img.shape[0] - 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)

    @staticmethod
    def draw_fps(img, fps: float, color: Tuple[int, int, int] = (255, 255, 255)):
        """
        在图像右上角绘制FPS信息
        Args:
            img: 图像
            fps: FPS值
            color: 文本颜色
        """
        fps_text = f"FPS: {fps:.1f}"
        text_size = cv2.getTextSize(fps_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        x = img.shape[1] - text_size[0] - 10  # 右边距10像素
        y = 30  # 顶部距离30像素
        
        # 绘制背景矩形
        cv2.rectangle(img, (x - 5, y - 20), (x + text_size[0] + 5, y + 5), (0, 0, 0), -1)
        # 绘制FPS文本
        cv2.putText(img, fps_text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    @staticmethod
    def draw_hand_info(img, hand, hand_index, detector):
        """绘制手部信息"""
        landmarks = hand["lmList"]
        hand_type = hand["type"]
        
        # 计算并绘制手掌中心
        palm_center = HandUtils.calculate_palm_center(landmarks)
        if config.DISPLAY_CONFIG['show_palm_center']:
            Display.draw_palm_center(img, palm_center, config.COLORS['palm_center'])

        # 计算手指数量（使用cvzone的方法）
        fingers = detector.fingersUp(hand)
        finger_count = fingers.count(1)
        
        # 准备显示信息
        info_dict = {
            'Fingers': finger_count,
            'Palm': f'({palm_center[0]}, {palm_center[1]})'
        }
        
        # 绘制信息
        Display.draw_text_info(
            img, hand_type, info_dict, 
            position_offset=hand_index * 120
        )