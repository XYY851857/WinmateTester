import subprocess
import time
import sys
import ctypes
import os
import re
import glob
import shutil
import tkinter as tk
from tkinter import messagebox


def show_loading():
    loading_root = tk.Toplevel()
    loading_root.title("請稍候")
    loading_root.geometry("380x160+400+300")
    loading_root.attributes("-topmost", True)
    tk.Label(loading_root, text="啟動中.....", font=("Arial", 24)).pack(expand=True)
    loading_root.update()
    return loading_root


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def find_latest_icpdas_editor():
    folder = r"D:\S8521\Update_Repo\ICPDAS_Editor"
    pattern = re.compile(r"ICPDAS_Editor_V(\d+)_(\d+)_(\d+)\.exe")
    candidates = []
    for file in glob.glob(os.path.join(folder, "ICPDAS_Editor_V*.exe")):
        m = pattern.search(os.path.basename(file))
        if m:
            ver_tuple = tuple(int(x) for x in m.groups())
            candidates.append((ver_tuple, file))
    if not candidates:
        return None
    # 取最大版本號
    candidates.sort(reverse=True)
    return candidates[0][1]


def find_latest_connecter_launcher():
    folder = r"D:\S8521\Update_Repo\Connecter_Launcher"
    pattern = re.compile(r"Connecter_Launcher_V(\d+)_(\d+)_(\d+)\.exe")
    candidates = []
    for file in glob.glob(os.path.join(folder, "Connecter_Launcher_V*.exe")):
        m = pattern.search(os.path.basename(file))
        if m:
            ver_tuple = tuple(int(x) for x in m.groups())
            candidates.append((ver_tuple, file))
    if not candidates:
        return None, None
    candidates.sort(reverse=True)
    exe_path = candidates[0][1]
    root_folder = os.path.dirname(exe_path)
    return exe_path, root_folder



def show_selector():
    root = tk.Tk()
    root.title("請選擇要執行的項目")
    root.state("zoomed")  # 全螢幕
    selection = tk.StringVar(value="VNC_VxComm")

    def do_select(value):
        selection.set(value)
        root.quit()

    btn_style = {"font": ("Arial", 54), "width": 18, "height": 3, "padx": 24, "pady": 36}
    btns = [
        tk.Button(root, text="VNC_VxComm", command=lambda: do_select("VNC_VxComm"), **btn_style),
        tk.Button(root, text="ICPDAS_Editor", command=lambda: do_select("ICPDAS_Editor"), **btn_style),
        tk.Button(root, text="Connecter_Launcher", command=lambda: do_select("Connecter_Launcher"), **btn_style),
    ]
    for b in btns:
        b.pack(pady=40, padx=80, fill="x")

    root.mainloop()
    result = selection.get()
    root.destroy()
    return result

def main():
    if not is_admin():
        print("目前權限不足，正在嘗試以管理員權限重新執行...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

    selection = show_selector()

    if selection == "VNC_VxComm":
        ret = subprocess.run(r"D:\VNC_VxComm.bat", shell=True)
        if ret.returncode != 0:
            print("執行 VNC_VxComm.bat 失敗")
            return
    elif selection == "ICPDAS_Editor":
        exe_path = find_latest_icpdas_editor()
        if not exe_path:
            print("找不到 ICPDAS_Editor 的執行檔")
            return
        ret = subprocess.run(f'"{exe_path}"', shell=True)
        if ret.returncode != 0:
            print(f"執行 {exe_path} 失敗")
            return
    elif selection == "Connecter_Launcher":
        exe_path, src_folder = find_latest_connecter_launcher()
        if not exe_path or not src_folder:
            print("找不到 Connecter_Launcher 的執行檔")
            return
        dst_folder = r"C:\Connecter"
        # 先刪除目標再複製
        if os.path.exists(dst_folder):
            shutil.rmtree(dst_folder)
        shutil.copytree(src_folder, dst_folder)
        # 複製完成後再搜尋 C:\Connecter 最新 exe
        pattern = re.compile(r"Connecter_Launcher_V(\d+)_(\d+)_(\d+)\.exe")
        candidates = []
        for file in glob.glob(os.path.join(dst_folder, "Connecter_Launcher_V*.exe")):
            m = pattern.search(os.path.basename(file))
            if m:
                ver_tuple = tuple(int(x) for x in m.groups())
                candidates.append((ver_tuple, file))
        if not candidates:
            print("C:\\Connecter 裡找不到 Connecter_Launcher 執行檔")
            return
        candidates.sort(reverse=True)
        dst_exe = candidates[0][1]
        # 顯示啟動中
        root = tk.Tk()
        root.withdraw()
        loading = show_loading()
        ret = subprocess.run(f'"{dst_exe}"', shell=True)
        loading.destroy()
        root.destroy()
        if ret.returncode != 0:
            print(f"執行 {dst_exe} 失敗")
            return

    return


if __name__ == '__main__':
    try:
        main()
        time.sleep(3)
        subprocess.run(['powershell', '-Command', 'Stop-Process -Name "winvnc" -Force'],  capture_output=True, text=True, check=True)
        time.sleep(3)
    except:
        pass
    subprocess.Popen(r"C:\Storage Card\Autorun.vbs", shell=True)
