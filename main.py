from transcript import Transcription
import tkinter as tk
import threading

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcript 控制窗口")
        self.root.geometry("320x240")  # 设置窗口大小为320x240

        self.transcription = None
        self.is_running = False
        self.threshold = tk.DoubleVar(value=0.01)

        self.create_widgets()

    def create_widgets(self):
        self.btn_toggle = tk.Button(self.root, text="启动", command=self.toggle_transcription)
        self.btn_toggle.pack(pady=20)

        self.scale_label = tk.Label(self.root, text="灵敏度")
        self.scale_label.pack()

        self.scale = tk.Scale(self.root, from_=0.0, to=0.1, resolution=0.001, orient=tk.HORIZONTAL, variable=self.threshold, command=self.update_threshold)
        self.scale.pack()

        self.btn_quit = tk.Button(self.root, text="退出", command=self.quit_app)
        self.btn_quit.pack()

    def toggle_transcription(self):
        if not self.is_running:
            self.start_transcription()
        else:
            self.stop_transcription()

    def start_transcription(self):
        self.transcription = Transcription("flowtext", self.threshold.get())
        self.transcription_thread = threading.Thread(target=self.transcription.run)
        self.transcription_thread.start()
        self.is_running = True
        self.btn_toggle.config(text="停止")

    def stop_transcription(self):
        if self.transcription:
            self.transcription.stop()
            self.transcription_thread.join()
            self.transcription = None
        self.is_running = False
        self.btn_toggle.config(text="启动")

    def update_threshold(self, value):
        if self.transcription:
            self.transcription.set_threshold(float(value))

    def quit_app(self):
        if self.transcription and self.is_running:
            self.transcription.stop()
            self.transcription_thread.join()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()
