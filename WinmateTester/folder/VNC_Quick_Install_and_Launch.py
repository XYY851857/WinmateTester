import shutil
import psutil
import os
import subprocess
from datetime import datetime
from tkinter import messagebox
import tkinter as tk  # 新增，用於建立數字鍵盤視窗

def get_mac_address_by_name():
    for interface, addrs in psutil.net_if_addrs().items():
        if interface == "乙太網路 2":
            for addr in addrs:
                if addr.family == psutil.AF_LINK:  # AF_LINK 表示 MAC 地址
                    return addr.address
    return "Unknown"

def addation_command():
    if os.path.exists('.\\addition_command.txt'):
        try:
            with open('.\\addition_command.txt', 'r', encoding='UTF-8') as file:
                for line in file:
                    command = line.strip()  # 移除空白與換行符
                    if command:  # 如果不是空行，執行指令
                        result = subprocess.run(['powershell', '-Command', command],
                                                capture_output=True, text=True,
                                                check=True, shell=True)
                        print('插件執行成功')
        except subprocess.CalledProcessError as e:
            messagebox.showinfo("錯誤", "防火牆設定失敗，請重試")
            quit()

def vnc_install():
    if not os.path.exists('C:\\Program Files (x86)\\apps'):
        os.makedirs('C:\\Program Files (x86)\\apps', exist_ok=True)

    shutil.copy('.\\VNC\\apps\\UltraVNC.ini', 'C:\\Program Files (x86)\\apps')
    shutil.copy('.\\VNC\\apps\\winvnc.exe', 'C:\\Program Files (x86)\\apps')
    # shutil.copy('.\\AutoRun.vbs', 'C:\\Storage Card')

    try:
        subprocess.run(['powershell', '-Command', 'start "C:\\Program Files (x86)\\apps\\winvnc.exe"'],
                       capture_output=True, text=True, check=True)
        subprocess.run(['powershell', '-Command',
                        'netsh interface ip set address name="乙太網路 2" static 192.168.111.111 255.255.0.0'],
                       capture_output=True, text=True, check=True)
    except:
        messagebox.showinfo("自啓動失敗", "請手動開啓C:\\Program Files (x86)\\apps\\winvnc.exe，並測試連線")
        quit()

def numeric_keypad():
    """
    建立一個數字鍵盤視窗，供使用者輸入號碼。
    使用者點擊 OK 後，將回傳輸入的數字字串。
    """
    user_input = ""  # 儲存使用者輸入的號碼

    def on_digit(digit):
        nonlocal user_input
        user_input += digit
        entry_var.set(user_input)

    def on_clear():
        nonlocal user_input
        user_input = ""
        entry_var.set(user_input)

    def on_del():
        nonlocal user_input
        user_input = user_input[:-1]
        entry_var.set(user_input)

    def on_ok():
        root.destroy()  # 關閉鍵盤視窗

    root = tk.Tk()
    root.title("請輸入號碼")

    entry_var = tk.StringVar()
    entry = tk.Entry(root, textvariable=entry_var, font=("Arial", 24), justify="center")
    entry.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

    # 建立數字鍵盤按鍵 (排列方式：第一列 7,8,9；第二列 4,5,6；第三列 1,2,3；第四列: Clear,0,Del)
    buttons = [
        ('7', 1, 0), ('8', 1, 1), ('9', 1, 2),
        ('4', 2, 0), ('5', 2, 1), ('6', 2, 2),
        ('1', 3, 0), ('2', 3, 1), ('3', 3, 2),
        ('Clear', 4, 0), ('0', 4, 1), ('Del', 4, 2),
    ]

    for (text, row, col) in buttons:
        if text.isdigit():
            action = lambda x=text: on_digit(x)
        elif text == 'Clear':
            action = on_clear
        elif text == 'Del':
            action = on_del
        btn = tk.Button(root, text=text, command=action, font=("Arial", 18), width=5, height=2)
        btn.grid(row=row, column=col, padx=5, pady=5)

    # 建立 OK 按鍵，置中並橫跨三個行
    ok_button = tk.Button(root, text="OK", command=on_ok, font=("Arial", 18), width=16, height=2)
    ok_button.grid(row=5, column=0, columnspan=3, padx=5, pady=10)

    root.mainloop()
    return user_input


if __name__ == "__main__":
    state = ''
    try:
        subprocess.run(['powershell', '-Command', 'Stop-Process -Name "winvnc" -Force'],
                       capture_output=True, text=True, check=True)
        addation_command()
        vnc_install()
    except:
        print('已安裝')
        state = 'Duplicate'
        pass

    # 呼叫數字鍵盤函數，取得使用者輸入的號碼
    user_number = numeric_keypad()
    # 寫入記錄檔，將時間、MAC 與使用者輸入的號碼一併記錄
    with open(".\\VNC\\VNC_install_log.txt", 'a') as file:
        mac_address = get_mac_address_by_name()
        current_time = datetime.now().strftime("%Y%m%d:%H%M%S")
        file.write(f'{current_time}: {mac_address} Number: {user_number} Success. {state}\n')
    messagebox.showinfo("成功", "安裝完成請測試VNC連線\n"
                               "IP:       192.168.111.111\n"
                               "Mask:     255.255.0.0\n"
                               "Gateway:  None")
