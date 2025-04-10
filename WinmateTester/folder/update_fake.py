import subprocess
import time
import sys
import ctypes


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def main():
    if not is_admin():
        print("目前權限不足，正在嘗試以管理員權限重新執行...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

    ret = subprocess.run(r"D:\VNC_VxComm.bat", shell=True)
    if ret.returncode != 0:
        print("執行 VNC_VxComm.bat 失敗")
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
    cmd = f'cmd /c "timeout /t 3 & copy /Y \"D:\\S8521\\S8521_Update\\Update.exe\" \"C:\\Storage Card\\.\""'
    subprocess.Popen(cmd, shell=True)
    subprocess.Popen(r"C:\Storage Card\Autorun.vbs", shell=True)


