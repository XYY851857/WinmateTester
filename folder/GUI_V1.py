import os.path
import time
import tkinter as tk
from tkinter import scrolledtext, font
import subprocess
import threading
from collections import Counter

keywords = ['fail', 'Fail', 'ERROR']


def start_all():
    ping()
    wr()
    rs485()
    bt()


def start_all_thread():
    threading.Thread(target=bt).start()
    threading.Thread(target=ping).start()
    threading.Thread(target=rs485).start()
    threading.Thread(target=wr).start()


def BT_thread():
    threading.Thread(target=bt).start()


def Ping_thread():
    threading.Thread(target=ping).start()


def WR_thread():
    threading.Thread(target=wr).start()


def RS485_thread():
    threading.Thread(target=rs485).start()


def display_result(text):
    result_text.insert(tk.END, text + "\n")
    result_text.see(tk.END)


def bt():
    BT_subprocess_exe_button.config(bg='yellow')
    display_result('藍牙: Testing...')
    try:
        result = subprocess.run(f'.\\new\\BT_subprocess.exe', capture_output=True, text=True)
        output = result.stdout
    except Exception as e:
        output = str(e)
    if 'PASS' in output:
        BT_subprocess_exe_button.config(bg='green')
    else:
        BT_subprocess_exe_button.config(bg='red')
    if os.path.exists('BT_report.txt'):
        os.remove('BT_report.txt')
    return display_result(output)


def ping():
    PingTest_subprocess_exe_button.config(bg='yellow')
    display_result('RJ45/Wi-Fi: Testing...')
    try:
        result = subprocess.run(f'.\\new\\PingTest_subprocess.exe', capture_output=True, text=True)
        output = result.stdout
    except Exception as e:
        output = str(e)
    if 'PASS' in output:
        PingTest_subprocess_exe_button.config(bg='green')
    else:
        PingTest_subprocess_exe_button.config(bg='red')
    return display_result(output)

def wr():
    WR_subprocess_exe_button.config(bg='yellow')
    display_result('USB: Testing...')
    try:
        result = subprocess.run(f'.\\new\\WR_subprocess.exe', capture_output=True, text=True)
        output = result.stdout
    except Exception as e:
        output = str(e)
    if 'PASS' in output:
        WR_subprocess_exe_button.config(bg='green')
    else:
        WR_subprocess_exe_button.config(bg='red')
    return display_result(output)


def rs485():
    RS485_subprocess_exe_button.config(bg='yellow')
    display_result('RS485: Testing...')
    try:
        result = subprocess.run(f'.\\new\\RS485.exe', capture_output=True, text=True)
        output = result.stdout
    except Exception as e:
        output = str(e)
    # with open('485_report.txt', 'r') as file:
    #     report_data = file
    print(output)
    if 'PASS' in output:
        RS485_subprocess_exe_button.config(bg='green')
    else:
        RS485_subprocess_exe_button.config(bg='red')
    return display_result(output)
    pass


window = tk.Tk()
window.title("WinMate控制器功能測試V1.0")
window.state('zoomed')
font_style = font.Font(size=20)
start_button = tk.Button(window, text="全部啟動", width=140, height=3, command=start_all_thread, font=font_style)
start_button.grid(row=0, column=0, columnspan=5, pady=10)

exes = ['.\\new\\BT_subprocess.exe', '.\\new\\PingTest_subprocess.exe', '.\\new\\WR_subprocess.exe',
        '.\\new\\RS485.exe']
button_width = 23
button_height = 3

BT_subprocess_exe_button = tk.Button(window, text=f"藍牙", width=button_width, height=button_height, font=font_style,
                                     command=BT_thread)
BT_subprocess_exe_button.grid(row=1, column=0, padx=5, pady=5)  # 藍牙測試按鈕

PingTest_subprocess_exe_button = tk.Button(window, text=f"RJ45/WiFi", width=button_width, height=button_height,
                                           font=font_style, command=Ping_thread)
PingTest_subprocess_exe_button.grid(row=1, column=1, padx=5, pady=5)  # WiFi設定及ping測試

WR_subprocess_exe_button = tk.Button(window, text=f"USB", width=button_width, height=button_height, font=font_style,
                                     command=WR_thread)
WR_subprocess_exe_button.grid(row=1, column=2, padx=5, pady=5)  # USB讀寫測試

RS485_subprocess_exe_button = tk.Button(window, text=f"RS485", width=button_width, height=button_height,
                                        font=font_style, command=RS485_thread)
RS485_subprocess_exe_button.grid(row=1, column=3, padx=5, pady=5)  # RS485測試

result_text = scrolledtext.ScrolledText(window, width=240, height=30, font=font_style)  # 建立輸出框
result_text.grid(row=2, column=0, columnspan=5, padx=10, pady=10)

window.grid_rowconfigure(0, weight=0)  # 權重設定
window.grid_rowconfigure(1, weight=0)
window.grid_rowconfigure(2, weight=1)

window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1)
window.grid_columnconfigure(2, weight=1)
window.grid_columnconfigure(3, weight=1)
window.grid_columnconfigure(4, weight=1)


window.mainloop()
