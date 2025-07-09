"""
使用模块化架构的手势检测应用
"""

import cv2
import time

import config
from cvzone.HandTrackingModule import HandDetector
from gesture_manager import GestureManager
from hand_utils import HandUtils
from socket_client import initialize_socket_client, disconnect_socket_client
from display import Display


class HandGestureApp:
    """手势检测应用主类"""
    
    def __init__(self):
        # 初始化摄像头
        self.cap = cv2.VideoCapture(config.CAMERA_INDEX)
        # 设置摄像头分辨率
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_FRAME_HEIGHT)
        
        # 设置摄像头FPS
        self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
        
        # 初始化手部检测器
        self.detector = HandDetector(
            maxHands=config.HAND_DETECTION_CONFIG['max_hands'],
            detectionCon=config.HAND_DETECTION_CONFIG['detection_confidence'],
            minTrackCon=config.HAND_DETECTION_CONFIG['min_tracking_confidence']
        )
        
        # 初始化手势管理器
        self.gesture_manager = GestureManager()
        
        # 初始化Socket客户端（如果启用）
        if config.DISPLAY_CONFIG.get('gesture_output', {}).get('enable_socket_output', True):
            self.socket_initialized = initialize_socket_client(debug_mode=config.IS_DEBUG)

        # 显示状态
        self.gesture_message = ""
        self.gesture_timer = 0
        
        # 运行状态
        self.running = True
        
        # FPS计算相关
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0
        self.fps_update_interval = config.DISPLAY_CONFIG['fps_update_interval']
        
        # 手势状态追踪
        self.previous_hands = {}  # {hand_id: hand_data}
    
    def update_fps(self):
        """更新FPS计算"""
        self.fps_counter += 1
        
        if self.fps_counter >= self.fps_update_interval:
            current_time = time.time()
            elapsed_time = current_time - self.fps_start_time
            
            if elapsed_time > 0:
                self.current_fps = self.fps_counter / elapsed_time
            
            # 重置计数器
            self.fps_counter = 0
            self.fps_start_time = current_time
    
    def process_frame(self, img):
        """处理单帧图像"""
        # 更新FPS计算
        self.update_fps()
        
        # 左右翻转摄像头画面（如果配置启用）
        if config.DISPLAY_CONFIG['flip_image']:
            img = cv2.flip(img, 1)
        
        # 检测手部
        hands, img = self.detector.findHands(
            img, 
            draw=config.DISPLAY_CONFIG['show_landmarks'], 
            flipType=config.DISPLAY_CONFIG['flip_image']
        )
        
        # 记录当前帧的手部ID
        current_hand_ids = set()
        
        if hands:
            for i, hand in enumerate(hands):
                hand_id = f"hand_{i}"
                current_hand_ids.add(hand_id)
                landmarks = hand["lmList"]
                hand_type = hand["type"]
                
                # 使用手势管理器检测手势
                detected_gestures = self.gesture_manager.detect_gestures(
                    landmarks, hand_id, hand_type
                )

                if detected_gestures:
                    # 处理检测到的手势
                    for gesture in detected_gestures:
                        self.handle_gesture_result(gesture)
                
                # 绘制手部信息
                Display.draw_hand_info(img, hand, i, self.detector)

                # 更新手部记录
                self.previous_hands[hand_id] = {
                    'landmarks': landmarks,
                    'hand_type': hand_type
                }
        
        # 检测丢失的手部
        lost_hand_ids = set(self.previous_hands.keys()) - current_hand_ids
        for lost_hand_id in lost_hand_ids:
            self.gesture_manager.on_hand_lost(lost_hand_id)
            del self.previous_hands[lost_hand_id]
        
        # 如果没有检测到任何手
        if not hands:
            # 清空所有手部记录
            if self.previous_hands:
                self.gesture_manager.on_all_hands_lost()
                self.previous_hands.clear()
        
        # 绘制握拳轨迹（在其他绘制之前）
        hand_close_detector = self.gesture_manager.get_detector_by_name("HandClose")
        if hand_close_detector and hasattr(hand_close_detector, 'get_trail_data_for_drawing'):
            # 类型转换确保能访问方法
            from gestures.dynamic.hand_close import HandCloseDetector
            if isinstance(hand_close_detector, HandCloseDetector):
                trail_data = hand_close_detector.get_trail_data_for_drawing()
                if trail_data and hand_close_detector.tracking_config.get('enable_tracking', True):
                    HandUtils.draw_fist_trails(
                        img, 
                        trail_data['trail_points'], 
                        trail_data['fist_active'],
                        config.COLORS['fist_trail'],
                        config.COLORS['fist_center'],
                        trail_data['trail_thickness']
                    )
        
        # 绘制手势消息
        if self.gesture_timer > 0:
            Display.draw_gesture_message(img, self.gesture_message, config.COLORS['gesture_message'])
            self.gesture_timer -= 1
        
        # 绘制FPS（如果配置启用）
        if config.DISPLAY_CONFIG['show_fps']:
            Display.draw_fps(img, self.current_fps, config.COLORS['fps_text'])
        
        return img
    
    def handle_gesture_result(self, gesture_result):
        """处理手势检测结果"""
        gesture_name = gesture_result['gesture']
        hand_type = gesture_result['hand_type']
        
        # 使用检测器提供的显示消息
        self.gesture_message = gesture_result.get('display_message', f"{hand_type} Hand: {gesture_name}")
        self.gesture_timer = config.DISPLAY_CONFIG['gesture_message_duration']
    
    def handle_window_events(self):
        """处理窗口事件"""
        key = cv2.waitKey(1) & 0xFF
        
        # 按 'q' 退出
        if key == ord('q'):
            self.running = False
            return
        
        # 检查窗口是否被关闭
        try:
            if cv2.getWindowProperty(config.DISPLAY_CONFIG['window_name'], cv2.WND_PROP_VISIBLE) < 1:
                self.running = False
        except cv2.error:
            self.running = False
    
    def run(self):
        """运行主循环"""
        print("启动手势检测应用...")
        print("按 'q' 键或关闭窗口退出")
        
        # 显示摄像头设置信息
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"摄像头FPS设置: {config.CAMERA_FPS}, 实际FPS: {actual_fps:.1f}")
        
        # 检查是否显示摄像头窗口
        if not config.DISPLAY_CONFIG['show_camera_window']:
            print("摄像头画面显示已禁用，只进行后台手势检测")
        
        if config.DISPLAY_CONFIG['show_fps']:
            print("FPS显示已启用")
        
        while self.running:
            # 读取帧
            success, img = self.cap.read()
            if not success:
                print("无法读取摄像头数据")
                continue
            
            # 处理帧
            img = self.process_frame(img)
            
            # 更新FPS
            self.update_fps()
            
            # 显示图像（如果配置启用）
            if config.DISPLAY_CONFIG['show_camera_window']:
                cv2.imshow(config.DISPLAY_CONFIG['window_name'], img)
                # 处理窗口事件
                self.handle_window_events()
            else:
                # 不显示窗口时，只检查键盘输入
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.running = False
        
        self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        print("\n正在关闭应用...")
        self.cap.release()
        
        # 断开Socket连接
        if self.socket_initialized:
            disconnect_socket_client()
        
        # 只有在显示窗口时才需要销毁窗口
        if config.DISPLAY_CONFIG['show_camera_window']:
            cv2.destroyAllWindows()
        
        print("应用已关闭")


def main():
    """主函数"""
    try:
        app = HandGestureApp()
        app.run()
    except KeyboardInterrupt:
        print("\n用户中断程序")
    except Exception as e:
        print(f"程序出错: {e}")


if __name__ == "__main__":
    main()