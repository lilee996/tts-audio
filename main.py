import asyncio
import edge_tts
import random
import json
import re
import time
from hashlib import md5
import requests
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import os
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles

# 加载环境变量
load_dotenv()

# 配置信息 - 从环境变量获取敏感信息
APP_ID = os.environ.get("BAIDU_TRANSLATE_APP_ID", "")  # 百度翻译API App ID
APP_KEY = os.environ.get("BAIDU_TRANSLATE_APP_KEY", "")  # 百度翻译API App Key
SECRET_TOKEN = "1305381000" 
# 百度翻译API配置
TRANSLATE_ENDPOINT = "http://api.fanyi.baidu.com"
TRANSLATE_PATH = "/api/trans/vip/translate"
TRANSLATE_URL = TRANSLATE_ENDPOINT + TRANSLATE_PATH

# 创建FastAPI应用
app = FastAPI(title="Text-to-Speech API", description="将文本翻译并转换为音频", version="1.0.0")

# 配置CORS
origins = ["*"]  # 允许所有来源，适合开发环境

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)
# 请求模型
class TTSRequest(BaseModel):
    text: str  # 要转换的文本
    target_language: str  # 目标语言代码，如"en"、"ja"等
    voice: str  # 语音类型，如"zh-HK-HiuGaaiNeural"
    token: str  # 访问令牌
    translate: bool = False  # 是否翻译文本，默认不翻译
    use_custom_split: bool = True  # 是否使用自定义分割，默认使用

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
    try:
        r = requests.post(TRANSLATE_URL, params=payload, headers=headers)
        result = r.json()
        if "trans_result" in result:
            return result["trans_result"][0]["dst"]
        else:
            # 直接抛出异常，由上层统一处理返回格式
            raise Exception("翻译失败: " + result.get("error_msg", "未知错误"))
    except requests.exceptions.RequestException as e:
        # 处理网络请求异常
        raise Exception("翻译服务连接失败: " + str(e))

# 基于标点符号的文本分割函数，主要用于句子级别的分割
# 针对字幕生成，优化为按句号、问号、感叹号等结束标点分割，同时支持中英文逗号

def split_text_by_punctuation(text: str) -> list[str]:
    """
    将文本按照中文和英文的标点符号分割成句子或短语
    主要分割符：中文句号。问号？感叹号！英文句号.问号?感叹号!
    次要分割符：中文逗号，英文逗号,
    """
    if not text:
        return []
    
    # 按标点分割，支持中英文逗号、句号、问号、感叹号
    # (?<=[。？！.?!，,]) 正向肯定断言，表示前面是标点
    # (?![。？！.?!，,]) 正向否定断言，表示后面不是标点
    segments = re.split(r'(?<=[。？！.?!，,])(?![。？！.?!，,])', text)
    
    # 清理结果，去除空字符串和前后空格
    cleaned_segments = []
    for seg in segments:
        seg = seg.strip()
        if seg:
            cleaned_segments.append(seg)
    
    # 确保结果不为空
    if not cleaned_segments:
        return [text.strip()]
    
    return cleaned_segments

# SRT字幕解析函数
def parse_srt_content(srt_content: str) -> list[dict]:
    """
    解析SRT字幕内容，返回结构化的字幕列表
    """
    cues = []
    
    # SRT格式：
    # 序号
    # 开始时间 --> 结束时间
    # 文本内容
    # 
    
    # 使用正则表达式匹配SRT格式
    cue_pattern = re.compile(r'^(\d+)\s*\n([0-9:,]+) --> ([0-9:,]+)\s*\n(.*?)(?=\n\n|\Z)', re.DOTALL | re.MULTILINE)
    matches = cue_pattern.findall(srt_content)
    
    for match in matches:
        index = int(match[0])
        start_time = match[1]
        end_time = match[2]
        text = match[3].strip()
        
        cues.append({
            "index": index,
            "start_time": start_time,
            "end_time": end_time,
            "text": text
        })
    
    return cues

# SRT字幕重新生成函数
def regenerate_srt(new_segments: list[str], cues: list[dict]) -> str:
    """
    根据新的文本片段重新生成SRT字幕
    """
    if not cues or not new_segments:
        return ""
    
    # 计算如何将新片段分配到原有的时间区间
    # 这里采用简单的平均分配策略，可以根据需要优化
    total_cues = len(cues)
    total_segments = len(new_segments)
    
    # 如果新片段数量少于或等于原有的cue数量，直接分配
    # 如果新片段数量多于原有的cue数量，需要合并时间区间
    
    new_cues = []
    
    # 直接将新片段均匀分配到每个cue中
    for i, segment in enumerate(new_segments):
        cue_index = i % total_cues
        cue = cues[cue_index]
        new_cues.append({
            "index": i + 1,
            "start_time": cue["start_time"],
            "end_time": cue["end_time"],
            "text": segment
        })
    
    # 生成新的SRT内容
    srt_content = ""
    for cue in new_cues:
        srt_content += f"{cue['index']}\n"
        srt_content += f"{cue['start_time']} --> {cue['end_time']}\n"
        srt_content += f"{cue['text']}\n\n"
    
    return srt_content

def ms_to_srt_time(ms: int) -> str:
    """
    Convert milliseconds to SRT time format (HH:MM:SS,mmm)
    """
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    milliseconds = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

# 生成音频和字幕异步函数
async def generate_tts(text: str, voice: str, use_custom_split: bool = True) -> tuple[str, str]:
    # 生成唯一的文件名
    filename = f"tts_{md5(text.encode('utf-8')).hexdigest()}_{voice.replace('.', '_')}"
    os.makedirs("download_audio", exist_ok=True)
    audio_file = os.path.join("download_audio", f"{filename}.mp3")
    subtitle_file = os.path.join("download_audio", f"{filename}.srt")
    
    try:
        # 使用WordBoundary获取更精确的单词时间
        communicate = edge_tts.Communicate(text, voice, boundary="WordBoundary")
        word_chunks = []
        
        # 写入音频文件并收集单词边界
        with open(audio_file, "wb") as af:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    af.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    # chunk["offset"] and chunk["duration"] are in 100-nanosecond units
                    # Convert to milliseconds by dividing by 10,000 (1 ms = 10,000 * 100 ns)
                    word_chunks.append({
                        "word": chunk["text"],
                        "offset_ms": chunk["offset"] // 10000,
                        "duration_ms": chunk["duration"] // 10000
                    })
        
        # 根据参数决定是否使用自定义分割
        if use_custom_split:
            new_segments = split_text_by_punctuation(text)
        else:
            # 使用原分词方式（按单词或默认方式）
            new_segments = [text]
        
        # 根据use_custom_split参数决定使用哪种字幕生成方式
        if use_custom_split:
            # 使用自定义分割方式
            if word_chunks:
                # 将单词边界转换为带位置信息的列表
                words_with_positions = []
                current_pos = 0
                for chunk in word_chunks:
                    word = chunk["word"]
                    # 在原始文本中查找单词的位置
                    pos = text.find(word, current_pos)
                    if pos == -1:
                        continue
                    
                    end_pos = pos + len(word)
                    words_with_positions.append({
                        "word": word,
                        "start_pos": pos,
                        "end_pos": end_pos,
                        "offset_ms": chunk["offset_ms"],
                        "duration_ms": chunk["duration_ms"]
                    })
                    current_pos = end_pos
                
                # 生成新的字幕cue
                new_cues = []
                index = 0
                current_pos = 0  # 用于跟踪当前查找位置，避免重复匹配
                
                for segment in new_segments:
                    segment = segment.strip()
                    if not segment:
                        continue
                    
                    # 查找片段在原始文本中的位置，从上一个位置开始
                    seg_start = text.find(segment, current_pos)
                    if seg_start == -1:
                        continue
                    
                    seg_end = seg_start + len(segment)
                    # 更新当前位置为该片段的结束位置，下一次查找从这里开始
                    current_pos = seg_end
                    
                    # 找到对应片段的所有单词
                    seg_words = [
                        w for w in words_with_positions
                        if w["start_pos"] < seg_end and w["end_pos"] > seg_start
                    ]
                    
                    if not seg_words:
                        continue
                    
                    # 计算片段的开始和结束时间
                    start_time = seg_words[0]["offset_ms"]
                    end_time = seg_words[-1]["offset_ms"] + seg_words[-1]["duration_ms"]
                    
                    # 转换为SRT时间格式
                    srt_start = ms_to_srt_time(start_time)
                    srt_end = ms_to_srt_time(end_time)
                    
                    # 添加到新的cue列表
                    index += 1
                    new_cues.append({"index": index, "start_time": srt_start, "end_time": srt_end, "text": segment})
                
                # 生成SRT内容
                srt_content = ""
                for cue in new_cues:
                    srt_content += f"{cue['index']}\n"
                    srt_content += f"{cue['start_time']} --> {cue['end_time']}\n"
                    srt_content += f"{cue['text']}\n\n"
            else:
                # 如果没有获取到单词边界，使用默认的字幕生成方式
                communicate = edge_tts.Communicate(text, voice, boundary="SentenceBoundary")
                submaker = edge_tts.SubMaker()
                
                # 重新写入音频文件并收集边界信息
                with open(audio_file, "wb") as af:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            af.write(chunk["data"])
                        elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                            submaker.feed(chunk)
                
                # 获取原始SRT内容
                original_srt = submaker.get_srt()
                
                # 解析原始SRT
                original_cues = parse_srt_content(original_srt)
                
                # 重新生成SRT
                new_srt = regenerate_srt(new_segments, original_cues)
                
                srt_content = new_srt
            
            # 保存新的SRT文件
            with open(subtitle_file, "w", encoding="utf-8") as sf:
                sf.write(srt_content)
        else:
            # 使用edge_tts的原分词方式生成字幕
            communicate = edge_tts.Communicate(text, voice, boundary="WordBoundary")
            submaker = edge_tts.SubMaker()
            
            # 重新写入音频文件并收集边界信息
            with open(audio_file, "wb") as af:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        af.write(chunk["data"])
                    elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                        submaker.feed(chunk)
            
            # 获取原始SRT内容并保存
            original_srt = submaker.get_srt()
            with open(subtitle_file, "w", encoding="utf-8") as sf:
                sf.write(original_srt)
        
        return audio_file, subtitle_file
    except Exception as e:
        # 清理可能生成的部分文件
        if os.path.exists(audio_file):
            os.remove(audio_file)
        if os.path.exists(subtitle_file):
            os.remove(subtitle_file)
        # 直接返回错误信息，由上层统一处理返回格式
        raise

# TTS API端点
@app.post("/api/tts", response_model=dict)
async def text_to_speech(tts_request: TTSRequest, request: Request):
    cleanup_files()
    # 验证令牌
    if tts_request.token != SECRET_TOKEN:
        # 返回统一格式的错误响应
        return {
            "code": 401,
            "message": "无效的访问令牌",
            "data": None
        }
    
    try:
        # 根据translate参数决定是否翻译文本
        if tts_request.translate:
            translated_text = translate_text(tts_request.text, to_lang=tts_request.target_language)
        else:
            translated_text = tts_request.text
        
        # 生成音频和字幕
        audio_file, subtitle_file = await generate_tts(translated_text, tts_request.voice, tts_request.use_custom_split)
        
        # 构造绝对URL
        port_suffix = f":{request.url.port}" if request.url.port is not None else ""
        base_url = f"{request.url.scheme}://{request.url.hostname}{port_suffix}"
        
        # 返回文件路径
        return {
            "code": 200,
            "message": "处理成功",
            "data": {
                "audio_url": f"{base_url}/api/download/{os.path.basename(audio_file)}",
                "subtitle_url": f"{base_url}/api/download/{os.path.basename(subtitle_file)}",
                "translated_text": translated_text
            }
        }
    except Exception as e:
        error_message = str(e)
        # 判断错误类型，返回对应的提示信息
        message = "该角色暂时无法使用" if "No audio was received" in error_message else "处理失败: " + error_message
        # 返回统一格式的错误响应，HTTP状态码为200，code字段为400
        return {
            "code": 400,
            "message": message,
            "data": None
        }

# 文件下载端点
@app.get("/api/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(os.getcwd(), "download_audio", filename)
    if not os.path.exists(file_path):
        # 返回统一格式的错误响应
        return {
            "code": 404,
            "message": "文件不存在",
            "data": None
        }
    return FileResponse(file_path, filename=filename)

# 清理临时文件（可选）
def cleanup_files():
    if os.path.exists("download_audio"):
        # 计算7天前的时间戳（秒）
        seven_days_ago = time.time() - 7 * 24 * 60 * 60
        for file in os.listdir("download_audio"):
            if file.endswith(".mp3") or file.endswith(".srt"):
                file_path = os.path.join("download_audio", file)
                # 获取文件的修改时间
                file_mtime = os.path.getmtime(file_path)
                # 如果文件修改时间超过7天，则删除
                if file_mtime < seven_days_ago:
                    os.remove(file_path)

if __name__ == "__main__":
    # 创建download_audio目录（如果不存在）
    os.makedirs("download_audio", exist_ok=True)
    # 在启动服务前清理旧文件
    print("启动TTS服务...")
    print(f"服务地址: http://localhost:8000")
    print(f"API文档: http://localhost:8000/docs")
    app.mount("/mp3", StaticFiles(directory="mp3"), name="mp3")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")