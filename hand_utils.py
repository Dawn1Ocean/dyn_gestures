"""
手部工具类 - 提供手部计算和可视化功能
"""

import cv2
import math
from typing import List, Tuple
import numpy as np


class HandUtils:
    """手部工具类"""
    
    # 手部关键点索引常量
    FINGERTIPS = [4, 8, 12, 16, 20]  # 拇指尖、食指尖、中指尖、无名指尖、小指尖
    PALM_POINTS = [0, 1, 5, 9, 13, 17]  # 手腕、拇指根、食指根、中指根、无名指根、小指根
    
    @staticmethod
    def calculate_palm_center(landmarks: List[List[int]]) -> Tuple[int, int]:
        """
        计算手掌中心
        Args:
            landmarks: 手部关键点列表
        Returns:
            手掌中心坐标 (x, y)
        """
        # 手腕和五个手指根部
        palm_points = [landmarks[i] for i in HandUtils.PALM_POINTS]
        
        center_x = sum(point[0] for point in palm_points) / len(palm_points)
        center_y = sum(point[1] for point in palm_points) / len(palm_points)
        
        return (int(center_x), int(center_y))
    
    @staticmethod
    def calculate_distance(p1: List[int], p2: List[int]) -> float:
        """
        计算两点之间的距离
        Args:
            p1: 第一个点坐标
            p2: 第二个点坐标
        Returns:
            距离值
        """
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    @staticmethod
    def calculate_palm_base_length(landmarks: List[List[int]]) -> float:
        """
        计算手掌基准长度（手腕到中指根部的距离）
        Args:
            landmarks: 手部关键点列表
        Returns:
            手掌基准长度
        """
        wrist = landmarks[0]
        middle_mcp = landmarks[9]  # 中指根部
        return HandUtils.calculate_distance(wrist, middle_mcp)
    
    @staticmethod
    def calculate_fingertip_distances(landmarks: List[List[int]], palm_center: Tuple[int, int]) -> List[float]:
        """
        计算所有手指尖到手掌中心的距离
        Args:
            landmarks: 手部关键点列表
            palm_center: 手掌中心坐标
        Returns:
            五个手指尖到手掌中心的距离列表
        """
        fingertips = [landmarks[i] for i in HandUtils.FINGERTIPS]
        return [HandUtils.calculate_distance(tip, list(palm_center)) for tip in fingertips]
    
    @staticmethod
    def calculate_fingertip_variance(landmarks: List[List[int]]) -> float:
        """
        计算手指尖之间距离的方差（用于检测手掌张开程度）
        Args:
            landmarks: 手部关键点列表
        Returns:
            手指尖距离方差
        """
        fingertips = [landmarks[i] for i in HandUtils.FINGERTIPS]
        
        distances = []
        for i in range(len(fingertips)):
            for j in range(i + 1, len(fingertips)):
                dist = HandUtils.calculate_distance(fingertips[i], fingertips[j])
                distances.append(dist)
        
        return float(np.var(distances)) if len(distances) > 1 else 0.0
    
    @staticmethod
    def is_finger_extended(landmarks: List[List[int]], finger_tip_index: int, 
                          finger_pip_index: int, finger_mcp_index: int,
                          distance_threshold_percent: float = 0.6) -> bool:
        """
        判断手指是否伸直（基于距离百分比）
        Args:
            landmarks: 手部关键点列表
            finger_tip_index: 指尖索引
            finger_pip_index: PIP关节索引
            finger_mcp_index: MCP关节索引
            distance_threshold_percent: 距离阈值百分比
        Returns:
            手指是否伸直
        """
        wrist = landmarks[0]
        tip = landmarks[finger_tip_index]
        pip = landmarks[finger_pip_index]
        mcp = landmarks[finger_mcp_index]
        
        # 计算手掌基准长度
        palm_base_length = HandUtils.calculate_palm_base_length(landmarks)
        
        # 检查手指是否伸直（指尖到手腕的距离 > 阈值 * 手掌基准长度）
        tip_to_wrist_dist = HandUtils.calculate_distance(tip, wrist)
        extended = tip_to_wrist_dist > palm_base_length * distance_threshold_percent
        
        # 检查手指是否朝上（Y坐标递减：tip < pip < mcp）
        upward = tip[1] < pip[1] < mcp[1]
        
        return extended and upward
    
    @staticmethod
    def is_finger_bent(landmarks: List[List[int]], finger_tip_index: int, 
                      finger_pip_index: int) -> bool:
        """
        判断手指是否弯曲
        Args:
            landmarks: 手部关键点列表
            finger_tip_index: 指尖索引
            finger_pip_index: PIP关节索引
        Returns:
            手指是否弯曲
        """
        tip = landmarks[finger_tip_index]
        pip = landmarks[finger_pip_index]
        
        # 如果指尖Y坐标大于PIP关节，认为是弯曲的
        return tip[1] > pip[1]
    
    @staticmethod
    def calculate_thumb_angle(landmarks: List[List[int]]) -> float:
        """
        计算大拇指与垂直方向的夹角
        Args:
            landmarks: 手部关键点列表
        Returns:
            大拇指角度（度）
        """
        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]
        
        # 计算大拇指向量（从MCP到TIP）
        thumb_vector = [thumb_tip[0] - thumb_mcp[0], thumb_tip[1] - thumb_mcp[1]]
        # 垂直向上的向量
        vertical_vector = [0, -1]
        
        # 计算夹角
        dot_product = thumb_vector[0] * vertical_vector[0] + thumb_vector[1] * vertical_vector[1]
        thumb_length = math.sqrt(thumb_vector[0]**2 + thumb_vector[1]**2)
        
        if thumb_length == 0:
            return 90.0
        
        cos_angle = dot_product / thumb_length
        cos_angle = max(-1, min(1, cos_angle))  # 限制在[-1, 1]范围内
        angle_rad = math.acos(cos_angle)
        angle_deg = math.degrees(angle_rad)
        
        return angle_deg
    
    @staticmethod
    def check_fingers_spread(landmarks: List[List[int]], finger1_index: int, 
                           finger2_index: int, reference_length_ratio: float = 0.3) -> bool:
        """
        检查两个手指是否分开（如V字形状）
        Args:
            landmarks: 手部关键点列表
            finger1_index: 第一个手指尖索引
            finger2_index: 第二个手指尖索引
            reference_length_ratio: 参考长度比值
        Returns:
            手指是否分开
        """
        finger1_tip = landmarks[finger1_index]
        finger2_tip = landmarks[finger2_index]
        
        # 计算手指间距离
        fingers_distance = HandUtils.calculate_distance(finger1_tip, finger2_tip)
        
        # 计算手掌基准长度作为参考
        palm_base_length = HandUtils.calculate_palm_base_length(landmarks)
        
        # 如果手指间距离大于手掌基准长度的指定比例，认为是张开的
        return fingers_distance > palm_base_length * reference_length_ratio
    
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