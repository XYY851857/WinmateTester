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

# 執行 Relay.bat：在新的 cmd 視窗中獨立執行
bat_path = r'D:\S7215\Relay.bat'
subprocess.Popen(
    ['cmd.exe', '/c', 'start', '""', bat_path],
    shell=False,
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)
