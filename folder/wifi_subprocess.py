import subprocess
import os
import sys
import time


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


if __name__ == "__main__":
    path = '.\\Wi-Fi-TP-Link_C51A.xml'
    path2 = resource_path('Wi-Fi-TP-Link_C51A.xml')
    name = 'TP-Link_C51A'


    combined = f'''
                $currentPolicy = Get-ExecutionPolicy
                Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

                $profilePath = "{path2}"
                netsh wlan add profile filename=$profilePath
                netsh wlan connect name="{name}"

                Set-ExecutionPolicy -ExecutionPolicy $currentPolicy -Scope Process -Force

                '''


    try:
        result = subprocess.run(['powershell', '-Command', combined], capture_output=True, text=True, check=True)
        print('Result: Wi-Fi Set Success\nConnecting.....')
        time.sleep(5)
        ping_result = subprocess.run(['powershell', '-Command', 'ping -S 192.168.2.102 192.168.2.1'], capture_output=True, text=True)
        ch_keyword = '=32'
        ch_start_pos = ping_result.stdout.find(ch_keyword)
        if ch_start_pos != -1:
            print('ping success')
            ch_start_pos += len(ch_keyword)
            ping_result = ping_result.stdout[ch_start_pos]
        # print(ping_result.stdout)
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print('\nConnect Failed')
    input('Press Enter to Exit')
