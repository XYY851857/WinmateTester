import subprocess
import time
import sys
import ctypes
import os
import re
import glob


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def find_latest_icpdas_editor():
    folder = r"D:\Update_Repo\ICPDAS_Editor"
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
    folder = r"D:\Update_Repo\Connecter_Launcher"
    pattern = re.compile(r"Connecter_Launcher_V(\d+)_(\d+)_(\d+)\.exe")
    candidates = []
    for file in glob.glob(os.path.join(folder, "Connecter_Launcher_V*.exe")):
        m = pattern.search(os.path.basename(file))
        if m:
            ver_tuple = tuple(int(x) for x in m.groups())
            candidates.append((ver_tuple, file))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def main():
    options = [("VNC_VxComm", "VNC_VxComm"), ("ICPDAS_Editor", "ICPDAS_Editor"), ("Connecter_Launcher", "Connecter_Launcher")]
    selection = options[0][0]  # Example selection, adjust as needed

    if not is_admin():
        print("目前權限不足，正在嘗試以管理員權限重新執行...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

    if selection == "VNC_VxComm":
        ret = subprocess.run(r"D:\VNC_VxComm.bat", shell=True)
        if ret.returncode != 0:
            print("執行 VNC_VxComm.bat 失敗")
            return
    elif selection == "ICPDAS_Editor":
        # Assuming find_latest_icpdas_editor() is defined elsewhere
        exe_path = find_latest_icpdas_editor()
        if not exe_path:
            print("找不到 ICPDAS_Editor 的執行檔")
            return
        ret = subprocess.run(f'"{exe_path}"', shell=True)
        if ret.returncode != 0:
            print(f"執行 {exe_path} 失敗")
            return
    elif selection == "Connecter_Launcher":
        exe_path = find_latest_connecter_launcher()
        if not exe_path:
            print("找不到 Connecter_Launcher 的執行檔")
            return
        ret = subprocess.run(f'"{exe_path}"', shell=True)
        if ret.returncode != 0:
            print(f"執行 {exe_path} 失敗")
            return

    subprocess.Popen(r"C:\Storage Card\Autorun.vbs", shell=True)
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
