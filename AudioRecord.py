import pyaudio
import wave
import numpy as np
import time
import io
from RequestText import Flowtext
import tkinter as tk
from threading import Thread, Event

# 定义参数
FORMAT = pyaudio.paInt16  # 采样位深度为16位
CHANNELS = 1  # 单声道
RATE = 16000  # 采样率16kHz
CHUNK = 1024  # 每次读取的帧数
THRESHOLD = 1500  # 声音阈值，根据实际情况调整
SILENCE_THRESHOLD = 1  # 静音持续时间阈值
MAX_SILENCE_THRESHOLD = 5  # 最大静音持续时间阈值

class SaveAudio:

    def __init__(self, input_device_index=None):
        # 初始化音频程序
        self.audio_buffer = io.BytesIO()
        self.wf = None
        self.frames = []
        self.initial_frames = []  # 保存初始录音数据
        self.threshold = THRESHOLD  # 初始化 threshold
        self.input_device_index = input_device_index  # 初始化输入设备索引

        # 初始化文本窗口
        self.flowtext = "初始化文本"
        self.root = None
        self.label = None
        # 控制程序启动和停止
        self.flowtext_stop_event = Event()
        self.audio_stop_event = Event()

    def audio_io(self):
        # 创建一个新的缓冲区
        buffer = io.BytesIO()
        wf = wave.open(buffer, "wb")
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
        wf.setframerate(RATE)

        # 写入初始录音数据和当前帧
        wf.writeframes(b''.join(self.initial_frames + self.frames))
        wf.close()

        # 更新主缓冲区
        self.audio_buffer = buffer

    def get_audio_data(self):
        # 获取内存中的最新 WAV 数据
        return self.audio_buffer.getvalue()

    def set_threshold(self, value):
        self.threshold = value

    def audio_stream(self):
        while not self.audio_stop_event.is_set():
            try:
                # 初始化PyAudio
                audio = pyaudio.PyAudio()

                # 打开麦克风流
                stream = audio.open(format=FORMAT, channels=CHANNELS,
                                    rate=RATE, input=True,
                                    input_device_index=self.input_device_index,
                                    frames_per_buffer=CHUNK)

                print("Listening...")

                recording = False  # 是否正在录音
                silence_start_time = None  # 静音开始时间
                recording_start_time = None  # 录音开始时间
                last_save_time = None  # 上一次保存时间

                while not self.audio_stop_event.is_set():
                    try:
                        data = stream.read(CHUNK, exception_on_overflow=False)
                        audio_data = np.frombuffer(data, dtype=np.int16)
                        amplitude = np.abs(audio_data).max()  # 获取振幅的最大值

                        # 判断是否有声音
                        if amplitude > self.threshold:
                            if not recording:
                                print("Recording started.")
                                recording = True
                                recording_start_time = time.time()  # 记录录音开始时间
                                last_save_time = recording_start_time  # 初始化上一次保存时间
                                self.initial_frames = self.frames.copy()  # 保存初始录音数据

                            self.frames.append(data)
                            silence_start_time = None  # 重置静音开始时间

                            # 每隔2秒保存一次录音数据
                            current_time = time.time()
                            if current_time - last_save_time >= 2:
                                elapsed_time = current_time - recording_start_time
                                self.audio_io()
                                self.flowtext = Flowtext.transcribe_audio(self.audio_buffer.getvalue())
                                # 使用主线程更新界面
                                self.root.after(0, self.update_text, self.flowtext)
                                print(self.flowtext)
                                print(f"Saved recording segment up to {elapsed_time:.2f} seconds")
                                last_save_time = current_time
                        else:
                            if recording:
                                if silence_start_time is None:
                                    silence_start_time = time.time()  # 记录静音开始时间
                                elif time.time() - silence_start_time > SILENCE_THRESHOLD:
                                    if time.time() - silence_start_time < MAX_SILENCE_THRESHOLD:    
                                        self.audio_io()
                                        self.flowtext = Flowtext.transcribe_audio(self.audio_buffer.getvalue())
                                        # 使用主线程更新界面
                                        self.root.after(0, self.update_text, self.flowtext)
                                        #print(self.flowtext)
                                        #print("Recording stopped due to silence.")
                                    # 超过最大静止时间就停止录制
                                    elif time.time() - silence_start_time > MAX_SILENCE_THRESHOLD:
                                        self.frames = []
                                        self.initial_frames = []
                                        self.audio_buffer = io.BytesIO()
                                        self.flowtext = ""
                                        # 使用主线程更新界面
                                        self.root.after(0, self.update_text, self.flowtext)
                                        recording = False
                    except IOError as e:
                        print(f"Error in audio stream: {e}")
                        break

                print("Finished listening.")

                # 关闭文件和音频流
                if recording:
                    self.audio_io()
                stream.stop_stream()
                stream.close()
                audio.terminate()
            except Exception as e:
                print(f"Error opening audio stream: {e}")

    # 定义窗口参数
    def create_window(self):
        self.root = tk.Tk()
        self.root.title("Floating Text Window")
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 800
        window_height = 100
        x_position = (screen_width - window_width) // 2
        y_position = screen_height - window_height - 50
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        
        self.label = tk.Label(self.root, text=self.flowtext, font=("SimHei", 24), fg="white", bg="black")
        self.label.pack(expand=True, fill=tk.BOTH)

    # 更新浮动文字
    def update_text(self, new_text):
        self.flowtext = new_text
        self.label.config(text=self.flowtext)
    
    # 启动浮动文字窗口
    def flowtext_run(self):
        while not self.flowtext_stop_event.is_set():
            self.create_window()
            self.root.mainloop()

    def stop_flowtext(self):
        close_window = Thread(target=self.close_window)
        close_window.start()
        self.flowtext_stop_event.set()
    
    def close_window(self):
        if self.root:
            self.root.destroy()

    def stop_audio(self):
        self.audio_stop_event.set()


def list_audio_devices():
    audio = pyaudio.PyAudio()
    info = audio.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')
    devices = []

    for i in range(num_devices):
        device_info = audio.get_device_info_by_host_api_device_index(0, i)
        if device_info['maxInputChannels'] > 0:
            devices.append((i, device_info['name']))
    
    audio.terminate()
    return devices
