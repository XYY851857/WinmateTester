import serial
from datetime import datetime
import time


def calculate_crc(data):  # CRC計算
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


def receive_data():
    no_data_count = 0
    received_text = 'N/A'
    while True:
        if ser.in_waiting > 0:
            data_received = ser.read(ser.in_waiting).hex().upper()
            received_text = f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]}: {' '.join(data_received[i:i + 2] for i in range(0, len(data_received), 2))}\n"
            no_data_count = 0
            # time.sleep(0.40)
        else:
            if no_data_count >= 3:
                received_text = f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]}: No data\n"
                # time.sleep(0.40)
        time.sleep(0.5)


if __name__ == "__main__":
    COM_PORT = 'COM3'
    BAUDRATE = 9600  # 9600
    BYTESIZE = serial.EIGHTBITS  # 8
    PARITY = serial.PARITY_EVEN  # EVEN
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

        else:
            print(f"Failed to connect to {COM_PORT}")

    except Exception as e:
        print("Error", e)

    finally:
        ser.close()
