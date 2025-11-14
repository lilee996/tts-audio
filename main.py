import asyncio
import edge_tts
import random
import json
from hashlib import md5
import requests
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import os

# 配置信息
APP_ID = "your_baidu_app_id"  # 替换为你的百度翻译API App ID
APP_KEY = "your_baidu_app_key"  # 替换为你的百度翻译API App Key
SECRET_TOKEN = "your_secret_token"  # 替换为你的API访问令牌，用于验证请求

# 百度翻译API配置
TRANSLATE_ENDPOINT = "http://api.fanyi.baidu.com"
TRANSLATE_PATH = "/api/trans/vip/translate"
TRANSLATE_URL = TRANSLATE_ENDPOINT + TRANSLATE_PATH

# 创建FastAPI应用
app = FastAPI(title="Text-to-Speech API", description="将文本翻译并转换为音频", version="1.0.0")

# 请求模型
class TTSRequest(BaseModel):
    text: str  # 要转换的文本
    target_language: str  # 目标语言代码，如"en"、"ja"等
    voice: str  # 语音类型，如"zh-HK-HiuGaaiNeural"
    token: str  # 访问令牌

# 生成MD5签名
def make_md5(s, encoding='utf-8'):
    return md5(s.encode(encoding)).hexdigest()

# 百度翻译函数
def translate_text(query: str, from_lang: str = "zh", to_lang: str = "en") -> str:
    salt = random.randint(32768, 65536)
    sign = make_md5(APP_ID + query + str(salt) + APP_KEY)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {
        'appid': APP_ID, 
        'q': query, 
        'from': from_lang, 
        'to': to_lang, 
        'salt': salt, 
        'sign': sign
    }
    r = requests.post(TRANSLATE_URL, params=payload, headers=headers)
    result = r.json()
    if "trans_result" in result:
        return result["trans_result"][0]["dst"]
    else:
        raise HTTPException(status_code=500, detail="翻译失败: " + result.get("error_msg", "未知错误"))

# 生成音频和字幕异步函数
async def generate_tts(text: str, voice: str) -> tuple[str, str]:
    # 生成唯一的文件名
    filename = f"tts_{md5(text.encode('utf-8')).hexdigest()}_{voice.replace('.', '_')}"
    audio_file = f"{filename}.mp3"
    subtitle_file = f"{filename}.srt"
    
    try:
        communicate = edge_tts.Communicate(text, voice, boundary="SentenceBoundary")
        submaker = edge_tts.SubMaker()
        
        # 写入音频文件和生成字幕
        with open(audio_file, "wb") as af:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    af.write(chunk["data"])
                elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                    submaker.feed(chunk)
        
        # 保存字幕文件
        with open(subtitle_file, "w", encoding="utf-8") as sf:
            sf.write(submaker.get_srt())
        
        return audio_file, subtitle_file
    except Exception as e:
        # 清理可能生成的部分文件
        if os.path.exists(audio_file):
            os.remove(audio_file)
        if os.path.exists(subtitle_file):
            os.remove(subtitle_file)
        raise HTTPException(status_code=500, detail="音频生成失败: " + str(e))

# TTS API端点
@app.post("/api/tts", response_model=dict)
async def text_to_speech(request: TTSRequest):
    # 验证令牌
    if request.token != SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="无效的访问令牌")
    
    try:
        # 翻译文本
        translated_text = translate_text(request.text, to_lang=request.target_language)
        
        # 生成音频和字幕
        audio_file, subtitle_file = await generate_tts(translated_text, request.voice)
        
        # 返回文件路径
        return {
            "audio_url": f"/api/download/{os.path.basename(audio_file)}",
            "subtitle_url": f"/api/download/{os.path.basename(subtitle_file)}",
            "translated_text": translated_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="处理失败: " + str(e))

# 文件下载端点
@app.get("/api/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(os.getcwd(), filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path, filename=filename)

# 清理临时文件（可选）
def cleanup_files():
    for file in os.listdir(os.getcwd()):
        if file.endswith(".mp3") or file.endswith(".srt"):
            if file.startswith("tts_"):
                os.remove(file)

if __name__ == "__main__":
    # 在启动服务前清理旧文件
    cleanup_files()
    print("启动TTS服务...")
    print(f"服务地址: http://localhost:8000")
    print(f"API文档: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")