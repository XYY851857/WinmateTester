import subprocess


if __name__ == "__main__":
    device_name = 'Bluetooth Mouse M336/M337/M535'
    pin_code = ''  # 若不需要可留空

    combined = f'''
                .\\btpair.exe -n "{device_name}" -p "{pin_code}"                
                '''


    try:
        result = subprocess.run(['powershell', '-Command', combined], capture_output=True, text=True, check=True)
        print(f'Result: Bluetooth Connect Success')
        if result.stderr:
            print(f'Error: \n {result.stderr}')
    except subprocess.CalledProcessError as e:  # ' System Error.  Code: 1244.使用者尚未被驗證，因此無法執行所要求的操作。'
        keyword = 'Code: '
        start_pos = e.stderr.find(keyword)
        if start_pos != -1:
            start_pos += len(keyword)
            result = e.stderr[start_pos:start_pos + 4]
            if result == '1244':  # 因無法操作OS故用error code判斷 1244:可連接但OS未點擊接收
                print('Result: Bluetooth OK')
            elif result[0:3] == "258":  # 連接逾時
                print('Result: Connect Timeout')
            elif result[0:2] == '31':  # 已經連上，無法再次配對，判斷爲success
                print('Result: Connected')
            else:
                print(f"Error:\n {e.stderr}")
        print(e.stderr)
    # input('Press Enter to Exit')
