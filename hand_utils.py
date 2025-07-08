"""
手部工具类 - 提供手部计算和可视化功能
"""

import cv2
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
    def draw_fist_trails(img, trail_points_dict: dict, fist_active_dict: dict, 
                        trail_color=(0, 255, 255), center_color=(0, 0, 255), trail_thickness=3):
        """
        在图像上绘制握拳轨迹
        Args:
            img: 图像
            trail_points_dict: 轨迹点字典 {hand_id: deque of points}
            fist_active_dict: 握拳活跃状态字典 {hand_id: bool}
            trail_color: 轨迹线颜色 (B, G, R)
            center_color: 当前位置圆点颜色 (B, G, R)
            trail_thickness: 轨迹线基础粗细
        """
        for hand_id, is_active in fist_active_dict.items():
            if is_active and hand_id in trail_points_dict:
                trail = list(trail_points_dict[hand_id])
                
                if len(trail) > 1:
                    # 绘制轨迹线
                    for i in range(1, len(trail)):
                        # 计算透明度（newer points more opaque）
                        alpha = i / len(trail)
                        thickness = max(1, int(trail_thickness * alpha))
                        
                        cv2.line(img, trail[i-1], trail[i], trail_color, thickness)
                
                # 绘制当前位置
                if trail:
                    current_pos = trail[-1]
                    cv2.circle(img, current_pos, 8, center_color, -1)
                    cv2.circle(img, current_pos, 10, trail_color, 2)
    
    @staticmethod
    def output_trail_change(hand_id: str, current_pos: Tuple[int, int], hand_type: str,
                           last_output_positions: dict, output_frame_counters: dict,
                           output_interval_frames: int, movement_threshold: float,
                           output_format: str) -> bool:
        """
        输出轨迹变化到命令行
        Args:
            hand_id: 手部ID
            current_pos: 当前位置 (x, y)
            hand_type: 手部类型 (Left/Right)
            last_output_positions: 上次输出位置字典 {hand_id: (x, y)}
            output_frame_counters: 输出帧计数器字典 {hand_id: int}
            output_interval_frames: 输出间隔帧数
            movement_threshold: 移动阈值（像素）
            output_format: 输出格式 ('json' 或 'simple')
        Returns:
            是否输出了轨迹变化
        """
        # 检查输出间隔
        output_frame_counters[hand_id] = output_frame_counters.get(hand_id, 0) + 1
        if output_frame_counters[hand_id] < output_interval_frames:
            return False
        
        # 重置帧计数器
        output_frame_counters[hand_id] = 0
        
        last_pos = last_output_positions.get(hand_id)
        
        if last_pos is not None:
            # 计算移动距离
            dx = current_pos[0] - last_pos[0]
            dy = current_pos[1] - last_pos[1]
            distance = (dx**2 + dy**2)**0.5
            
            # 检查是否超过移动阈值
            if distance >= movement_threshold:
                # 输出轨迹变化
                if output_format == 'json':
                    import json
                    import time
                    output_data = {
                        'timestamp': time.time(),
                        'hand_id': hand_id,
                        'hand_type': hand_type,
                        'position': {
                            'x': current_pos[0],
                            'y': current_pos[1]
                        },
                        'movement': {
                            'dx': dx,
                            'dy': dy,
                            'distance': round(distance, 2)
                        },
                        'previous_position': {
                            'x': last_pos[0],
                            'y': last_pos[1]
                        }
                    }
                    print(f"[TRAIL_OUTPUT] {json.dumps(output_data, separators=(',', ':'))}")
                else:
                    # 简单格式输出
                    print(f"[TRAIL_OUTPUT] {hand_type}_{hand_id}: pos=({current_pos[0]},{current_pos[1]}) "
                          f"move=({dx:+d},{dy:+d}) dist={distance:.1f}")
                
                # 更新上次输出位置
                last_output_positions[hand_id] = current_pos
                return True
        else:
            # 第一次输出，记录位置但不输出
            last_output_positions[hand_id] = current_pos
        
        return False
    
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
        
        # 计算拇指相对于其他四指的位置
        other_fingers_x = [index_tip[0], middle_tip[0], ring_tip[0], pinky_tip[0]]
        avg_other_x = sum(other_fingers_x) / len(other_fingers_x)
        thumb_relative_position = thumb_tip[0] - avg_other_x
        
        # 根据手的类型和拇指位置判断朝向
        if hand_type == "Left":
            # 左手：拇指在右边(positive)表示手心朝向，拇指在左边(negative)表示手背朝向
            if thumb_relative_position > 15:  # 拇指明显在右边
                return "palm"
            elif thumb_relative_position < -15:  # 拇指明显在左边
                return "back"
            else:
                return "uncertain"
        else:  # Right hand
            # 右手：拇指在左边(negative)表示手心朝向，拇指在右边(positive)表示手背朝向
            if thumb_relative_position < -15:  # 拇指明显在左边
                return "palm"
            elif thumb_relative_position > 15:  # 拇指明显在右边
                return "back"
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
    def check_two_finger_pose(landmarks: List[List[int]], palm_base_length: float, finger_distance_threshold: float) -> bool:
        """检查是否为双指姿态（食指和中指并拢朝上，其他手指弯曲）"""
        # 1. 检查食指和中指是否伸直且朝上
        index_extended = HandUtils.is_finger_extended(landmarks, 8, 6, 5, 0.6)
        middle_extended = HandUtils.is_finger_extended(landmarks, 12, 10, 9, 0.6)
        
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