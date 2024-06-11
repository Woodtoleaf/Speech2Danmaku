from fastapi import FastAPI, File, UploadFile, HTTPException
import uvicorn
from transformers import pipeline
import torch
import io
import soundfile as sf
from fastapi.responses import JSONResponse
import os
import signal


# 检查 CUDA 是否可用并设置设备
device = 0 if torch.cuda.is_available() else -1

# 初始化语音识别 pipeline
transcriber = pipeline(
    "automatic-speech-recognition", 
    model="models",
    device=device
)

transcriber.model.config.forced_decoder_ids = (
    transcriber.tokenizer.get_decoder_prompt_ids(
        language="zh", 
        task="transcribe"
    )
)

app = FastAPI()

@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    #print(f"Received file: {file.filename}")
    #print(f"Content type: {file.content_type}")

    if file.content_type != "audio/wav":
        raise HTTPException(status_code=400, detail="Invalid file type. Only WAV files are accepted.")
    
    audio_bytes = await file.read()
    audio, sample_rate = sf.read(io.BytesIO(audio_bytes))
    
    # 转录音频
    res = transcriber(audio)
    return res


def start_fastapi_server():
    uvicorn.run(app, host="127.0.0.1", port=8000)

def stop_fastapi_server():
    os.kill(os.getpid(), signal.SIGINT)


if __name__ == "__main__":
    start_fastapi_server()