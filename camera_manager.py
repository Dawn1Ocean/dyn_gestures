"""
相机管理器 - 负责摄像头的初始化和管理
"""

import cv2
import config
from logger_config import setup_logger

logger = setup_logger(__name__)

class CameraManager:
    """摄像头管理器"""
    
    def __init__(self):
        self.cap = None
        self.is_initialized = False
    
    def initialize(self) -> bool:
        """初始化摄像头
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info(f"正在初始化摄像头 (索引: {config.CAMERA_INDEX})")
            
            self.cap = cv2.VideoCapture(config.CAMERA_INDEX)
            
            if not self.cap.isOpened():
                logger.error(f"无法打开摄像头 (索引: {config.CAMERA_INDEX})")
                return False
            
            # 设置摄像头参数
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_FRAME_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
            
            # 验证设置
            actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"摄像头参数设置完成:")
            logger.info(f"  分辨率: {actual_width}x{actual_height} (设定: {config.CAMERA_FRAME_WIDTH}x{config.CAMERA_FRAME_HEIGHT})")
            logger.info(f"  帧率: {actual_fps:.1f} (设定: {config.CAMERA_FPS})")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"摄像头初始化失败: {e}")
            return False
    
    def read_frame(self):
        """读取一帧图像
        
        Returns:
            tuple: (成功标志, 图像数据)
        """
        if not self.is_initialized or self.cap is None:
            logger.error("摄像头未初始化")
            return False, None
        
        try:
            success, img = self.cap.read()
            if not success:
                logger.warning("无法读取摄像头数据")
            return success, img
        except Exception as e:
            logger.error(f"读取摄像头帧时出错: {e}")
            return False, None
    
    def release(self):
        """释放摄像头资源"""
        if self.cap is not None:
            logger.info("正在释放摄像头资源")
            self.cap.release()
            self.cap = None
            self.is_initialized = False
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        self.release()
