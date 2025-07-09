"""
性能监控器 - 监控应用性能指标
"""

import time
import threading
from typing import Dict, Any, Optional
from logger_config import setup_logger

logger = setup_logger(__name__)

# 尝试导入psutil，如果不可用则提供降级功能
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False
    logger.warning("psutil不可用，系统资源监控功能将被禁用")

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, fps_update_interval: int = 10):
        self.fps_update_interval = fps_update_interval
        self.reset_fps_counter()
        
        # 性能指标
        self.metrics = {
            'current_fps': 0.0,
            'avg_fps': 0.0,
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'frame_count': 0
        }
        
        # 系统监控线程
        self.monitoring = False
        self.monitor_thread = None
        
    def reset_fps_counter(self):
        """重置FPS计数器"""
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.total_frames = 0
        self.app_start_time = time.time()
    
    def update_fps(self) -> bool:
        """更新FPS计算
        
        Returns:
            bool: 是否更新了FPS值
        """
        self.fps_counter += 1
        self.total_frames += 1
        self.metrics['frame_count'] = self.total_frames
        
        if self.fps_counter >= self.fps_update_interval:
            current_time = time.time()
            elapsed_time = current_time - self.fps_start_time
            
            if elapsed_time > 0:
                self.metrics['current_fps'] = self.fps_counter / elapsed_time
                
                # 计算平均FPS
                total_elapsed = current_time - self.app_start_time
                if total_elapsed > 0:
                    self.metrics['avg_fps'] = self.total_frames / total_elapsed
            
            # 重置计数器
            self.fps_counter = 0
            self.fps_start_time = current_time
            return True
        
        return False
    
    def start_system_monitoring(self, interval: float = 1.0):
        """开始系统资源监控
        
        Args:
            interval: 监控间隔（秒）
        """
        if self.monitoring or not PSUTIL_AVAILABLE:
            if not PSUTIL_AVAILABLE:
                logger.warning("psutil不可用，无法启动系统资源监控")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_system_resources,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("已启动系统资源监控")
    
    def stop_system_monitoring(self):
        """停止系统资源监控"""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
        logger.info("已停止系统资源监控")
    
    def _monitor_system_resources(self, interval: float):
        """监控系统资源（在后台线程中运行）"""
        while self.monitoring:
            try:
                if PSUTIL_AVAILABLE and psutil is not None:
                    # CPU使用率
                    self.metrics['cpu_usage'] = psutil.cpu_percent(interval=0.1)
                    
                    # 内存使用率
                    memory = psutil.virtual_memory()
                    self.metrics['memory_usage'] = memory.percent
                else:
                    # 降级模式，不提供系统资源信息
                    self.metrics['cpu_usage'] = 0.0
                    self.metrics['memory_usage'] = 0.0
                
                time.sleep(interval)
                
            except Exception as e:
                logger.warning(f"系统资源监控出错: {e}")
                time.sleep(interval)
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取当前性能指标
        
        Returns:
            Dict: 性能指标字典
        """
        return self.metrics.copy()
    
    def log_performance_summary(self):
        """记录性能摘要"""
        metrics = self.get_metrics()
        total_time = time.time() - self.app_start_time
        
        logger.info("=== 性能摘要 ===")
        logger.info(f"运行时间: {total_time:.2f}秒")
        logger.info(f"总处理帧数: {metrics['frame_count']}")
        logger.info(f"平均FPS: {metrics['avg_fps']:.2f}")
        logger.info(f"当前FPS: {metrics['current_fps']:.2f}")
        logger.info(f"CPU使用率: {metrics['cpu_usage']:.1f}%")
        logger.info(f"内存使用率: {metrics['memory_usage']:.1f}%")
    
    def __del__(self):
        """析构函数"""
        self.stop_system_monitoring()
