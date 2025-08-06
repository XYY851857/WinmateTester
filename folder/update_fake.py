import subprocess
import ctypes

# 自己這支 Python 視窗最小化
try:
    SW_MINIMIZE = 6
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)
except Exception:
    pass  # 忽略非 Windows

# 執行 Relay.bat，最小化新開啟的視窗
si = subprocess.STARTUPINFO()
si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
si.wShowWindow = 6  # SW_MINIMIZE

subprocess.Popen([r'D:\S8521\Relay.bat'], shell=True, startupinfo=si)
