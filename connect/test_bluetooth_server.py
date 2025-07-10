# server.py
import socket

# RFCOMM 蓝牙协议
server_sock = socket.socket(
    socket.AF_BLUETOOTH, 
    socket.SOCK_STREAM, 
    socket.BTPROTO_RFCOMM
)

# 绑定到本地任意可用的蓝牙适配器和 RFCOMM 端口 4
# 使用空字符串作为地址，系统会自动选择第一个可用的蓝牙设备
host = "28:A0:6B:F6:8C:BC" 
port = 4
server_sock.bind((host, port))

# 开始监听，1 表示允许的最大挂起连接数为 1
server_sock.listen(1)

print(f"[*] 正在监听 RFCOMM 端口 {port}...")

try:
    # 接受客户端连接
    # accept() 会阻塞程序，直到有客户端连接进来
    # 它返回一个新的套接字对象(client_sock)用于与该客户端通信，以及客户端的地址(client_info)
    client_sock, client_info = server_sock.accept()
    print(f"[+] 接受来自 {client_info[0]} 的连接")

    while True:
        # 从客户端接收数据，缓冲区大小为 1024 字节
        data = client_sock.recv(1024)
        if not data:
            break
        
        # 将收到的字节解码为字符串并打印
        received_message = data.decode('utf-8')
        print(f"[*] 收到消息: {received_message}")
        
        # 构造回复消息并发送给客户端
        response = f"服务器已收到你的消息: '{received_message}'"
        client_sock.sendall(response.encode('utf-8'))

except Exception as e:
    print(f"[!] 发生错误: {e}")

finally:
    print("[-] 关闭套接字")
    if 'client_sock' in locals():
        client_sock.close()
    server_sock.close()