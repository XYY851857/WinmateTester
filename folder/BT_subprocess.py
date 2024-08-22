import subprocess


def pair():
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
                return 'PASS'
            elif result[0:3] == "258":  # 連接逾時
                print('Result: Connect Timeout')
                return 'Failed'
            elif result[0:2] == '31':  # 已經連上，無法再次配對，判斷爲success
                print('Result: Connected')
                return 'PASS'
            else:
                print(f"Result: Error:\n {e.stderr}")
        print(f"Result: ERROR\n{e.stderr}")
        with open('ERROR_report.txt', 'a') as errfile:
            errfile.write(f'BT_subprocess.py:  {e.stderr}\n')
        return f'ERROR\n{e.stderr}'


if __name__ == "__main__":
    device_name = 'BT3.0 Mouse'
    pin_code = ''  # 若不需要可留空

    combined = f'''
                .\\btpair.exe -n "{device_name}" -p "{pin_code}"                
                '''

    result = pair()
    with open("report.txt", 'a') as file:
        file.write(f'Bluetooth: {result}\n')



