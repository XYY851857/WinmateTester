import serial
import time


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


def receive_data():
    try:
        no_data_count = 0
        fail_count = 0
        run_count = 0
        data_received = None
        ser.write(bytes.fromhex('01 04 00 01 00 01 60 0A'))
        time.sleep(5)
        for _ in range(0, 20):
            data_received = None
            run_count += 1
            ser.write(bytes.fromhex('01 04 00 01 00 01 60 0A'))
            time.sleep(0.5)
            if ser.in_waiting > 0:
                data_received = ser.read(ser.in_waiting).hex().upper()
                data_CRC = calculate_crc(data_received[0:10]).hex().upper()
                if data_CRC != data_received[10:14]:
                    fail_count += 1
            if data_received is None:
                no_data_count += 1
            if fail_count > 0 or no_data_count > 0:
                break
        if no_data_count == 0 and fail_count == 0:
            print('\nRS485: PASS')
        else:
            print(f'\nRS485: Failed, LOSS Rate: {((fail_count + no_data_count)/run_count)*100:.2f} %')
    except Exception as e:
        print('RS485: ERROR, Try Again')
        with open('ERROR_report.txt', 'a') as errfile:
            errfile.write(f'RS485： {e}')


if __name__ == "__main__":
    COM_PORT = 'COM1'
    BAUDRATE = 115200  # 115200
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
            receive_data()
            ser.close()

        else:
            print(f"Failed to connect to {COM_PORT}")

    except Exception as e:
        print("Error", e)
        with open('ERROR_report.txt', 'a') as errfile:
            errfile.write(f'RS485: {e}\n')

    finally:
        ser.close()
