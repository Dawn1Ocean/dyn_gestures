import socket
import threading
import time
import atexit
from typing import Optional
from abc import ABC, abstractmethod

# 注意：使用蓝牙功能可能需要安装额外的库
# 在某些系统上，需要安装 PyBluez 或类似库：pip install pybluez
# 如果遇到蓝牙相关的导入错误，请参考系统对应的蓝牙库文档

import config


class BaseClient(ABC):
    """客户端管理器基类 - 定义共同接口"""
    
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.is_connected: bool = False
        self.is_enabled: bool = False
        self.connection_lock = threading.Lock()
        self.reconnect_attempts: int = 0
        self.max_reconnect_attempts: int = 3
        self.reconnect_delay: float = 1.0
        self.debug_mode: bool = False
        
        # 注册程序退出时的清理函数
        atexit.register(self.disconnect)
    
    @abstractmethod
    def initialize(self, host: Optional[str] = None, port: Optional[int] = None, debug_mode: bool = False, **kwargs) -> bool:
        pass
    
    @abstractmethod
    def _connect(self) -> bool:
        pass
    
    @abstractmethod
    def send_message(self, message: str) -> Optional[str]:
        pass
    
    @abstractmethod
    def _reconnect(self) -> bool:
        pass
    
    @abstractmethod
    def _retry_send(self, message: str) -> Optional[str]:
        pass
    
    @abstractmethod
    def disconnect(self):
        pass
    
    @abstractmethod
    def get_status(self) -> dict:
        pass


class SocketClient(BaseClient):
    """Socket客户端管理器 - 支持持久连接和自动重连"""
    
    def __init__(self):
        super().__init__()
        self.host: str = config.SOCKET_HOST
        self.port: int = config.SOCKET_PORT
    
    def initialize(self, host: Optional[str] = None, port: Optional[int] = None, debug_mode: bool = False, **kwargs) -> bool:
        """
        初始化Socket连接
        
        :param host: 服务器主机地址
        :param port: 服务器端口
        :param debug_mode: 是否启用调试模式
        :param kwargs: 额外参数
        :return: 是否初始化成功
        """
        # 检查配置中是否启用了Socket输出
        socket_enabled = config.DISPLAY_CONFIG.get('gesture_output', {}).get('enable_socket_output', False)
        if not socket_enabled:
            print("[SOCKET] Socket输出未启用，跳过初始化")
            return False
        
        self.host = host or config.SOCKET_HOST
        self.port = port or config.SOCKET_PORT
        self.debug_mode = debug_mode
        
        if self.debug_mode:
            print(f"[SOCKET] 初始化Socket客户端，目标服务器: {self.host}:{self.port}")
        
        success = self._connect()
        if success:
            self.is_enabled = True
            print(f"[SOCKET] Socket客户端初始化成功")
        else:
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
            print(f"[SOCKET] 连接被拒绝，请确保服务器程序 ({self.host}:{self.port}) 正在运行")
            return False
        except Exception as e:
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


class BluetoothClient(BaseClient):
    """蓝牙客户端管理器 - 支持持久连接和自动重连"""
    
    def __init__(self):
        super().__init__()
        self.server_mac: str = config.BLUETOOTH_MAC
        self.port: int = config.BLUETOOTH_PORT
    
    def initialize(self, host: Optional[str] = None, port: Optional[int] = None, debug_mode: bool = False, **kwargs) -> bool:
        """
        初始化蓝牙连接
        
        :param host: 服务器蓝牙MAC地址
        :param port: RFCOMM端口
        :param debug_mode: 是否启用调试模式
        :return: 是否初始化成功
        """
        # 检查配置中是否启用了蓝牙输出
        bluetooth_enabled = config.CONNECTION_TYPE == 'bluetooth'
        if not bluetooth_enabled:
            print("[蓝牙] 蓝牙连接未启用，跳过初始化")
            return False
        
        self.server_mac = host or config.BLUETOOTH_MAC
        self.port = port or config.BLUETOOTH_PORT
        self.debug_mode = debug_mode
        
        if self.debug_mode:
            print(f"[蓝牙] 初始化蓝牙客户端，目标设备: {self.server_mac}:{self.port}")
        
        success = self._connect()
        if success:
            self.is_enabled = True
            print(f"[蓝牙] 蓝牙客户端初始化成功")
        else:
            print(f"[蓝牙] 蓝牙客户端初始化失败")
        
        return success
    
    def _connect(self) -> bool:
        """建立蓝牙连接"""
        try:
            with self.connection_lock:
                if self.is_connected:
                    return True
                
                # 尝试创建蓝牙socket
                try:
                    # 如果系统支持蓝牙库，这些常量应该存在
                    self.socket = socket.socket(
                        socket.AF_BLUETOOTH, 
                        socket.SOCK_STREAM, 
                        socket.BTPROTO_RFCOMM
                    )
                except AttributeError:
                    print("[蓝牙] 错误：系统不支持蓝牙socket连接。请安装蓝牙库，例如：pip install pybluez")
                    print("[蓝牙] 或者检查socket模块是否支持AF_BLUETOOTH和BTPROTO_RFCOMM")
                    return False
                self.socket.settimeout(5.0)  # 设置连接超时
                
                if self.debug_mode:
                    print(f"[蓝牙] 正在连接到设备 {self.server_mac} 的 RFCOMM 端口 {self.port}...")
                
                self.socket.connect((self.server_mac, self.port))
                self.is_connected = True
                self.reconnect_attempts = 0
                
                if self.debug_mode:
                    print(f"[蓝牙] 连接成功！")
                
                return True
                
        except ConnectionRefusedError:
            print(f"[蓝牙] 连接被拒绝，请确保服务器程序在设备 {self.server_mac} 上运行")
            return False
        except Exception as e:
            print(f"[蓝牙] 连接失败: {e}")
            return False
    
    def send_message(self, message: str) -> Optional[str]:
        """
        发送消息到蓝牙服务器
        
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
                    print(f"[蓝牙] 发送消息: '{message}'")
                
                self.socket.sendall(message.encode('utf-8'))
                
                # 接收响应
                data = self.socket.recv(1024)
                response = data.decode('utf-8')
                
                if self.debug_mode:
                    print(f"[蓝牙] 收到响应: '{response}'")
                
                return response
                
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            if self.debug_mode:
                print("[蓝牙] 连接已断开，尝试重连...")
            self.is_connected = False
            return self._retry_send(message)
        except Exception as e:
            print(f"[蓝牙] 发送消息失败: {e}")
            return None
    
    def _reconnect(self) -> bool:
        """重新连接到蓝牙服务器"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            if self.debug_mode:
                print(f"[蓝牙] 达到最大重连次数 ({self.max_reconnect_attempts})，放弃重连")
            return False
        
        self.reconnect_attempts += 1
        if self.debug_mode:
            print(f"[蓝牙] 尝试重连 ({self.reconnect_attempts}/{self.max_reconnect_attempts})...")
        
        time.sleep(self.reconnect_delay)
        return self._connect()
    
    def _retry_send(self, message: str) -> Optional[str]:
        """重试发送消息"""
        if self._reconnect():
            return self.send_message(message)
        return None
    
    def disconnect(self):
        """断开蓝牙连接"""
        try:
            with self.connection_lock:
                if self.socket and self.is_connected:
                    if self.debug_mode:
                        print("[蓝牙] 正在断开连接...")
                    self.socket.close()
                    self.is_connected = False
                    print("[蓝牙] 连接已断开")
        except Exception as e:
            if self.debug_mode:
                print(f"[蓝牙] 断开连接时发生错误: {e}")
        finally:
            self.socket = None
            self.is_enabled = False
    
    def get_status(self) -> dict:
        """获取连接状态"""
        return {
            'enabled': self.is_enabled,
            'connected': self.is_connected,
            'server_mac': self.server_mac,
            'port': self.port,
            'reconnect_attempts': self.reconnect_attempts
        }


# 全局客户端实例
_client: Optional[BaseClient] = None


def initialize_client(host: Optional[str] = None, port: Optional[int] = None, debug_mode: bool = False) -> bool:
    """
    根据配置初始化合适的客户端（Socket或蓝牙）
    
    :param host: 服务器地址（IP地址或MAC地址）
    :param port: 服务器端口
    :param debug_mode: 是否启用调试模式
    :return: 是否初始化成功
    """
    global _client
    
    # 根据配置决定使用哪种客户端
    print(config.CONNECTION_TYPE.lower())
    connection_type = config.CONNECTION_TYPE.lower()
    
    if _client is not None:
        # 如果已有客户端且类型匹配，直接使用现有客户端
        if (connection_type == 'socket' and isinstance(_client, SocketClient)) or \
           (connection_type == 'bluetooth' and isinstance(_client, BluetoothClient)):
            return _client.initialize(host=host, port=port, debug_mode=debug_mode)
        
        # 如果类型不匹配，断开现有连接
        _client.disconnect()
        _client = None
    
    # 创建新的客户端实例
    if connection_type == 'bluetooth':
        print(f"[通信] 使用蓝牙连接模式")
        _client = BluetoothClient()
    else:  # 默认使用socket
        print(f"[通信] 使用Socket连接模式")
        _client = SocketClient()
    
    return _client.initialize(host=host, port=port, debug_mode=debug_mode)


def send_message(message: str, host: Optional[str] = None, port: Optional[int] = None, debug_mode: bool = False) -> Optional[str]:
    """
    发送消息到服务器（Socket或蓝牙）
    
    :param message: 要发送的消息
    :param host: 服务器地址（如果未初始化则使用此参数）
    :param port: 服务器端口（如果未初始化则使用此参数）
    :param debug_mode: 是否启用调试模式
    :return: 服务器响应
    """
    global _client
    
    # 如果客户端未初始化，尝试初始化
    if _client is None or not _client.is_enabled:
        if not initialize_client(host=host, port=port, debug_mode=debug_mode):
            return None
    
    if _client:
        return _client.send_message(message)
    return None


def disconnect_client():
    """断开客户端连接"""
    global _client
    if _client:
        _client.disconnect()


def get_client_status() -> dict:
    """获取客户端状态"""
    global _client
    if _client:
        status = _client.get_status()
        status['type'] = 'bluetooth' if isinstance(_client, BluetoothClient) else 'socket'
        return status
    return {'enabled': False, 'connected': False, 'type': 'none'}