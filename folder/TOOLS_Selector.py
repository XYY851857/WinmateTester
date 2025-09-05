import subprocess
import time
import sys
import ctypes
import os
import re
import glob
import shutil
import tkinter as tk
from typing import List


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
    folder = r"D:\S8521\Update_Repo\Connecter"
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


def run_generic_tool(name: str):
    """在 D:\\S8521\\Update_Repo\\{name} 資料夾中找到最新版本的 {name}_V*.exe 並執行"""
    base_dir = r"D:\S8521\Update_Repo"
    folder = os.path.join(base_dir, name)
    if not os.path.isdir(folder):
        print(f"資料夾 {folder} 不存在")
        return
    pattern = re.compile(fr"{re.escape(name)}_V(\d+)_(\d+)_(\d+)\.exe", re.I)
    candidates = []
    for file in glob.glob(os.path.join(folder, f"{name}_V*.exe")):
        m = pattern.search(os.path.basename(file))
        if m:
            ver_tuple = tuple(int(x) for x in m.groups())
            candidates.append((ver_tuple, file))
    if not candidates:
        print(f"{folder} 內找不到執行檔")
        return
    candidates.sort(reverse=True)
    exe_path = candidates[0][1]
    subprocess.run(f'"{exe_path}"', shell=True)


def show_selector():
    root = tk.Tk()
    root.title("請選擇要執行的項目")
    # 最大化
    root.attributes("-fullscreen", True)
    selection = tk.StringVar(value="")

    base_dir = r"D:\S8521\Update_Repo"

    def do_select(value):
        selection.set(value)
        root.quit()
    def do_exit():
        selection.set("")
        root.quit()

    btn_style = {
        "font": ("Arial", 36),
        "bg": "#f0f0f0",
        "activebackground": "#e1e1e1",
        "relief": "raised",
        "bd": 3,
    }
    frame = tk.Frame(root, bg="#ffffff")
    frame.pack(fill="both", expand=True, padx=40, pady=40)

    # 動態偵測資料夾生成按鈕
    folders: List[str] = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])
    if "VNC_VxComm" not in folders:
        folders.insert(0, "VNC_VxComm")  # 仍顯示 VNC_VxComm

    for folder_name in folders:
        tk.Button(frame,
                  text=folder_name,
                  command=lambda v=folder_name: do_select(v),
                  **btn_style).pack(side="top", fill="both", expand=True, pady=15)

    # 新增離開按鈕
    exit_btn = tk.Button(frame, text="離開", command=do_exit,
                        font=("Arial", 32, "bold"),
                        bg="#e57373", activebackground="#ffcdd2",
                        relief="raised", bd=4, fg="#ffffff", height=1)
    exit_btn.pack(side="bottom", fill="x", padx=100, pady=30)

    root.mainloop()
    result = selection.get()
    root.destroy()
    return result if result else None

def main():
    if not is_admin():
        print("目前權限不足，正在嘗試以管理員權限重新執行...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

    selection = show_selector()

    if selection is None:
        return

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
        ret = subprocess.run(f'"{dst_exe}"', shell=True)
        if ret.returncode != 0:
            print(f"執行 {dst_exe} 失敗")
            return
    else:
        # generic handler for any folder detected
        run_generic_tool(selection)

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
