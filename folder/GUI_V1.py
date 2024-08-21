import tkinter as tk
from tkinter import scrolledtext, font
import subprocess
import time


def start_all():
    for exe in exes:
        run_exe(exe)
        time.sleep(0.1)


def run_exe(exe):

    try:
        result = subprocess.run(f'{exe}', capture_output=True, text=True)
        output = result.stdout
    except Exception as e:
        output = str(e)

    display_result(output)


def display_result(text):
    result_text.insert(tk.END, text + "\n")
    result_text.see(tk.END)


window = tk.Tk()
window.title("WinMate控制器功能測試V1.0")
window.state('zoomed')
font_style = font.Font(size=20)
start_button = tk.Button(window, text="全部啟動", width=140, height=7, command=start_all, font=font_style)
start_button.grid(row=0, column=0, columnspan=5, pady=10)

exes = ['.\\BT_subprocess.exe', '.\\PingTest_subprocess.exe', '.\\wifi_subprocess.exe', '.\\WR_subprocess.exe', '.\\RS485.exe']
button_width = 22
button_height = 7
PingTest_subprocess_exe_button = tk.Button(window, text=f"網路連接", width=button_width, height=button_height, font=font_style, command=lambda: run_exe(exes[2]))
PingTest_subprocess_exe_button.grid(row=1, column=0, padx=5, pady=5)

BT_subprocess_exe_button = tk.Button(window, text=f"藍牙", width=button_width, height=button_height, font=font_style, command=lambda: run_exe(exes[0]))
BT_subprocess_exe_button.grid(row=1, column=1, padx=5, pady=5)

PingTest_subprocess_exe_button = tk.Button(window, text=f"RJ45/WiFi", width=button_width, height=button_height, font=font_style, command=lambda: run_exe(exes[1]))
PingTest_subprocess_exe_button.grid(row=1, column=2, padx=5, pady=5)


PingTest_subprocess_exe_button = tk.Button(window, text=f"USB", width=button_width, height=button_height, font=font_style, command=lambda: run_exe(exes[3]))
PingTest_subprocess_exe_button.grid(row=1, column=3, padx=5, pady=5)

PingTest_subprocess_exe_button = tk.Button(window, text=f"RS485", width=button_width, height=button_height, font=font_style, command=lambda: run_exe(exes[4]))
PingTest_subprocess_exe_button.grid(row=1, column=4, padx=5, pady=5)


result_text = scrolledtext.ScrolledText(window, width=240, height=30)
result_text.grid(row=2, column=0, columnspan=5, padx=10, pady=10)


window.grid_rowconfigure(0, weight=1)
window.grid_rowconfigure(1, weight=1)
window.grid_rowconfigure(2, weight=1)

window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1)
window.grid_columnconfigure(2, weight=1)
window.grid_columnconfigure(3, weight=1)
window.grid_columnconfigure(4, weight=1)


window.mainloop()
