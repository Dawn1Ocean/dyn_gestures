"""
使用模块化架构的手势检测应用
"""

from cvzone.HandTrackingModule import HandDetector
import cv2
from gesture_manager import GestureManager
from hand_utils import HandUtils
import config


class HandGestureApp:
    """手势检测应用主类"""
    
    def __init__(self):
        # 初始化摄像头
        self.cap = cv2.VideoCapture(config.CAMERA_INDEX)
        
        # 初始化手部检测器
        self.detector = HandDetector(
            staticMode=config.HAND_DETECTION_CONFIG['static_mode'],
            maxHands=config.HAND_DETECTION_CONFIG['max_hands'],
            modelComplexity=config.HAND_DETECTION_CONFIG['model_complexity'],
            detectionCon=config.HAND_DETECTION_CONFIG['detection_confidence'],
            minTrackCon=config.HAND_DETECTION_CONFIG['min_tracking_confidence']
        )
        
        # 初始化手势管理器
        self.gesture_manager = GestureManager()
        
        # 显示状态
        self.gesture_message = ""
        self.gesture_timer = 0
        
        # 运行状态
        self.running = True
        
        # 静态手势输出控制 - 避免重复刷屏
        self.last_printed_gesture = None  # 记录上一次打印的任何手势 (gesture_key)
    
    def process_frame(self, img):
        """处理单帧图像"""
        # 左右翻转摄像头画面（如果配置启用）
        if config.DISPLAY_CONFIG['flip_image']:
            img = cv2.flip(img, 1)
        
        # 检测手部
        hands, img = self.detector.findHands(
            img, 
            draw=config.DISPLAY_CONFIG['show_landmarks'], 
            flipType=not config.DISPLAY_CONFIG['flip_image']
        )
        
        if hands:  
            for i, hand in enumerate(hands):
                hand_id = f"hand_{i}"
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
                else:
                    self.last_printed_gesture = None
                
                # 绘制手部信息
                self.draw_hand_info(img, hand, i)
        else:
            # 没有检测到手时，重置静态手势跟踪和检测历史
            self.last_printed_gesture = None
            self.gesture_manager.on_all_hands_lost()
        
        # 绘制手势消息
        if self.gesture_timer > 0:
            HandUtils.draw_gesture_message(img, self.gesture_message, config.COLORS['gesture_message'])
            self.gesture_timer -= 1
        
        return img
    
    def handle_gesture_result(self, gesture_result):
        """处理手势检测结果"""
        gesture_name = gesture_result['gesture']
        hand_type = gesture_result['hand_type']
        confidence = gesture_result.get('confidence', 0)
        
        # 使用检测器提供的显示消息
        self.gesture_message = gesture_result.get('display_message', f"{hand_type} Hand: {gesture_name}")
        self.gesture_timer = config.DISPLAY_CONFIG['gesture_message_duration']

        gesture_key = f"{hand_type}_{gesture_name}"
        message = f"检测到手势: {gesture_name}, 手部: {hand_type}, 置信度: {confidence:.1f}%"

        if self.last_printed_gesture == gesture_key and gesture_name in config.GESTURE_TYPES['static_gestures']:
            # 连续相同的静态手势，用 \r 覆盖
            print(f"\r{message}", end='', flush=True)
        else:
            print()
            print(message, end='', flush=True)

        self.last_printed_gesture = gesture_key
    
    def draw_hand_info(self, img, hand, hand_index):
        """绘制手部信息"""
        landmarks = hand["lmList"]
        hand_type = hand["type"]
        
        # 计算并绘制手掌中心
        palm_center = HandUtils.calculate_palm_center(landmarks)
        if config.DISPLAY_CONFIG['show_palm_center']:
            HandUtils.draw_palm_center(img, palm_center, config.COLORS['palm_center'])
        
        # 计算手指数量（使用cvzone的方法）
        fingers = self.detector.fingersUp(hand)
        finger_count = fingers.count(1)
        
        # 准备显示信息
        info_dict = {
            'Fingers': finger_count,
            'Palm': f'({palm_center[0]}, {palm_center[1]})'
        }
        
        # 绘制信息
        HandUtils.draw_text_info(
            img, hand_type, info_dict, 
            position_offset=hand_index * 120
        )
    
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
        
        # 检查是否显示摄像头窗口
        if not config.DISPLAY_CONFIG['show_camera_window']:
            print("摄像头画面显示已禁用，只进行后台手势检测")
        
        while self.running:
            # 读取帧
            success, img = self.cap.read()
            if not success:
                print("无法读取摄像头数据")
                continue
            
            # 处理帧
            img = self.process_frame(img)
            
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