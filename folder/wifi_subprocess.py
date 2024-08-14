import subprocess
import os
import sys
import time


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


if __name__ == "__main__":
    name = 'WM_Tester'
    path = f'.\\Wi-Fi-{name}.xml'
    path2 = resource_path(f'Wi-Fi-{name}.xml')


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

    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print('\nConnect Failed')
    input('Press Enter to Exit')
