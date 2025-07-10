# MediaPipe 手势检测项目

这是一个基于 MediaPipe 的实时手势检测应用程序，采用现代化模块化架构设计，支持多种静态和动态手势识别，并具有轨迹追踪、网络通信和命令行输出功能。

## ✨ 功能特点

### 🎯 手势检测功能
- **实时手势检测**: 使用摄像头进行实时手势识别
- **多种手势支持**: 
  - 静态手势: 数字手势(一、二、三)、竖大拇指(点赞)、倒竖大拇指
  - 动态手势: 握拳到张开手势、张开到握拳手势、左右挥手手势、双指滑动手势、手掌翻转手势
- **双手支持**: 同时检测和识别两只手的手势

### 🎨 轨迹追踪功能
- **实时握拳轨迹追踪与绘制**: 可视化手部移动轨迹
- **智能轨迹平滑算法**: 减少手部抖动影响
- **抗抖动机制**: 提高手势检测稳定性
- **智能去抖与自动清除**: 自动管理轨迹生命周期
- **命令行轨迹变化输出**: 支持JSON/简单格式输出

### 📱 远程摄像头支持 (新功能)
- **Android设备摄像头**: 支持使用Android平板/手机作为摄像头
- **无线连接**: 通过WiFi网络连接远程摄像头
- **高质量画面**: 支持高分辨率视频流
- **实时传输**: 低延迟的图像传输

### 🔧 技术特性
- **模块化设计**: 易于扩展新的手势检测器
- **可配置界面**: 支持显示/隐藏手部关键点、手掌中心、FPS等
- **设备集成友好**: 标准化输出格式，便于与其他设备/软件集成
- **网络通信支持**: 集成Socket客户端，支持远程设备控制
- **性能监控**: 实时FPS显示和日志记录
- **现代化包管理**: 使用UV包管理器，支持快速安装和依赖管理

## 📁 项目结构

```
cvzone-test/
├── 📄 main.py                    # 主应用程序入口
├── ⚙️ config.py                  # 全局配置文件
├── 📹 camera_manager.py          # 摄像头管理器 (支持本地和远程摄像头)
├── 🖼️ display.py                 # 显示管理器
├── 🤏 hand_utils.py              # 手部工具类（包含轨迹绘制和输出功能）
├── 📝 logger_config.py           # 日志配置
├── 🎯 gestures/                  # 手势检测器模块
│   ├── __init__.py
│   ├── base.py                   # 基础检测器类
│   ├── manager.py                # 手势管理器
│   ├── output.py                 # 输出管理器
│   ├── trajectory_tracker.py     # 轨迹追踪器
│   ├── static/                   # 静态手势检测器
│   │   ├── __init__.py
│   │   ├── finger_count_one.py   # 数字一手势检测器
│   │   ├── finger_count_two.py   # 数字二手势检测器  
│   │   ├── finger_count_three.py # 数字三手势检测器
│   │   └── thumbs.py             # 竖大拇指/倒竖大拇指检测器
│   └── dynamic/                  # 动态手势检测器
│       ├── __init__.py
│       ├── hand_open.py          # 握拳到张开检测器
│       ├── hand_close.py         # 张开到握拳检测器（支持轨迹追踪）
│       ├── hand_swipe.py         # 左右挥手检测器
│       ├── hand_flip.py          # 手掌翻转检测器
│       └── two_finger_swipe.py   # 双指滑动检测器
├── 🌐 connect/                   # 网络通信模块
│   ├── socket_client.py          # Socket客户端
│   └── test_socket_server.py     # Socket服务器测试
├── 🔧 cvzone/                    # CVZone 手部检测模块
│   ├── HandTrackingModule.py     # 手部追踪模块
│   └── hand_landmarker.task      # MediaPipe 模型文件
├── 📊 logs/                      # 日志目录
├── 📦 pyproject.toml             # 项目配置和依赖
├── 🔒 uv.lock                    # UV依赖锁定文件
└── 📖 README.md                  # 项目说明文档
```

## 🚀 快速开始

### 📋 系统要求

- **Python**: 3.8 - 3.11
- **摄像头**: 支持OpenCV的摄像头设备 或 Android设备 (用于远程摄像头)
- **操作系统**: Windows、macOS、Linux
- **内存**: 建议4GB以上

### 📦 安装步骤

#### 方法一：使用UV包管理器（推荐）

```bash
# 安装uv包管理器
pip install uv

# 克隆项目
git clone [项目地址]
cd dyn_gestures

# 安装依赖
uv sync

# 运行项目
uv run python main.py
```

#### 方法二：使用传统pip

```bash
# 克隆项目
git clone [项目地址] 
cd dyn_gestures

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行项目  
python main.py
```

## 📱 远程摄像头配置指南 (Android设备)

### 🎯 使用Xiaomi Pad 6 Pro作为摄像头

#### 第一步：Android端设置

1. **下载IP Webcam应用**
   - Google Play Store: 搜索 "IP Webcam"
   - 或下载APK: https://ip-webcam.appspot.com/

2. **配置IP Webcam**
   ```
   启动应用 → 设置选项：
   - 视频分辨率: 640x480 或 800x600 (推荐)
   - 质量: 80% (平衡画质和传输速度)
   - FPS限制: 15-30 (根据网络情况调整)
   ```

3. **启动摄像头服务**
   - 点击 "启动服务器"
   - 记下显示的IP地址，例如: `192.168.31.123:8080`

#### 第二步：PC端配置

1. **修改配置文件**
   编辑 `config.py`:
   ```python
   # 启用IP摄像头
   USE_IP_CAMERA = True
   
   # 设置小米平板的IP地址
   IP_CAMERA_URL = "http://192.168.31.123:8080"  # 替换为实际IP
   ```

2. **确保网络连接**
   - PC和小米平板必须在同一WiFi网络中
   - 测试连接：在浏览器访问 `http://192.168.31.123:8080`

#### 第三步：运行手势检测

```bash
python main.py
```

看到日志输出：
```
摄像头信息: IP摄像头: http://192.168.31.123:8080
远程摄像头提示：确保小米平板和PC在同一WiFi网络中
```

### 🔧 其他方案选择

#### 方案二：DroidCam (备选)
1. 下载DroidCam应用
2. 修改 `IP_CAMERA_URL` 为DroidCam的地址格式

#### 方案三：RTSP摄像头
对于支持RTSP的摄像头应用，可以使用：
```python
IP_CAMERA_URL = "rtsp://192.168.1.100:5554/camera"
```

### 📊 性能优化建议

1. **网络优化**
   - 使用5GHz WiFi (更快传输)
   - 确保路由器和设备距离较近
   - 关闭其他占用带宽的应用

2. **画质设置**
   ```python
   # config.py 中调整分辨率
   CAMERA_FRAME_WIDTH = 640   # 降低分辨率可提高帧率
   CAMERA_FRAME_HEIGHT = 360
   ```

3. **延迟控制**
   - IP Webcam中降低质量设置到60-80%
   - 使用有线网络连接PC (如果可能)

### 🐛 故障排除

#### 常见问题

1. **连接失败**
   ```
   错误: IP摄像头初始化失败
   解决: 检查IP地址是否正确，设备是否在同一网络
   ```

2. **画面卡顿**
   ```
   原因: 网络带宽不足
   解决: 降低分辨率或画质设置
   ```

3. **无法读取数据**
   ```
   错误: 无法读取IP摄像头数据
   解决: 检查IP Webcam应用是否仍在运行
   ```

#### 调试步骤

1. **测试网络连接**
   ```bash
   ping 192.168.31.123  # 替换为实际IP
   ```

2. **浏览器测试**
   访问: `http://192.168.31.123:8080/shot.jpg`
   应该能看到单张图片

3. **查看详细日志**
   ```python
   # config.py 中启用调试
   IS_DEBUG = True
   ```

## 🎮 使用说明

### 支持的手势

1. **数字手势**
   - 🔢 **数字一**: 伸出食指 → 复制 (Ctrl+C)
   - 🔢 **数字二**: 伸出食指和中指 → 粘贴 (Ctrl+V)  
   - 🔢 **数字三**: 伸出食指、中指和无名指 → 撤销 (Ctrl+Z)

2. **拇指手势**
   - 👍 **竖大拇指**: 拇指向上 → 向上滚动
   - 👎 **倒大拇指**: 拇指向下 → 向下滚动

3. **动态手势**
   - 🖐️ **握拳张开**: 握拳后快速张开 → 窗口全屏
   - ✊ **张开握拳**: 张开后握拳并移动 → 拖拽窗口
   - 👆 **双指滑动**: 食指中指并拢水平滑动 → 窗口最小化
   - 👋 **左右挥手**: 手掌水平挥动 → 切换窗口
   - 🔄 **手掌翻转**: 手掌翻转动作 → 关闭窗口

### 运行模式

#### 标准模式
```bash
python main.py
```

#### 调试模式
```bash
# 修改 config.py
IS_DEBUG = True

python main.py
```

## ⚙️ 配置说明

### 摄像头配置
```python
# 本地摄像头
USE_IP_CAMERA = False
CAMERA_INDEX = 0

# 远程摄像头
USE_IP_CAMERA = True
IP_CAMERA_URL = "http://192.168.1.100:8080"
```

### 手势检测参数
```python
HAND_DETECTION_CONFIG = {
    'max_hands': 1,                    # 最大检测手数
    'detection_confidence': 0.5,       # 检测置信度
    'min_tracking_confidence': 0.5     # 跟踪置信度
}
```

### Socket通信
```python
SOCKET_HOST = '192.168.31.247'  # 目标主机
SOCKET_PORT = 65432             # 端口号
```

## 🔗 与project项目连接

1. **启动project的Socket服务器**
   ```bash
   cd ../project
   python app.py
   # 点击"启动Socket服务器"
   ```

2. **启动dyn_gestures客户端**
   ```bash
   python main.py
   ```

3. **验证连接**
   - project界面显示"客户端已连接"
   - 手势识别结果实时传输到project

## 📝 开发指南

### 添加新手势
1. 继承 `GestureDetector` 基类
2. 实现 `detect()` 方法
3. 在 `GestureManager` 中注册

### 自定义输出格式
修改 `gestures/output.py` 中的输出函数

### 性能调优
调整 `config.py` 中的检测参数和FPS设置

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 📄 许可证

MIT License - 详见LICENSE文件

## 🆘 技术支持

遇到问题？
1. 查看日志输出
2. 检查网络连接
3. 确认配置文件设置
4. 提交Issue描述问题

---

**享受远程手势控制的便利！** 🎉
