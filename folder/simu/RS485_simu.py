import serial
import time

def calculate_crc(data_hex):
    """
    計算 Modbus RTU 通訊使用的 16-bit CRC (多項式 0xA001)。
    接收參數為十六進位字串 (不含 0x 前綴)，回傳兩個位元組(小端序)。
    """
    data_bytes = bytes.fromhex(data_hex)  # 將十六進位字串轉成位元組
    crc = 0xFFFF
    for byte in data_bytes:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, byteorder='little')

def receive_data():
    """
    進行 RS485 讀寫測試：
    1. 先寫入固定指令並等待 5 秒（第一次等待較久，以應對部分裝置較慢的首次回應）。
    2. 接著重複最多 20 次寫入與讀取，每次讀取資料後檢查 CRC。
    3. 若發生任何一次 CRC 錯誤或無法讀到資料，即提早結束測試並顯示失敗率。
    4. 若 20 次都成功，顯示 PASS。
    """
    try:
        # 將 Modbus 讀取指令先轉為 bytes，避免每次都重複轉換
        # 01 04 00 01 00 01 60 0A 說明：
        #   01 = 裝置位址 (Slave Address)
        #   04 = Function Code (Read Input Registers)
        #   00 01 = 起始暫存器位址 (High, Low)
        #   00 01 = 要讀取暫存器個數 (High, Low)
        #   60 0A = CRC (小端序)
        modbus_cmd = bytes.fromhex('01 04 00 01 00 01 60 0A')

        no_data_count = 0
        fail_count = 0
        run_count = 0

        # 第一次發送後，等待較長時間 5 秒
        ser.write(modbus_cmd)
        time.sleep(5)

        # 連續最多執行 20 次測試
        for _ in range(20):
            run_count += 1

            # 寫入指令後稍等 0.5 秒
            ser.write(modbus_cmd)
            time.sleep(0.5)

            data_received = None
            if ser.in_waiting > 0:
                # 讀取目前序列阜緩衝區所有資料
                raw_data = ser.read(ser.in_waiting)
                data_received = raw_data.hex().upper()

                # 通常應該收到 7 bytes (對應 14 個 hex 字元)
                # 前 5 bytes (10 個 hex) 是回應的地址、功能碼、資料等
                # 後 2 bytes (4 個 hex) 是 CRC
                if len(data_received) >= 14:
                    data_crc_calc = calculate_crc(data_received[0:10]).hex().upper()
                    data_crc_recv = data_received[10:14]
                    if data_crc_calc != data_crc_recv:
                        fail_count += 1
                else:
                    # 若資料長度不足，等同 CRC 無法比對
                    fail_count += 1

            else:
                # 若序列阜緩衝區沒有資料，代表未讀到回應
                no_data_count += 1

            # 只要發現失敗或未讀到資料，就提早結束
            if fail_count > 0 or no_data_count > 0:
                break

        # 統計結果
        if no_data_count == 0 and fail_count == 0:
            print('\nRS485: PASS')
        else:
            loss_rate = ((fail_count + no_data_count) / run_count) * 100
            print(f'\nRS485: PASS, LOSS Rate: {loss_rate:.2f} %')

    except Exception as e:
        print('RS485: ERROR, Try Again')
        # 可根據需求將錯誤寫入檔案：
        # with open('ERROR_report.txt', 'a') as errfile:
        #     errfile.write(f'RS485： {e}')

if __name__ == "__main__":
    COM_PORT = 'COM1'
    BAUDRATE = 115200   # 設定鮑率
    BYTESIZE = serial.EIGHTBITS  # 資料位元：8
    PARITY = serial.PARITY_NONE  # 無同位檢查
    STOPBITS = serial.STOPBITS_ONE  # 停止位元：1

    # 開啟序列阜
    ser = serial.Serial(
        port=COM_PORT,
        baudrate=BAUDRATE,
        bytesize=BYTESIZE,
        parity=PARITY,
        stopbits=STOPBITS
    )

    try:
        if ser.is_open:
            receive_data()
            ser.close()
        else:
            print(f"Failed to connect to {COM_PORT}")

    except Exception as e:
        print("Error", e)
        # with open('ERROR_report.txt', 'a') as errfile:
        #     errfile.write(f'RS485: {e}\n')

    finally:
        if ser.is_open:
            ser.close()
