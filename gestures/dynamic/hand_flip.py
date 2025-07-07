"""
手掌翻转手势检测器 - 动态手势
"""

import numpy as np
from collections import deque
from typing import List, Dict, Any, Optional, Tuple
from ..base import DynamicGestureDetector
from hand_utils import HandUtils


class HandFlipDetector(DynamicGestureDetector):
    """手掌翻转手势检测器"""
    
    def __init__(self, max_movement_percent: float = 0.15, min_flip_frames: int = 10, 
                 history_length: int = 20):
        super().__init__("HandFlip", history_length)
        self.max_movement_percent = max_movement_percent  # 最大移动距离百分比（相对于手掌基准长度）
        self.min_flip_frames = min_flip_frames  # 翻转检测的最小帧数
        
    def detect(self, landmarks: List[List[int]], hand_id: str, hand_type: str) -> Optional[Dict[str, Any]]:
        """检测手掌翻转手势"""
        # 初始化历史记录
        if hand_id not in self.history:
            self.history[hand_id] = {
                'palm_positions': deque(maxlen=self.history_length),
                'hand_orientations': deque(maxlen=self.history_length),
                'hand_open_states': deque(maxlen=self.history_length),
                'flip_detection_state': 'waiting',  # 'waiting', 'detecting', 'completed'
                'initial_orientation': None,
                'flip_start_frame': 0
            }
        
        hand_history = self.history[hand_id]
        
        # 计算当前手掌中心、基准长度和朝向
        palm_center = HandUtils.calculate_palm_center(landmarks)
        palm_base_length = HandUtils.calculate_palm_base_length(landmarks)
        hand_orientation = self._calculate_hand_orientation(landmarks, hand_type)
        
        # 检查手是否张开
        is_hand_open = self._is_hand_open(landmarks)
        
        # 添加到历史记录
        hand_history['palm_positions'].append(palm_center)
        hand_history['hand_orientations'].append(hand_orientation)
        hand_history['hand_open_states'].append(is_hand_open)
        
        # 需要足够的历史数据
        if len(hand_history['palm_positions']) >= self.min_flip_frames:
            result = self._analyze_flip_gesture(hand_history, palm_base_length, hand_type)
            if result:
                # 重置历史以避免重复检测
                self.reset(hand_id)
                return result
        
        return None
    
    def _is_hand_open(self, landmarks: List[List[int]]) -> bool:
        """判断手是否张开（五指张开）"""
        # 计算手掌中心和基准长度
        palm_center = HandUtils.calculate_palm_center(landmarks)
        palm_base_length = HandUtils.calculate_palm_base_length(landmarks)
        
        if palm_base_length <= 0:
            return False
        
        # 计算所有手指尖到掌心的距离
        current_distances = HandUtils.calculate_fingertip_distances(landmarks, palm_center)
        
        # 检查所有五根手指是否都远离掌心（张开状态）
        open_threshold = palm_base_length * 0.6  # 张开时手指尖应该远离掌心
        open_fingers = sum(1 for dist in current_distances if dist > open_threshold)
        
        return open_fingers == 5  # 必须所有五根手指都张开
    
    def _calculate_hand_orientation(self, landmarks: List[List[int]], hand_type: str) -> str:
        """计算手掌朝向（手心还是手背朝向摄像头）"""
        return HandUtils.detect_palm_back_orientation(landmarks, hand_type)
    
    def _analyze_flip_gesture(self, hand_history: dict, palm_base_length: float, 
                            hand_type: str) -> Optional[Dict[str, Any]]:
        """分析翻转手势"""
        positions = list(hand_history['palm_positions'])
        orientations = list(hand_history['hand_orientations'])
        open_states = list(hand_history['hand_open_states'])
        
        # 检查翻转前后手是否都是张开的
        if not self._check_hand_open_throughout(open_states):
            return None
        
        # 检查手掌移动距离是否在阈值内
        if not self._check_movement_within_threshold(positions, palm_base_length):
            return None
        
        # 检查是否发生了翻转
        flip_result = self._detect_orientation_flip(orientations)
        if not flip_result:
            return None
        
        flip_type, flip_description = flip_result
        
        # 计算置信度
        confidence = self._calculate_confidence(
            positions, orientations, open_states, flip_type, palm_base_length
        )
        
        return {
            'gesture': 'HandFlip',
            'hand_type': hand_type,
            'confidence': confidence,
            'details': {
                'description': flip_description,
                'flip_type': flip_type,
                'flip_description': flip_description,
                'movement_distance': round(self._calculate_total_movement(positions), 1),
                'movement_percent': round((self._calculate_total_movement(positions) / palm_base_length) * 100, 1),
                'frames_analyzed': len(positions)
            }
        }
    
    def _check_hand_open_throughout(self, open_states: List[bool]) -> bool:
        """检查整个过程中手是否保持张开"""
        # 要求至少80%的帧中手都是张开的
        open_ratio = sum(open_states) / len(open_states)
        return open_ratio >= 0.8
    
    def _check_movement_within_threshold(self, positions: List[Tuple[int, int]], 
                                       palm_base_length: float) -> bool:
        """检查手掌移动距离是否在阈值内"""
        total_movement = self._calculate_total_movement(positions)
        max_allowed_movement = palm_base_length * self.max_movement_percent
        return total_movement <= max_allowed_movement
    
    def _calculate_total_movement(self, positions: List[Tuple[int, int]]) -> float:
        """计算总移动距离"""
        if len(positions) < 2:
            return 0.0
        
        # 计算起点和终点的距离
        start_pos = positions[0]
        end_pos = positions[-1]
        
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        
        return (dx**2 + dy**2)**0.5
    
    def _detect_orientation_flip(self, orientations: List[str]) -> Optional[Tuple[str, str]]:
        """检测朝向翻转"""
        if len(orientations) < self.min_flip_frames:
            return None
        
        # 过滤掉不确定的朝向
        valid_orientations = [o for o in orientations if o != "uncertain"]
        if len(valid_orientations) < self.min_flip_frames // 2:
            return None
        
        # 获取起始和结束阶段的朝向
        start_segment_size = min(3, len(valid_orientations) // 3)
        end_segment_size = min(3, len(valid_orientations) // 3)
        
        start_orientations = valid_orientations[:start_segment_size]
        end_orientations = valid_orientations[-end_segment_size:]
        
        # 计算起始和结束阶段的主要朝向
        start_palm_count = start_orientations.count("palm")
        start_back_count = start_orientations.count("back")
        
        end_palm_count = end_orientations.count("palm")
        end_back_count = end_orientations.count("back")
        
        # 确定起始和结束的主要朝向
        if start_palm_count > start_back_count:
            start_main_orientation = "palm"
        elif start_back_count > start_palm_count:
            start_main_orientation = "back"
        else:
            return None  # 起始朝向不明确
        
        if end_palm_count > end_back_count:
            end_main_orientation = "palm"
        elif end_back_count > end_palm_count:
            end_main_orientation = "back"
        else:
            return None  # 结束朝向不明确
        
        # 检查是否发生了翻转
        if start_main_orientation != end_main_orientation:
            if start_main_orientation == "palm" and end_main_orientation == "back":
                flip_type = "palm_to_back"
                flip_description = "palm2back"
            else:  # start_main_orientation == "back" and end_main_orientation == "palm"
                flip_type = "back_to_palm" 
                flip_description = "back2palm"
            
            return flip_type, flip_description
        
        return None
    
    def _calculate_angle_difference(self, angle1: float, angle2: float) -> float:
        """计算两个角度之间的差异（考虑360度环绕）"""
        diff = angle2 - angle1
        
        # 处理角度环绕
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360
            
        return diff
    
    def _calculate_confidence(self, positions: List[Tuple[int, int]], 
                            orientations: List[str], open_states: List[bool],
                            flip_type: str, palm_base_length: float) -> float:
        """计算翻转手势的置信度"""
        base_confidence = 75
        
        # 根据翻转类型加分（明确的翻转类型得分更高）
        if flip_type in ["palm_to_back", "back_to_palm"]:
            base_confidence += 15
        
        # 根据手保持张开的比例加分
        open_ratio = sum(open_states) / len(open_states)
        if open_ratio >= 0.95:
            base_confidence += 10
        elif open_ratio >= 0.85:
            base_confidence += 5
        
        # 根据位置稳定性加分（移动越小越好）
        movement_ratio = self._calculate_total_movement(positions) / palm_base_length
        if movement_ratio < 0.05:
            base_confidence += 10
        elif movement_ratio < 0.10:
            base_confidence += 5
        
        # 根据朝向变化的一致性加分
        orientation_consistency = self._calculate_orientation_consistency(orientations)
        if orientation_consistency > 0.8:
            base_confidence += 10
        elif orientation_consistency > 0.6:
            base_confidence += 5
        
        return min(100, base_confidence)
    
    def _calculate_orientation_smoothness(self, orientations: List[float]) -> float:
        """计算朝向变化的平滑性"""
        if len(orientations) < 3:
            return 1.0
        
        # 计算相邻角度差异的标准差
        angle_diffs = []
        for i in range(1, len(orientations)):
            diff = self._calculate_angle_difference(orientations[i-1], orientations[i])
            angle_diffs.append(abs(diff))
        
        if not angle_diffs:
            return 1.0
        
        # 平滑性 = 1 - (标准差 / 最大可能标准差)
        std_dev = float(np.std(angle_diffs))
        max_std = 90  # 假设最大标准差
        smoothness = max(0.0, 1.0 - (std_dev / max_std))
        
        return float(smoothness)
    
    def _calculate_orientation_consistency(self, orientations: List[str]) -> float:
        """计算朝向变化的一致性"""
        if len(orientations) < 3:
            return 1.0
        
        # 过滤掉不确定的朝向
        valid_orientations = [o for o in orientations if o != "uncertain"]
        if len(valid_orientations) < 3:
            return 0.5
        
        # 计算朝向变化的稳定性
        # 一致性高意味着翻转过程中朝向变化是渐进的，而不是跳跃的
        palm_count = valid_orientations.count("palm")
        back_count = valid_orientations.count("back")
        total_valid = len(valid_orientations)
        
        # 如果朝向很混乱（既不是明显的手心也不是明显的手背），一致性低
        if palm_count == 0 or back_count == 0:
            return 0.3  # 没有翻转
        
        # 计算朝向变化的渐进性
        # 理想情况下，应该是从一种朝向逐渐变为另一种朝向
        transition_quality = min(palm_count, back_count) / total_valid
        
        # 检查是否有明显的转换点
        has_transition = False
        for i in range(1, len(valid_orientations)):
            if valid_orientations[i] != valid_orientations[i-1]:
                has_transition = True
                break
        
        if not has_transition:
            return 0.2  # 没有朝向变化
        
        # 综合评分
        consistency = transition_quality * 0.7 + (0.3 if has_transition else 0)
        return min(1.0, consistency)
    
    def reset(self, hand_id: Optional[str] = None):
        """重置检测器状态"""
        if hand_id is None:
            self.history.clear()
        elif hand_id in self.history:
            self.history[hand_id] = {
                'palm_positions': deque(maxlen=self.history_length),
                'hand_orientations': deque(maxlen=self.history_length),
                'hand_open_states': deque(maxlen=self.history_length),
                'flip_detection_state': 'waiting',
                'initial_orientation': None,
                'flip_start_frame': 0
            }
    
    def get_display_message(self, gesture_result: Dict[str, Any]) -> str:
        """获取手掌翻转手势的显示消息"""
        hand_type = gesture_result['hand_type']
        details = gesture_result.get('details', {})
        flip_type = details.get('flip_type', 'unknown')
        flip_description = details.get('flip_description', 'unknown')
        movement_percent = details.get('movement_percent', 0)
        return f"{hand_type} Hand: {flip_description} ({movement_percent:.1f}%)"
