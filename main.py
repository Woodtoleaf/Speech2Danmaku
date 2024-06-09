from transcript import Transcription
import tkinter as tk
import threading
import sounddevice as sd

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcript 控制窗口")
        self.root.geometry("320x320")  # 调整窗口大小以适应新控件

        self.transcription = None
        self.is_running = False
        self.threshold = tk.DoubleVar(value=0.01)
        self.input_device = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        self.btn_toggle = tk.Button(self.root, text="启动", command=self.toggle_transcription)
        self.btn_toggle.pack(pady=20)

        self.device_label = tk.Label(self.root, text="选择输入设备")
        self.device_label.pack()

        self.input_devices = self.get_input_devices()
        device_names = [device['name'] for device in self.input_devices]
        self.device_menu = tk.OptionMenu(self.root, self.input_device, *device_names)
        self.device_menu.pack()
        if device_names:
            self.input_device.set(device_names[0])  # 设置默认选择

        self.scale_label = tk.Label(self.root, text="灵敏度")
        self.scale_label.pack()

        self.scale = tk.Scale(self.root, from_=0.0, to=0.1, resolution=0.001, orient=tk.HORIZONTAL, variable=self.threshold, command=self.update_threshold)
        self.scale.pack()

        self.btn_quit = tk.Button(self.root, text="退出", command=self.quit_app)
        self.btn_quit.pack()

    def get_input_devices(self):
        devices = sd.query_devices()
        input_devices = [{'id': i, 'name': device['name']} for i, device in enumerate(devices) if device['max_input_channels'] > 0]
        return input_devices

    def toggle_transcription(self):
        if not self.is_running:
            self.start_transcription()
        else:
            self.stop_transcription()

    def start_transcription(self):
        selected_device_name = self.input_device.get()
        selected_device = next(device['id'] for device in self.input_devices if device['name'] == selected_device_name)
        self.transcription = Transcription("flowtext", self.threshold.get(), selected_device)
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
