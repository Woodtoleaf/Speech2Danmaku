import httpx
from pydub import AudioSegment
import io

class Flowtext():
    def transcribe_audio(audio_data):
        # 将音频数据转换为 AudioSegment 对象
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format="wav")
        
        # 将音频数据导出为 WAV 格式到内存中
        audio_io = io.BytesIO()
        audio.export(audio_io, format="wav")
        audio_io.seek(0)
        
        # 准备文件数据
        files = {'file': ('audio.wav', audio_io, 'audio/wav')}
        
        # 发送 POST 请求到服务器
        response = httpx.post("http://127.0.0.1:8000/transcribe/", files=files)
        
        # 检查响应状态并打印结果
        if response.status_code == 200:
            #print(response.json())
            return response.json()['text']
        else:
            print("Request failed with status code:", response.status_code)
            print("Response:", response.text)
            return None
