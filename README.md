# Edge TTS 语音合成项目

一个使用 `edge-tts` 库实现的简单Python语音合成项目。

## 功能特点
- 支持多种语音（包括中文、英文等）
- 生成 MP3 格式音频文件
- 异步处理，性能高效

## 安装依赖

### 1. 创建虚拟环境
```powershell
python -m venv .venv
```

### 2. 激活虚拟环境
```powershell
.venv\Scripts\Activate.ps1
```

### 3. 安装依赖
```powershell
pip install edge-tts
```

或使用 `requirements.txt` 安装：
```powershell
pip install -r requirements.txt
```

## 使用说明

### 运行示例脚本
```powershell
python main.py
```

脚本将合成默认文本 "您好，欢迎使用edge-tts进行语音合成！" 并生成 `output.mp3` 文件。

### 自定义参数

在 `main.py` 中修改以下参数：

- `TEXT`: 要合成的文本内容
- `VOICE`: 选择语音类型
- `OUTPUT_FILE`: 输出文件路径

## 可用语音

要查看所有可用的语音列表，可运行以下命令：
```powershell
edge-tts --list-voices
```

### 中文语音示例
- `zh-CN-XiaoxiaoNeural`: 中文女声
- `zh-CN-YunjianNeural`: 中文男声
- `zh-CN-YunxiNeural`: 中文男声

## 注意事项
- 需要网络连接才能使用 edge-tts 服务
- 首次运行可能需要下载语音包
- 支持长文本合成