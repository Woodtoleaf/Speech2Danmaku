import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from threading import Thread
import time
import ModelFastapi
import AudioRecord

# Global variables
sa_instance = None
recording_active = False
selected_device_index = None
window = None  # Global reference to the main window
server_thread = None

# Function to start FastAPI server in a separate thread
def start_server():
    global server_thread
    try:
        server_thread = Thread(target=ModelFastapi.start_fastapi_server)
        server_thread.start()
        time.sleep(5)  # Ensure server has started before returning
        messagebox.showinfo("Success", "Server started successfully")
        start_button.config(text="服务运行中")  # Update button text
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start server: {e}")

def stop_server():
    global server_thread
    if server_thread and server_thread.is_alive():
        try:
            ModelFastapi.stop_fastapi_server()
            server_thread.join()
            messagebox.showinfo("Success", "Server stopped successfully")
            start_button.config(text="启动服务（先运行）")  # Update button text
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop server: {e}")

def toggle_record():
    global sa_instance, recording_active

    if not recording_active:
        try:
            print(f"Selected device index: {selected_device_index}")  # Debugging output
            sa_instance = AudioRecord.SaveAudio(input_device_index=selected_device_index)
            sa_instance.set_threshold(threshold_slider.get())

            # Start flowtext thread
            flowtext_thread = Thread(target=sa_instance.flowtext_run)
            flowtext_thread.start()

            # Start audio thread
            audio_thread = Thread(target=sa_instance.audio_stream)
            audio_thread.start()

            messagebox.showinfo("Success", "Recording started successfully")
            recording_active = True
            toggle_button.config(text="停止字幕")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start recording: {e}")
    else:
        try:
            if sa_instance:
                # Stop flowtext and audio threads
                sa_instance.stop_flowtext()
                sa_instance.stop_audio()

                messagebox.showinfo("Success", "Recording stopped successfully")
                recording_active = False
                toggle_button.config(text="启动字幕（后运行）")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop recording: {e}")

def set_threshold(val):
    global sa_instance
    threshold_value = int(val)
    if sa_instance:
        # Use `after` to ensure this is executed in the main thread
        window.after(0, sa_instance.set_threshold, threshold_value)

def create_control_panel():
    global selected_device_index, toggle_button, threshold_slider, window, start_button

    selected_device_index = None

    # 创建窗口组件
    window = tk.Tk()
    window.geometry("300x300")
    window.title("Control Panel")

    def on_close():
        global sa_instance
        if sa_instance:
            sa_instance.stop_flowtext()
            sa_instance.stop_audio()

        stop_server()  # Stop FastAPI server

        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_close)  # 设置窗口关闭时的回调函数

    # 开始与停止
    start_button = tk.Button(window, text="启动服务（先运行）", command=start_server)
    start_button.pack(pady=10)

    toggle_button = tk.Button(window, text="启动字幕（后运行）", command=toggle_record)
    toggle_button.pack(pady=10)

    # Threshold slider
    threshold_slider = tk.Scale(window, from_=0, to=10000, orient=tk.HORIZONTAL, label="灵敏度", command=set_threshold)
    threshold_slider.set(1500)  # Set initial value to 1000
    threshold_slider.pack(pady=10)

    # Dropdown menu for audio devices
    devices = AudioRecord.list_audio_devices()
    device_names = [name for index, name in devices]

    def on_device_selected(event):
        global selected_device_index
        selected_device_index = devices[device_menu.current()][0]
        print(f"Selected device index updated to: {selected_device_index}")  # Debugging output

    device_menu = ttk.Combobox(window, values=device_names, state="readonly")
    device_menu.bind("<<ComboboxSelected>>", on_device_selected)
    device_menu.config(width=30)  # 设置宽度为 15
    device_menu.pack(pady=10)
    device_menu.set("选择输入设备（停止字幕后选择）")  # Set default value

    # Button to exit the program
    exit_button = tk.Button(window, text="退出程序", command=on_close)
    exit_button.pack(pady=10)

    # Run the tkinter main loop
    window.mainloop()

if __name__ == "__main__":
    control_thread = Thread(target=create_control_panel)
    control_thread.start()
    control_thread.join()  # Ensure the main thread waits for the GUI thread to finish