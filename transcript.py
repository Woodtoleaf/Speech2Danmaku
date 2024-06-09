import tkinter as tk
import sounddevice as sd
import soundfile as sf
import numpy as np
from transformers import pipeline
import threading
import queue
import os
import torch
import psutil

# 设置设备
device = 0 if torch.cuda.is_available() else -1
fs = 44100
duration = 0.5  # 每次录音时间为0.5秒

# 加载模型
try:
    transcriber = pipeline(
        "automatic-speech-recognition",
        model="models",
        device=device
    )
    transcriber.model.config.forced_decoder_ids = transcriber.tokenizer.get_decoder_prompt_ids(language="zh", task="transcribe")
except Exception as e:
    print(f"模型加载失败: {e}")
    raise

class Transcription:
    def __init__(self, text, threshold, cpu_affinity=None):
        self.text = text
        self.threshold = threshold
        self.root = None
        self.audio_queue = queue.Queue(maxsize=10)  # 增加队列大小
        self.running = threading.Event()
        self.running.set()
        self.cpu_affinity = cpu_affinity

    def create_window(self):
        self.root = tk.Tk()
        self.root.title("浮动文字窗口")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 800
        window_height = 100
        x_position = (screen_width - window_width) // 2
        y_position = screen_height - window_height - 50
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.root.attributes("-topmost", True)
        self.label = tk.Label(self.root, text=self.text, font=("SimHei", 24), fg="white", bg="black")
        self.label.pack(expand=True, fill=tk.BOTH)
        self.label.bind("<Button-1>", self.start_move)
        self.label.bind("<B1-Motion>", self.do_move)
        self._offsetx = 0
        self._offsety = 0
        self.update_text()

    def start_move(self, event):
        self._offsetx = event.x
        self._offsety = event.y

    def do_move(self, event):
        x = event.x_root - self._offsetx
        y = event.y_root - self._offsety
        self.root.geometry(f"+{x}+{y}")

    def update_text(self):
        self.label.config(text=self.text)
        if self.running.is_set():
            self.root.after(1000, self.update_text)

    def record_and_save(self):
        if self.cpu_affinity:
            p = psutil.Process(os.getpid())
            p.cpu_affinity(self.cpu_affinity)  # 设置进程的 CPU 亲和性
        
        while self.running.is_set():
            try:
                recording = sd.rec(int(duration * fs), samplerate=fs, channels=2)
                sd.wait()
                if self.audio_queue.full():
                    self.audio_queue.get()
                self.audio_queue.put(recording)
            except Exception as e:
                print(f"录音失败: {e}")

    
    def transcribe_and_update(self):
        if not self.running.is_set():
            return
        
        try:
            if not self.audio_queue.empty():
                recordings = list(self.audio_queue.queue)
                if all(not self.is_silent(recording) for recording in recordings):
                    combined_recording = np.concatenate(recordings, axis=0)
                    filename = "combined_recording.wav"
                    sf.write(filename, combined_recording, fs)
                    transcription = transcriber(filename)
                    transcribed_text = transcription['text']
                    os.remove(filename)
                else:
                    self.text = "No speech detected."

                # Update GUI
                self.root.after(0, self.update_gui_text, transcribed_text)
        except Exception as e:
            print(f"转录失败: {e}")
        
        # 2秒后再次调用
        threading.Timer(2.0, self.transcribe_and_update).start()

    def update_gui_text(self, text):
        self.text = text
        self.label.config(text=self.text)

    def is_silent(self, data, threshold=None):
        if threshold is None:
            threshold = self.threshold
        return np.max(np.abs(data)) < threshold

    def set_threshold(self, threshold):
        self.threshold = threshold

    def run(self):
        self.create_window()
        threading.Thread(target=self.record_and_save, daemon=True).start()
        self.transcribe_and_update()  # 启动定时调用
        self.root.mainloop()

    def stop(self):
        self.running.clear()
        if self.root:
            self.root.quit()