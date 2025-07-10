"""
使用模块化架构的手势检测应用
"""

import cv2
import time

import config
from cvzone.HandTrackingModule import HandDetector
from gestures.manager import GestureManager
from connect.socket_client import initialize_client, disconnect_client
from display import Display
from camera_manager import CameraManager
from logger_config import setup_logger

# 设置日志
logger = setup_logger(__name__)


class HandGestureApp:
    """手势检测应用主类"""
    
    def __init__(self):
        # 初始化日志和异常处理
        self.logger = logger
        # 初始化各个管理器
        self.camera_manager = CameraManager()
        # 初始化手部检测器
        self.detector = None
        self.gesture_manager = None
        # Socket连接状态
        self.socket_initialized = False
        # 显示状态
        self.gesture_message = ""
        self.gesture_timer = 0
        # 运行状态
        self.running = True
        # 手势状态追踪
        self.previous_hands = {}  # {hand_id: hand_data}
        # FPS计算相关
        self.fps_time = time.time()
        self.fps_counter = 0
        self.fps_display = 0.0
        # FPS计算
        self.prev_time = time.time()
        self.fps = 0
    
    def initialize(self) -> bool:
        """初始化应用组件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info("正在初始化手势检测应用...")
            
            # 初始化摄像头
            if not self.camera_manager.initialize():
                self.logger.error("摄像头初始化失败")
                return False
            
            # 初始化手部检测器
            self.detector = HandDetector(
                maxHands=config.HAND_DETECTION_CONFIG['max_hands'],
                detectionCon=config.HAND_DETECTION_CONFIG['detection_confidence'],
                minTrackCon=config.HAND_DETECTION_CONFIG['min_tracking_confidence']
            )
            self.logger.info("手部检测器初始化完成")
            
            # 初始化手势管理器
            self.gesture_manager = GestureManager()
            self.logger.info("手势管理器初始化完成")
            
            # 初始化Socket客户端（如果启用）
            if config.DISPLAY_CONFIG.get('gesture_output', {}).get('enable_socket_output', True):
                self.socket_initialized = initialize_client(debug_mode=config.IS_DEBUG)
                if self.socket_initialized:
                    self.logger.info("Socket客户端初始化完成")
            
            self.logger.info("应用初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"应用初始化失败: {e}")
            return False
    
    def update_fps(self):
        """更新FPS计算"""
        self.fps_counter += 1
        current_time = time.time()
        
        # 每秒更新一次FPS显示
        if current_time - self.fps_time >= 1.0:
            self.fps_display = self.fps_counter / (current_time - self.fps_time)
            self.fps_counter = 0
            self.fps_time = current_time
        
        return self.fps_display
    
    def process_frame(self, img):
        """处理单帧图像"""        
        # 左右翻转摄像头画面（如果配置启用）
        if config.DISPLAY_CONFIG['flip_image']:
            img = cv2.flip(img, 1)
        
        # 检测手部
        if self.detector:
            hands, img = self.detector.findHands(
                img, 
                draw=config.DISPLAY_CONFIG['show_landmarks'], 
                flipType=config.DISPLAY_CONFIG['flip_image']
            )
        
            # 记录当前帧的手部ID
            current_hand_ids = set()
        
            if hands and self.gesture_manager is not None:
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
        
            if self.gesture_manager:
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
            
                # 绘制手势轨迹（在其他绘制之前）
                for detector in self.gesture_manager.get_all_tracker_detectors():
                    tracker = detector.get_trajectory_tracker()
                    trail_data = tracker.get_trail_data_for_drawing()
                    if trail_data and tracker.tracking_config.get('enable_tracking', True):
                            Display.draw_gesture_trails(
                            img, 
                            trail_data['trail_points'], 
                            trail_data['tracking_active'],
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
            Display.draw_fps(img, self.update_fps(), config.COLORS['fps_text'])
        
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
        self.logger.info("启动手势检测应用...")
        self.logger.info("按 'q' 键或关闭窗口退出")
        
        # 显示摄像头设置信息
        if self.camera_manager.cap:
            actual_fps = self.camera_manager.cap.get(cv2.CAP_PROP_FPS)
            self.logger.info(f"摄像头FPS设置: {config.CAMERA_FPS}, 实际FPS: {actual_fps:.1f}")
        
        # 检查是否显示摄像头窗口
        if not config.DISPLAY_CONFIG['show_camera_window']:
            self.logger.info("摄像头画面显示已禁用，只进行后台手势检测")
        
        if config.DISPLAY_CONFIG['show_fps']:
            self.logger.info("FPS显示已启用")
        
        while self.running:
            # 读取帧
            success, img = self.camera_manager.read_frame()
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
        self.logger.info("正在关闭应用...")
        
        # 释放摄像头
        self.camera_manager.release()
        
        # 断开Socket连接
        if self.socket_initialized:
            disconnect_client()
        
        # 只有在显示窗口时才需要销毁窗口
        if config.DISPLAY_CONFIG['show_camera_window']:
            cv2.destroyAllWindows()
        
        self.logger.info("应用已关闭")


def main():
    """主函数"""
    app = None
    try:
        app = HandGestureApp()
        
        # 初始化应用
        if not app.initialize():
            logger.error("应用初始化失败")
        
        # 运行应用
        app.run()
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序出错: {e}")
    finally:
        if app:
            app.cleanup()


if __name__ == "__main__":
    main()