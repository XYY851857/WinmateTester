import serial
from datetime import datetime
import time

# pyinstaller --clean --onefile --hidden-import=serial .\RS485.py


def calculate_crc(data):
    data = bytes.fromhex(data)
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, byteorder='little')


def decode_modbus_response(response):
    if len(response) != 14:
        return "RS485接收到的數據長度不正確"

    data_bytes = f'{response[6:8]} {response[8:10]}'
    temperature_raw = int.from_bytes(bytes.fromhex(data_bytes), byteorder='big') * 0.01
    return temperature_raw


def receive_data():
    no_data_count = 0
    received_text = 'N/A'
    fail_count = 0
    run_count = 0
    for _ in range(0, 20):
        run_count += 1
        ser.write(bytes.fromhex('01 04 00 01 00 01 60 0A'))
        time.sleep(0.25)
        if ser.in_waiting > 0:
            data_received = ser.read(ser.in_waiting).hex().upper()
            no_data_count = 0
            data_CRC = calculate_crc(data_received[0:10]).hex().upper()
            if data_CRC != data_received[10:14]:
                check_result = 'Failed'
                fail_count += 1
            decode_temp = decode_modbus_response(data_received)
            print(f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]}: {round(decode_temp, 2)}")
        else:
            if no_data_count >= 3:
                received_text = f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]}: No data\n"
                print(received_text)
        if fail_count >= 3:
            print(f'ERROR Rate: {(fail_count/run_count)*100} %')
            with open('report.txt', 'a') as errfile:
                errfile.write(f'RS485:Failed')

        time.sleep(0.75)


if __name__ == "__main__":
    COM_PORT = 'COM1'
    BAUDRATE = 115200  # 9600
    BYTESIZE = serial.EIGHTBITS  # 8
    PARITY = serial.PARITY_NONE  # NONE
    STOPBITS = serial.STOPBITS_ONE  # 1

    ser = serial.Serial(
        port=COM_PORT,
        baudrate=BAUDRATE,
        bytesize=BYTESIZE,
        parity=PARITY,
        stopbits=STOPBITS
    )


    try:
        if ser.is_open:
            print(f"connected to {COM_PORT}")  # 以下放接續動作
            receive_data()
            with open('report.txt', 'a') as file:
                file.write(f'RS485: PASS')
            ser.close()
            quit()

        else:
            print(f"Failed to connect to {COM_PORT}")
            with open('report.txt', 'a') as file:
                file.write(f'RS485: Failed')

    except Exception as e:
        print("Error", e)
        with open('ERROR_report.txt', 'a') as errfile:
            file.write(f'RS485: {e}\n')

    finally:
        ser.close()
