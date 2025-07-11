"""
摄像头管理器 - 支持本地和远程IP摄像头
"""

import cv2
import urllib.request
import numpy as np
import config
from logger_config import setup_logger

logger = setup_logger(__name__)

class CameraManager:
    """摄像头管理器，支持本地和远程摄像头"""
    
    def __init__(self, use_ip_camera=False, ip_camera_url=None):
        """
        初始化摄像头管理器
        Args:
            use_ip_camera: 是否使用IP摄像头
            ip_camera_url: IP摄像头的URL (例如: "http://192.168.1.100:8080")
        """
        self.cap = None
        self.use_ip_camera = use_ip_camera
        self.ip_camera_url = ip_camera_url
        self.is_initialized = False
        
        # IP摄像头相关
        self.stream = None
    
    def initialize(self) -> bool:
        """初始化摄像头"""
        try:
            if self.use_ip_camera and self.ip_camera_url:
                return self._initialize_ip_camera()
            else:
                return self._initialize_local_camera()
        except Exception as e:
            logger.error(f"摄像头初始化失败: {e}")
            return False
    
    def _initialize_local_camera(self) -> bool:
        """初始化本地摄像头"""
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
            logger.info("本地摄像头初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"本地摄像头初始化失败: {e}")
            return False
    
    def _initialize_ip_camera(self) -> bool:
        """初始化IP摄像头"""
        try:
            # 测试连接
            test_url = f"{self.ip_camera_url}/shot.jpg"
            response = urllib.request.urlopen(test_url, timeout=5)
            if response.getcode() == 200:
                self.is_initialized = True
                logger.info(f"IP摄像头连接成功: {self.ip_camera_url}")
                return True
            else:
                logger.error(f"IP摄像头连接失败，状态码: {response.getcode()}")
                return False
                
        except Exception as e:
            logger.error(f"IP摄像头初始化失败: {e}")
            logger.error("请检查:")
            logger.error("1. 小米平板上的IP Webcam应用是否已启动")
            logger.error("2. IP地址和端口是否正确")
            logger.error("3. PC和平板是否在同一WiFi网络中")
            return False
    
    def read_frame(self):
        """读取摄像头帧"""
        if not self.is_initialized:
            logger.error("摄像头未初始化")
            return False, None
            
        try:
            if self.use_ip_camera:
                return self._read_ip_frame()
            else:
                return self._read_local_frame()
        except Exception as e:
            logger.error(f"读取摄像头帧失败: {e}")
            return False, None
    
    def _read_local_frame(self):
        """读取本地摄像头帧"""
        if self.cap is None:
            return False, None
        return self.cap.read()
    
    def _read_ip_frame(self):
        """读取IP摄像头帧"""
        try:
            # 从IP摄像头获取图像
            img_url = f"{self.ip_camera_url}/shot.jpg"
            img_resp = urllib.request.urlopen(img_url, timeout=1)
            img_np = np.array(bytearray(img_resp.read()), dtype=np.uint8)
            img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
            
            if img is not None:
                # 调整图像大小以匹配配置
                img = cv2.resize(img, (config.CAMERA_FRAME_WIDTH, config.CAMERA_FRAME_HEIGHT))
                return True, img
            else:
                return False, None
                
        except Exception as e:
            logger.error(f"读取IP摄像头帧失败: {e}")
            return False, None
    
    def release(self):
        """释放摄像头资源"""
        if self.cap is not None:
            logger.info("正在释放摄像头资源")
            self.cap.release()
            self.cap = None
        
        if self.stream is not None:
            self.stream = None
            
        self.is_initialized = False
        logger.info("摄像头资源已释放")
    
    def get_camera_info(self):
        """获取摄像头信息"""
        if not self.is_initialized:
            return "摄像头未初始化"
        
        if self.use_ip_camera:
            return f"IP摄像头: {self.ip_camera_url}"
        else:
            return f"本地摄像头: 索引{config.CAMERA_INDEX}"
