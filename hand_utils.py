"""
手部工具类 - 提供手部计算和可视化功能
"""

import math
from typing import List, Tuple, Optional

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
    def is_finger_extended_and_upward(landmarks: List[List[int]], finger_tip_index: int, 
                                    finger_pip_index: int, finger_mcp_index: int, 
                                    distance_threshold_percent: float = 0.6) -> bool:
        """
        判断手指是否伸直（基于距离百分比）且朝上
        Args:
            landmarks: 手部关键点列表
            finger_tip_index: 指尖索引
            finger_pip_index: PIP 关节索引
            finger_mcp_index: MCP 关节索引
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
        upward = tip[1] < pip[1] < mcp[1]  # 指尖Y坐标小于PIP且PIP小于MCP
        
        return extended and upward
    
    @staticmethod
    def is_finger_bent(landmarks: List[List[int]], finger_tip_index: int, 
                      finger_pip_index: int) -> bool:
        """
        判断手指是否弯曲 - 支持任意手部朝向
        使用距离比较法，比单纯的坐标比较更准确
        Args:
            landmarks: 手部关键点列表
            finger_tip_index: 指尖索引
            finger_pip_index: PIP关节索引
            finger_mcp_index: MCP关节索引（可选，提供时判断更准确）
        Returns:
            手指是否弯曲
        """
        tip = landmarks[finger_tip_index]
        pip = landmarks[finger_pip_index]
        
        # 使用手腕作为参考点
        wrist = landmarks[0]
        
        # 计算指尖到手腕和PIP到手腕的距离
        tip_to_wrist_dist = HandUtils.calculate_distance(tip, wrist)
        pip_to_wrist_dist = HandUtils.calculate_distance(pip, wrist)
        
        # 如果指尖到手腕的距离小于PIP到手腕的距离，说明手指弯曲
        return tip_to_wrist_dist < pip_to_wrist_dist * 0.9
    
    @staticmethod
    def calculate_thumb_angle(landmarks: List[List[int]]) -> float:
        """
        计算大拇指与垂直方向的夹角（双向）
        Args:
            landmarks: 手部关键点列表
        Returns:
            大拇指角度（度），范围 0-90 度，不论向上还是向下
        """
        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]
        
        # 计算大拇指向量（从MCP到TIP）
        thumb_vector = [thumb_tip[0] - thumb_mcp[0], thumb_tip[1] - thumb_mcp[1]]
        
        # 计算向量长度
        thumb_length = math.sqrt(thumb_vector[0]**2 + thumb_vector[1]**2)
        
        if thumb_length == 0:
            return 90.0
        
        # 计算与垂直方向的夹角（使用Y分量的绝对值）
        # abs(cos(θ)) = |y_component| / length
        cos_angle = abs(thumb_vector[1]) / thumb_length
        cos_angle = min(1.0, cos_angle)  # 限制在[0, 1]范围内
        
        # 计算角度（这给出的是与垂直方向的夹角）
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
    def is_thumb_close_to_palm(landmarks: List[List[int]], distance_threshold_percent: float = 0.4) -> bool:
        """
        判断拇指是否靠近掌心
        Args:
            landmarks: 手部关键点列表
            distance_threshold_percent: 距离阈值百分比（相对于手掌基准长度）
        Returns:
            拇指是否靠近掌心
        """
        thumb_tip = landmarks[4]
        palm_center = HandUtils.calculate_palm_center(landmarks)
        palm_base_length = HandUtils.calculate_palm_base_length(landmarks)
        
        # 计算拇指尖到掌心的距离
        thumb_to_palm_distance = HandUtils.calculate_distance(thumb_tip, list(palm_center))
        
        # 计算距离比例
        distance_ratio = thumb_to_palm_distance / palm_base_length if palm_base_length > 0 else 1.0
        
        # 如果距离小于阈值，认为拇指靠近掌心
        return distance_ratio < distance_threshold_percent

    @staticmethod
    def is_hand_upward(landmarks: List[List[int]]) -> bool:
        """
        检查手是否向上
        Args:
            landmarks: 手部关键点列表
        Returns:
            手是否向上
        """
        wrist = landmarks[0]
        
        # 检查手指尖的y坐标是否都小于手腕的y坐标
        fingertips = [landmarks[i] for i in HandUtils.FINGERTIPS]
        upward_fingers = sum(1 for tip in fingertips if tip[1] < wrist[1])
        
        return upward_fingers == 5
    
    @staticmethod
    def detect_palm_back_orientation(landmarks: List[List[int]], hand_type: Optional[str] = None) -> str:
        """
        检测手心还是手背朝向摄像头
        基于手指从左到右的排列顺序和左右手类型来判断
        Args:
            landmarks: 手部关键点列表
            hand_type: 手的类型 ("Left" 或 "Right")，如果为None则自动检测
        Returns:
            "palm": 手心朝向摄像头
            "back": 手背朝向摄像头  
            "uncertain": 不确定
        """
        # 首先检查手是否向上且张开
        if not HandUtils.is_hand_upward(landmarks) and not HandUtils.is_hand_open(landmarks):
            return "uncertain"
        
        # 获取手指尖的位置
        thumb_tip = landmarks[4]    # 拇指尖
        index_tip = landmarks[8]    # 食指尖
        middle_tip = landmarks[12]  # 中指尖
        ring_tip = landmarks[16]    # 无名指尖
        pinky_tip = landmarks[20]   # 小指尖
        
        left_thumb_position = thumb_tip[0] < index_tip[0] < middle_tip[0] < ring_tip[0] < pinky_tip[0]
        right_thumb_position = thumb_tip[0] > index_tip[0] > middle_tip[0] > ring_tip[0] > pinky_tip[0]
        
        # 根据手的类型和拇指位置判断朝向
        if hand_type == "Left":
            if left_thumb_position:
                return "back"
            elif right_thumb_position:
                return "palm"
            else:
                return "uncertain"
        else:  # Right hand
            if right_thumb_position:
                return "bacl"
            elif left_thumb_position:
                return "palm"
            else:
                return "uncertain"
            
    @staticmethod
    def is_hand_open(landmarks: List[List[int]], open_threshold: float = 0.5) -> bool:
        """
        检查手是否张开
        Args:
            landmarks: 手部关键点列表
            open_threshold: 张开阈值（相对于手掌基准长度的比例）
        Returns:
            手是否张开
        """
        palm_center = HandUtils.calculate_palm_center(landmarks)
        palm_base_length = HandUtils.calculate_palm_base_length(landmarks)
        
        if palm_base_length <= 0:
            return False
        
        fingertip_distances = HandUtils.calculate_fingertip_distances(landmarks, palm_center)
        
        # 检查是否有足够多的手指远离掌心（张开状态）
        open_fingers = sum(1 for dist in fingertip_distances if dist > palm_base_length * open_threshold)
        
        return open_fingers == 5
    
    @staticmethod
    def is_hand_closed(landmarks: List[List[int]], distances: List[float]) -> bool:
        """判断手是否处于握拳状态"""
        # 计算手掌基准长度
        palm_base_length = HandUtils.calculate_palm_base_length(landmarks)
        
        if palm_base_length <= 0:
            return False
        
        # 检查所有手指尖到掌心的距离是否都很小
        max_allowed_distance = palm_base_length * 0.5  # 握拳时手指尖应该很接近掌心
        close_fingers = sum(1 for dist in distances if dist < max_allowed_distance)
        
        return close_fingers == 5  # 所有5根手指都必须接近掌心
    
    @staticmethod
    def check_two_finger_pose(landmarks: List[List[int]], palm_base_length: float, finger_distance_threshold: float) -> bool:
        """检查是否为双指姿态（食指和中指并拢朝上，其他手指弯曲）"""
        # 1. 检查食指和中指是否伸直且朝上
        index_extended = HandUtils.is_finger_extended_and_upward(landmarks, 8, 6, 5, 0.6)
        middle_extended = HandUtils.is_finger_extended_and_upward(landmarks, 12, 10, 9, 0.6)
        
        # 2. 检查无名指和小指是否弯曲
        ring_bent = HandUtils.is_finger_bent(landmarks, 16, 14)
        pinky_bent = HandUtils.is_finger_bent(landmarks, 20, 18)
        
        # 3. 检查拇指是否靠近掌心
        thumb_close_to_palm = HandUtils.is_thumb_close_to_palm(landmarks, 0.5)
        
        # 4. 检查食指和中指是否并拢（距离很近）
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        finger_distance = HandUtils.calculate_distance(index_tip, middle_tip)
        fingers_close = finger_distance < palm_base_length * finger_distance_threshold

        return (index_extended and middle_extended and ring_bent and
                pinky_bent and thumb_close_to_palm and fingers_close)