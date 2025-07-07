# MediaPipe 手势检测项目

这是一个基于 MediaPipe 的实时手势检测应用程序，使用模块化架构设计，支持多种静态和动态手势识别，并具有轨迹追踪和命令行输出功能。

## 功能特点

- **实时手势检测**: 使用摄像头进行实时手势识别
- **多种手势支持**: 
  - 静态手势: V字手势(胜利手势)、竖大拇指(点赞)、倒竖大拇指
  - 动态手势: 握拳到张开手势、张开到握拳手势
- **轨迹追踪功能**: 
  - 实时握拳轨迹追踪与绘制
  - 智能去抖与自动清除
  - 命令行轨迹变化输出（JSON/简单格式）
- **双手支持**: 同时检测和识别两只手的手势
- **可配置界面**: 支持显示/隐藏手部关键点、手掌中心、FPS等
- **设备集成友好**: 标准化输出格式，便于与其他设备/软件集成
- **模块化设计**: 易于扩展新的手势检测器

## 项目结构

```
.
├── main.py                 # 主应用程序
├── config.py              # 配置文件
├── gesture_manager.py     # 手势管理器
├── hand_utils.py          # 手部工具类（包含轨迹绘制和输出功能）
├── gestures/              # 手势检测器模块
│   ├── __init__.py
│   ├── base.py           # 基础检测器类
│   ├── static/           # 静态手势检测器
│   │   ├── peace_sign.py # V字手势检测器
│   │   └── thumbs.py     # 竖大拇指/倒竖大拇指检测器
│   └── dynamic/          # 动态手势检测器
│       ├── hand_open.py  # 握拳到张开检测器
│       └── hand_close.py # 张开到握拳检测器（支持轨迹追踪）
├── cvzone/               # CVZone 手部检测模块
├── pyproject.toml        # 项目配置
├── uv.lock              # 依赖锁定文件
└── README.md             # 项目说明
```

## 安装要求

- Python 3.8 - 3.11
- 摄像头设备

## 安装步骤

1. 克隆或下载项目到本地
2. 安装依赖包：
   ```bash
   uv sync
   ```

## 运行方法

```bash
uv run python main.py
```

或者：

```bash
# 激活虚拟环境
source .venv/bin/activate
python main.py
```

## 使用说明

1. 启动程序后，摄像头会自动开启
2. 将手放在摄像头前方，程序会自动检测并识别手势
3. 支持的手势包括：
   - **V 字手势**: 伸出食指和中指形成 V 字形
   - **竖大拇指**: 竖起大拇指，其他手指握拳（点赞手势）
   - **倒竖大拇指**: 向下竖大拇指，其他手指握拳
   - **握拳到张开**: 从握拳状态快速张开手掌
   - **张开到握拳**: 从张开状态握拳（支持轨迹追踪和命令行输出）
4. 轨迹追踪功能：
   - 张开到握拳手势触发后，会显示握拳移动轨迹
   - 实时输出轨迹变化到命令行（可配置格式）
   - 松开握拳后轨迹自动清除
5. 按 'q' 键或关闭窗口退出程序

## 轨迹输出示例

**JSON格式输出**：
```json
[TRAIL_OUTPUT] {"timestamp":1751861591.025,"hand_id":"hand_0","hand_type":"Left","position":{"x":323,"y":210},"movement":{"dx":-10,"dy":-2,"distance":10.2},"previous_position":{"x":333,"y":212}}
```

**简单格式输出**：
```
[TRAIL_OUTPUT] Left_hand_0: pos=(323,210) move=(-10,+2) dist=10.2
```

## 配置选项

可以通过修改 `config.py` 文件来调整以下设置：

- **摄像头配置**: 摄像头索引、FPS、分辨率、检测参数
- **显示配置**: 是否显示关键点、手掌中心、摄像头窗口、FPS等
- **手势参数**: 各种手势的检测阈值和敏感度
- **轨迹追踪配置**: 
  - `enable_tracking`: 启用轨迹追踪
  - `debounce_frames`: 去抖帧数
  - `max_trail_points`: 最大轨迹点数
  - `trail_thickness`: 轨迹线粗细
- **命令行输出配置**:
  - `enable_console_output`: 启用命令行输出
  - `output_interval_frames`: 输出间隔帧数（回报率）
  - `movement_threshold`: 移动阈值（像素）
  - `output_format`: 输出格式（'json' 或 'simple'）
- **颜色配置**: 界面元素的颜色设置

## 手势检测原理

### 静态手势
- **V 字手势**: 检测食指和中指是否伸直且分开，其他手指是否弯曲，拇指是否收起
- **竖大拇指**: 检测大拇指是否朝上伸直，其他手指是否握拳贴近手掌
- **倒竖大拇指**: 检测大拇指是否朝下伸直，其他手指是否握拳贴近手掌

### 动态手势
- **握拳到张开**: 通过分析手指尖位置的方差变化来检测从握拳到张开的动作
- **张开到握拳**: 分析手指尖到掌心距离的减少来检测闭合动作，要求所有5根手指都参与
  - 轨迹追踪：记录握拳后的手部移动轨迹
  - 去抖机制：防止误触发和轨迹闪烁
  - 实时输出：将轨迹变化输出到命令行，便于设备集成

## 扩展开发

### 添加新的手势检测器

1. 在 `gestures/static/` 或 `gestures/dynamic/` 目录下创建新的检测器文件
2. 继承 `StaticGestureDetector` 或 `DynamicGestureDetector` 基类
3. 实现 `detect()` 方法
4. 在 `gesture_manager.py` 中注册新的检测器

### 使用轨迹输出进行设备集成

**Python 集成示例**：
```python
import subprocess
import json

# 监听程序输出
process = subprocess.Popen(['python', 'main.py'], 
                         stdout=subprocess.PIPE, 
                         text=True)

for line in process.stdout:
    if '[TRAIL_OUTPUT]' in line:
        if line.strip().startswith('[TRAIL_OUTPUT] {'):
            # JSON格式
            data = json.loads(line.split('[TRAIL_OUTPUT] ')[1])
            print(f"手部移动到: ({data['position']['x']}, {data['position']['y']})")
        else:
            # 简单格式
            print(f"轨迹变化: {line.strip()}")
```

### 自定义手势参数

修改 `config.py` 中的 `GESTURE_CONFIG` 部分来调整检测参数。

## 应用场景

- **游戏控制**: 通过手势控制游戏角色移动
- **智能家居**: 手势控制灯光、音响等设备
- **机器人控制**: 将轨迹数据传递给机械臂
- **演示控制**: 手势切换幻灯片
- **康复训练**: 记录手部运动数据
- **研究项目**: 手势识别算法研究

## 技术栈

- **MediaPipe**: Google 的机器学习框架，用于手部关键点检测
- **CVZone**: 基于 MediaPipe 的计算机视觉库
- **OpenCV**: 计算机视觉库，用于图像处理和显示
- **NumPy**: 数值计算库
- **Python 3.8+**: 编程语言
- **UV**: 现代 Python 包管理器

## 故障排除

1. **摄像头无法打开**: 检查摄像头是否被其他应用占用，或修改 `config.py` 中的 `CAMERA_INDEX`
2. **检测不准确**: 调整 `config.py` 中的检测参数，确保光线充足
3. **程序卡死**: 检查是否有其他程序占用摄像头资源
4. **轨迹追踪不工作**: 检查 `config.py` 中的 `enable_tracking` 是否为 `True`
5. **命令行无输出**: 检查 `enable_console_output` 配置，确保移动距离超过阈值
6. **GPU 警告**: 程序会自动使用 GPU 加速（如果可用），警告信息不影响功能

## 性能优化

- 调整 `CAMERA_FPS` 来平衡性能和延迟
- 修改 `max_trail_points` 来控制内存使用
- 调整 `output_interval_frames` 来控制输出频率

## 许可证

本项目仅供学习和研究使用。

## 贡献

欢迎提交问题报告和功能请求！
