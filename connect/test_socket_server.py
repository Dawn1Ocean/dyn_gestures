import socket
import threading

def start_server(host='127.0.0.1', port=65432, connection_handler=None):
    """
    启动一个TCP服务器，监听指定的地址和端口。

    :param host: 服务器绑定的主机名或IP地址 (默认为 '127.0.0.1')。
    :param port: 服务器监听的端口号 (默认为 65432)。
    :param connection_handler: 一个函数，用于处理每个客户端连接。
                               该函数应接受 conn (socket对象) 和 addr (地址) 两个参数。
    """
    if connection_handler is None:
        raise ValueError("必须提供一个 connection_handler 函数")

    # AF_INET 表示使用 IPv4 地址, SOCK_STREAM 表示使用 TCP 协议
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"服务器已在 {host}:{port} 启动，等待客户端连接...")

        while True:
            # accept() 会阻塞程序，直到有客户端连接进来
            conn, addr = s.accept()
            # 为每个客户端创建一个新线程来处理，避免阻塞主线程
            # 这样服务器就可以同时响应多个客户端（尽管在这个例子中我们主要考虑一对一）
            thread = threading.Thread(target=connection_handler, args=(conn, addr))
            thread.start()

def handle_connection(conn, addr):
    """
    这是一个处理客户端连接的示例函数。
    你可以根据你的需求，编写自己的处理逻辑。
    """
    print(f"客户端 {addr} 已连接。")
    with conn:
        while True:
            # recv(1024) 表示一次最多接收 1024 字节的数据
            # 如果客户端关闭了连接，recv() 会返回一个空字节串 b''
            data = conn.recv(1024)
            if not data:
                print(f"客户端 {addr} 已断开连接。")
                break
            
            # 将收到的字节数据解码为UTF-8字符串
            message = data.decode('utf-8')
            print(f"收到来自 {addr} 的消息: {message}")
            
            # 准备并发送响应
            response = f"服务器已收到您的消息: '{message}'"
            # 将响应字符串编码为字节数据并发送
            conn.sendall(response.encode('utf-8'))

# --- 如何使用 ---
if __name__ == "__main__":
    # 将我们自定义的 handle_connection 函数作为参数传递给 start_server
    # 程序会在这里进入一个无限循环，等待连接
    try:
        start_server(host='127.0.0.1', port=65432, connection_handler=handle_connection)
    except KeyboardInterrupt:
        print("\n服务器被手动关闭。")
    except Exception as e:
        print(f"服务器出错: {e}")