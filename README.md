# Edge TTS 语音合成项目

一个使用 `edge-tts` 库实现的基于 FastAPI 的语音合成服务，支持文本翻译和音频生成功能。

## 功能特点
- 支持多种语音（包括中文、英文等）
- 生成 MP3 格式音频文件和 SRT 字幕
- 集成百度翻译 API 实现文本翻译
- 异步处理，性能高效
- 提供 RESTful API 接口
- 支持通过 Web 界面访问音频列表

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
pip install -r requirements.txt
```

## 配置

在 `main.py` 中设置以下参数：

```python
# 百度翻译 API 配置
APP_ID = "your_baidu_app_id"  # 替换为你的百度翻译 API App ID
APP_KEY = "your_baidu_app_key"  # 替换为你的百度翻译 API App Key
SECRET_TOKEN = "your_secret_token"  # 替换为你的 API 访问令牌
```

- 百度翻译 API 可在 [百度智能云控制台](https://console.bce.baidu.com/) 申请
- `SECRET_TOKEN` 用于验证 API 请求，可自定义设置

## API 文档

### 运行 API 服务
```powershell
python main.py
```

服务将在 `http://localhost:8000` 启动，API 文档可在以下地址访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### API 端点

#### POST /api/tts

语音合成接口

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

文件下载接口

## 音频数据结构

项目包含以下与音频相关的文件：

### audio_list_grouped.json

一个 JSON 文件，包含按语言分组的音频列表信息。结构示例：

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

存放所有合成的 MP3 音频文件，文件命名与语音类型对应。

## Web 界面

通过静态网页可查看和播放音频列表：

### 本地访问
1. 创建 `index.html` 文件（可参考项目提供的示例）
2. 使用本地服务器打开：
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

## 可用语音

### 查看语音列表
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

## 注意事项
- 需要网络连接才能使用 edge-tts 和百度翻译服务
- 首次运行可能需要下载语音包
- 支持长文本合成
- 音频文件默认保存在项目根目录，可在代码中修改保存路径
- API 访问令牌需保密，不要泄露到公共仓库

## 清理临时文件

服务启动时会自动清理旧的音频和字幕文件，也可手动清理：

```powershell
for %%i in (*.mp3 *.srt) do if %%~ni == tts_* del %%i
```