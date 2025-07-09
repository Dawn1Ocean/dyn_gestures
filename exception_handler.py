"""
异常处理器 - 统一处理应用异常
"""

import traceback
from typing import Optional, Callable, Any
from logger_config import setup_logger

logger = setup_logger(__name__)

class ExceptionHandler:
    """异常处理器"""
    
    def __init__(self):
        self.error_callbacks = {}
    
    def register_error_callback(self, error_type: type, callback: Callable):
        """注册错误回调函数
        
        Args:
            error_type: 错误类型
            callback: 回调函数
        """
        self.error_callbacks[error_type] = callback
    
    def handle_exception(self, error: Exception, context: str = "") -> bool:
        """处理异常
        
        Args:
            error: 异常对象
            context: 异常上下文信息
            
        Returns:
            bool: 是否可以恢复
        """
        error_type = type(error)
        error_msg = f"异常发生在 {context}: {str(error)}"
        
        logger.error(error_msg)
        logger.debug(f"异常详情:\n{traceback.format_exc()}")
        
        # 检查是否有注册的错误回调
        if error_type in self.error_callbacks:
            try:
                return self.error_callbacks[error_type](error, context)
            except Exception as callback_error:
                logger.error(f"错误回调函数执行失败: {callback_error}")
        
        # 默认错误处理策略
        return self._default_error_handling(error, context)
    
    def _default_error_handling(self, error: Exception, context: str) -> bool:
        """默认错误处理策略
        
        Args:
            error: 异常对象
            context: 异常上下文
            
        Returns:
            bool: 是否可以恢复
        """
        # 对于一些常见错误，尝试恢复
        if isinstance(error, (ConnectionError, OSError)):
            logger.warning(f"检测到连接错误，尝试恢复: {error}")
            return True
        
        if isinstance(error, ValueError):
            logger.warning(f"检测到数值错误，跳过当前操作: {error}")
            return True
        
        # 对于严重错误，不尝试恢复
        if isinstance(error, (MemoryError, SystemError)):
            logger.critical(f"检测到严重错误，应用可能需要重启: {error}")
            return False
        
        # 其他错误默认尝试恢复
        return True
