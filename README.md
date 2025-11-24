# Edge TTS 语音合成项目

一个使用 `edge-tts` 库实现的基于 FastAPI 的语音合成服务，支持文本翻译和音频生成功能。

## ✨ 功能特性
- 🎤 **多语音支持**：覆盖中文、英文等多种语言和音色
- 🎵 **音频与字幕**：生成高质量 MP3 格式音频和同步 SRT 字幕
- 🌐 **自动翻译**：集成百度翻译 API 实现文本自动翻译
- ⚡ **异步高效**：采用异步处理架构，性能优异
- 📡 **RESTful API**：提供规范的 API 接口，易于集成
- 🖥️ **Web 界面**：支持通过静态网页查看和播放音频列表

## 🚀 快速开始

### 1. 安装依赖

#### 创建虚拟环境
```powershell
python -m venv .venv
```

#### 激活虚拟环境
```powershell
.venv\Scripts\Activate.ps1
```

#### 安装依赖
```powershell
pip install -r requirements.txt
```

### 2. 配置参数

项目使用环境变量管理配置。复制 `.env.example` 文件并重命名为 `.env`，然后填写以下参数：

```bash
# 百度翻译 API 配置
BAIDU_TRANSLATE_APP_ID=your_baidu_translate_app_id
BAIDU_TRANSLATE_APP_KEY=your_baidu_translate_app_key

# API访问令牌
API_SECRET_TOKEN=your_api_secret_token
```

- 百度翻译 API 可在 [百度智能云控制台](https://console.bce.baidu.com/) 申请
- `API_SECRET_TOKEN` 用于验证 API 请求，需妥善保管
- 确保 `.env` 文件不被提交到版本控制系统中（已在 `.gitignore` 中配置）

### 3. 启动服务

```powershell
python main.py
```

服务将在 `http://localhost:8000` 启动，API 文档可在以下地址访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 📖 API 文档

### 主要端点

#### POST /api/tts
**语音合成接口**

**请求参数：**
```json
{
  "text": "要转换的文本",
  "target_language": "目标语言代码（如 en、ja）",
  "voice": "语音类型（如 zh-CN-XiaoxiaoNeural）",
  "token": "你的 API 访问令牌"
}
```

**响应示例：**
```json
{
  "audio_url": "/api/download/tts_xxxx.mp3",
  "subtitle_url": "/api/download/tts_xxxx.srt",
  "translated_text": "翻译后的文本"
}
```

#### GET /api/download/{filename}
**文件下载接口**

用于下载生成的音频或字幕文件

## 📊 音频数据结构

### audio_list_grouped.json

按语言分组的音频列表信息文件，结构示例：

```json
[
  {
    "language": "Chinese",
    "languageCode": "zh-CN",
    "count": 2,
    "list": [
      {
        "friendlyName": "小桐",
        "shortName": "zh-CN-XiaotongNeural",
        "audioUrl": "mp3/zh-CN-XiaotongNeural.mp3",
        "parameters": {
          "name": "Microsoft Server Speech Text to Speech Voice (zh-CN, XiaoxiaoNeural)",
          "gender": "Female",
          "locale": "zh-CN"
        }
      },
      ...
    ]
  },
  ...
]
```

### mp3/ 文件夹

存放所有合成的 MP3 音频文件，文件命名与语音类型一一对应

## 🖥️ Web 界面

通过静态网页可查看和播放音频列表：

### 本地访问
1. 创建 `index.html` 文件（可参考项目提供的示例）
2. 使用 Python 内置服务器打开：
   ```powershell
   python -m http.server 8000
   ```
3. 在浏览器中访问 `http://localhost:8000`

### GitHub Pages 部署

1. 将项目推送到 GitHub
   ```bash
   git remote add origin https://github.com/your-username/your-repo-name.git
   git push -u origin master
   ```

2. 启用 GitHub Pages
   - 进入仓库 Settings → Pages
   - 选择分支：master，目录：/(root)
   - 点击 Save

3. 访问 Web 页面
   ```
   https://your-username.github.io/your-repo-name/
   ```

## 🗣️ 可用语音

### 查看所有语音
```powershell
edge-tts --list-voices
```

或查看本地文件：
```powershell
cat available_voices.txt
```

### 中文语音示例
- `zh-CN-XiaotongNeural`: 小桐 - 中文女声
- `zh-CN-YunzheNeural`: 云哲 - 中文男声
- `zh-CN-XiaoxiaoNeural`: 晓晓 - 中文女声

## ⚠️ 注意事项
- 需要稳定的网络连接才能使用 edge-tts 和百度翻译服务
- 首次运行可能需要下载语音包（取决于所选语音）
- 支持长文本合成，系统会自动进行分段处理
- 音频文件默认保存在项目根目录，可在代码中修改保存路径
- API 访问令牌需严格保密，切勿泄露到公共仓库

## 🧹 清理临时文件

服务启动时会自动清理旧的音频和字幕文件（前缀为 `tts_` 的文件），也可手动清理：

```powershell
for %%i in (*.mp3 *.srt) do if %%~ni == tts_* del %%i
```