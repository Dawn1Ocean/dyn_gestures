import socket
import threading
import time
import atexit
from typing import Optional, Union

import config


class SocketClient:
    """Socket客户端管理器 - 支持持久连接和自动重连"""
    
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.host: str = config.SOCKET_HOST
        self.port: int = config.SOCKET_PORT
        self.is_connected: bool = False
        self.is_enabled: bool = False
        self.connection_lock = threading.Lock()
        self.reconnect_attempts: int = 0
        self.max_reconnect_attempts: int = 3
        self.reconnect_delay: float = 1.0
        self.debug_mode: bool = False
        self.silent_mode: bool = True
        
        # 注册程序退出时的清理函数
        atexit.register(self.disconnect)
    
    def initialize(self, host: Optional[str] = None, port: Optional[int] = None, debug_mode: bool = False, silent_mode: bool = True) -> bool:
        """
        初始化Socket连接
        
        :param host: 服务器主机地址
        :param port: 服务器端口
        :param debug_mode: 是否启用调试模式
        :param silent_mode: 是否启用静默模式
        :return: 是否初始化成功
        """
        # 检查配置中是否启用了Socket输出
        socket_enabled = config.DISPLAY_CONFIG.get('gesture_output', {}).get('enable_socket_output', False)
        if not socket_enabled:
            if not silent_mode:
                print("[SOCKET] Socket输出未启用，跳过初始化")
            return False
        
        self.host = host or config.SOCKET_HOST
        self.port = port or config.SOCKET_PORT
        self.debug_mode = debug_mode
        self.silent_mode = silent_mode
        
        if self.debug_mode:
            print(f"[SOCKET] 初始化Socket客户端，目标服务器: {self.host}:{self.port}")
        
        success = self._connect()
        if success:
            self.is_enabled = True
            if not self.silent_mode:
                print(f"[SOCKET] Socket客户端初始化成功")
        else:
            if not self.silent_mode:
                print(f"[SOCKET] Socket客户端初始化失败")
        
        return success
    
    def _connect(self) -> bool:
        """建立Socket连接"""
        try:
            with self.connection_lock:
                if self.is_connected:
                    return True
                
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5.0)  # 设置连接超时
                
                if self.debug_mode:
                    print(f"[SOCKET] 正在连接到服务器 {self.host}:{self.port}...")
                
                self.socket.connect((self.host, self.port))
                self.is_connected = True
                self.reconnect_attempts = 0
                
                if self.debug_mode:
                    print(f"[SOCKET] 连接成功！")
                
                return True
                
        except ConnectionRefusedError:
            if not self.silent_mode:
                print(f"[SOCKET] 连接被拒绝，请确保服务器程序 ({self.host}:{self.port}) 正在运行")
            return False
        except Exception as e:
            if not self.silent_mode:
                print(f"[SOCKET] 连接失败: {e}")
            return False
    
    def send_message(self, message: str) -> Optional[str]:
        """
        发送消息到服务器
        
        :param message: 要发送的消息
        :return: 服务器响应，如果失败则返回None
        """
        if not self.is_enabled or not self.socket:
            return None
        
        try:
            with self.connection_lock:
                # 检查连接状态
                if not self.is_connected:
                    if not self._reconnect():
                        return None
                
                # 确保socket对象存在
                if not self.socket:
                    return None
                
                # 发送消息
                if self.debug_mode:
                    print(f"[SOCKET] 发送消息: '{message}'")
                
                self.socket.sendall(message.encode('utf-8'))
                
                # 接收响应
                data = self.socket.recv(1024)
                response = data.decode('utf-8')
                
                if self.debug_mode:
                    print(f"[SOCKET] 收到响应: '{response}'")
                
                return response
                
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            if self.debug_mode:
                print("[SOCKET] 连接已断开，尝试重连...")
            self.is_connected = False
            return self._retry_send(message)
        except Exception as e:
            if not self.silent_mode:
                print(f"[SOCKET] 发送消息失败: {e}")
            return None
    
    def _reconnect(self) -> bool:
        """重新连接到服务器"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            if self.debug_mode:
                print(f"[SOCKET] 达到最大重连次数 ({self.max_reconnect_attempts})，放弃重连")
            return False
        
        self.reconnect_attempts += 1
        if self.debug_mode:
            print(f"[SOCKET] 尝试重连 ({self.reconnect_attempts}/{self.max_reconnect_attempts})...")
        
        time.sleep(self.reconnect_delay)
        return self._connect()
    
    def _retry_send(self, message: str) -> Optional[str]:
        """重试发送消息"""
        if self._reconnect():
            return self.send_message(message)
        return None
    
    def disconnect(self):
        """断开Socket连接"""
        try:
            with self.connection_lock:
                if self.socket and self.is_connected:
                    if self.debug_mode:
                        print("[SOCKET] 正在断开连接...")
                    self.socket.close()
                    self.is_connected = False
                    if not self.silent_mode:
                        print("[SOCKET] 连接已断开")
        except Exception as e:
            if self.debug_mode:
                print(f"[SOCKET] 断开连接时发生错误: {e}")
        finally:
            self.socket = None
            self.is_enabled = False
    
    def get_status(self) -> dict:
        """获取连接状态"""
        return {
            'enabled': self.is_enabled,
            'connected': self.is_connected,
            'host': self.host,
            'port': self.port,
            'reconnect_attempts': self.reconnect_attempts
        }


# 全局Socket客户端实例
_socket_client: Optional[SocketClient] = None


def initialize_socket_client(host: Optional[str] = None, port: Optional[int] = None, debug_mode: bool = False, silent_mode: bool = True) -> bool:
    """
    初始化全局Socket客户端
    
    :param host: 服务器主机地址
    :param port: 服务器端口
    :param debug_mode: 是否启用调试模式
    :param silent_mode: 是否启用静默模式
    :return: 是否初始化成功
    """
    global _socket_client
    if _socket_client is None:
        _socket_client = SocketClient()
    
    return _socket_client.initialize(host, port, debug_mode, silent_mode)


def send_message_to_server(message: str, host: Optional[str] = None, port: Optional[int] = None, isdev: bool = False, silent: bool = False) -> Optional[str]:
    """
    发送消息到服务器（兼容旧接口）
    
    :param message: 要发送的消息
    :param host: 服务器主机地址（如果未初始化则使用此参数）
    :param port: 服务器端口（如果未初始化则使用此参数）
    :param isdev: 开发模式（兼容参数）
    :param silent: 静默模式（兼容参数）
    :return: 服务器响应
    """
    global _socket_client
    
    # 如果客户端未初始化，尝试初始化
    if _socket_client is None or not _socket_client.is_enabled:
        if not initialize_socket_client(host, port, isdev, silent):
            return None
    
    if _socket_client:
        return _socket_client.send_message(message)
    return None


def disconnect_socket_client():
    """断开Socket客户端连接"""
    global _socket_client
    if _socket_client:
        _socket_client.disconnect()


def get_socket_client_status() -> dict:
    """获取Socket客户端状态"""
    global _socket_client
    if _socket_client:
        return _socket_client.get_status()
    return {'enabled': False, 'connected': False}


# --- 如何使用 ---
if __name__ == "__main__":
    # 初始化Socket客户端
    print("--- 初始化Socket客户端 ---")
    if initialize_socket_client(debug_mode=True, silent_mode=False):
        print("初始化成功")
        
        # 发送多条消息
        print("\n--- 发送消息测试 ---")
        send_message_to_server("你好，服务器！我是客户端。")
        send_message_to_server("这是我的第二条消息。")
        send_message_to_server("这是我的第三条消息。")
        
        # 显示状态
        print(f"\n--- 连接状态 ---")
        print(get_socket_client_status())
        
        # 断开连接
        print("\n--- 断开连接 ---")
        disconnect_socket_client()
    else:
        print("初始化失败")