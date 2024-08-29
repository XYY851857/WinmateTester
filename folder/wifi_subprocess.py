import subprocess
import os
import sys


def connect():
    try:
        result = subprocess.run(['powershell', '-Command', combined], capture_output=True, text=True, check=True)
        print('Wi-Fi Set Success\nConnecting.....')
        return 'OK'

    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print('\nWi-Fi Set Failed')
        return 'Failed'


if __name__ == "__main__":
    name = 'WM_Tester'
    path = f'.\\Wi-Fi-{name}.xml'

    combined = f'''
                $currentPolicy = Get-ExecutionPolicy
                Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

                $profilePath = "{path}"
                netsh wlan add profile filename=$profilePath
                netsh wlan connect name="{name}"

                Set-ExecutionPolicy -ExecutionPolicy $currentPolicy -Scope Process -Force

                '''

    result = connect()
    with open("report.txt", 'a') as file:
        file.write(f'Wi-Fi Set {result}\n')
