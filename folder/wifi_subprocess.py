import subprocess

def connect(name, path):
    """
    使用 Powershell 指令設定並連線指定的 Wi-Fi Profile。
    執行成功則回傳 'OK'，失敗則回傳 'Failed'。
    """
    # 建立要執行的 Powershell 指令
    combined = f'''
        $currentPolicy = Get-ExecutionPolicy
        Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

        $profilePath = "{path}"
        netsh wlan add profile filename=$profilePath
        netsh wlan connect name="{name}"

        Set-ExecutionPolicy -ExecutionPolicy $currentPolicy -Scope Process -Force
    '''

    try:
        # 執行 Powershell 指令，若發生錯誤將進入 except 區塊
        subprocess.run(
            ['powershell', '-Command', combined],
            capture_output=True, text=True, check=True
        )
        print('Wi-Fi Set Success\nConnecting.....')
        return 'OK'
    except subprocess.CalledProcessError as e:
        # 印出錯誤訊息，並回傳 'Failed'
        print(e.stdout)
        print('\nWi-Fi Set Failed')
        return 'Failed'


if __name__ == "__main__":
    wifi_name = 'WM_Tester'
    wifi_path = f'.\\Wi-Fi-{wifi_name}.xml'

    # 呼叫連線函式
    result = connect(wifi_name, wifi_path)

    # 將執行結果寫入報告檔案
    with open("report.txt", 'a', encoding='utf-8') as file:
        file.write(f'Wi-Fi Set {result}\n')
