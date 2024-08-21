import serial
from datetime import datetime
import time


def decode_modbus_response(response):
    if len(response) != 14:
        return "RS485接收到的數據長度不正確"

    data_bytes = f'{response[6:8]} {response[8:10]}'
    temperature_raw = int.from_bytes(bytes.fromhex(data_bytes), byteorder='big') * 0.01
    return temperature_raw


def receive_data():
    no_data_count = 0
    received_text = 'N/A'
    for _ in range(0, 500000):
        ser.write(bytes.fromhex('01 04 00 01 00 01 60 0A'))
        time.sleep(0.25)
        if ser.in_waiting > 0:
            data_received = ser.read(ser.in_waiting).hex().upper()
            no_data_count = 0
            decode_temp = decode_modbus_response(data_received)
            print(f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]}: {round(decode_temp, 2)}")
        else:
            if no_data_count >= 3:
                received_text = f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]}: No data\n"
                print(received_text)

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
            with open('485_report.txt', 'a') as file:
                file.write(f'Success: {COM_PORT}')
            receive_data()

        else:
            print(f"Failed to connect to {COM_PORT}")
            with open('RS485_report.txt', 'a') as file:
                file.write(f'Failed: {COM_PORT}')

    except Exception as e:
        print("Error", e)
        with open('485_report.txt', 'a') as file:
            file.write(f'Failed: {e}')

    finally:
        ser.close()
