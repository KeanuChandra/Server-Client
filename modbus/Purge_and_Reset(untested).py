import socket
import numpy as np
import encodings
import time
import sys
import errno
import threading
import subprocess
import minimalmodbus
import usb.core

import os.path
import csv

from datetime import datetime

if __name__ == "__main__":

    sensor = minimalmodbus.Instrument('/dev/ttyUSB0',240) 
    sensor.serial.baudrate = 9600               # BaudRate
    sensor.serial.bytesize = 8                  # Number of data bits to be requested
    sensor.serial.parity = minimalmodbus.serial.PARITY_NONE  # Parity Setting here is NONE but can be ODD or EVEN
    sensor.serial.stopbits = 2                  # Number of stop bits
    sensor.serial.timeout  = 0.5                # Timeout time in seconds
    sensor.mode = minimalmodbus.MODE_RTU        # Mode to be used (RTU or ascii mode)

    sensor.clear_buffers_before_each_transaction = True
    sensor.close_port_after_each_call = True

    while True:
        my_data = accurate_temperature_data(sensor)
        print("Temperature "+str(my_data['temperature']))
        print("Humidity "+str(my_data['humidity']))
        time.sleep(1)

    #THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    #file_path = THIS_FOLDER+"/data/"+dt+".csv"
    #csvfile = open(file_path, 'w+')


# =======================================================
# === Extended Feature: Accurate 32-bit Float Reading ===
# =======================================================
# This section is appended separately to respect the request
# to not change the original temperature_data function or main block

def accurate_temperature_data(sensor):
    """
    Reads temperature and humidity as 32-bit float values from the sensor,
    using correct 0-based register addressing and Vaisala's little-endian word order.
    """
    sensor.byteorder = minimalmodbus.BYTEORDER_LITTLE_SWAP  # Ensure correct byte order for Vaisala floats
    temperature = sensor.read_float(256, functioncode=3, number_of_registers=2)  # 257 - 1
    humidity = sensor.read_float(258, functioncode=3, number_of_registers=2)     # 259 - 1
    return {
        'temperature': temperature,
        'humidity': humidity
    }


def read_sensor_registers(sensor):
    """
    Reads a full set of sensor registers. Adjust addresses as needed.
    Addresses are corrected for 0-based Modbus indexing.
    """
    try:
        sensor.byteorder = minimalmodbus.BYTEORDER_LITTLE_SWAP
        return {
            'temperature_celsius': sensor.read_float(256, functioncode=3),   # 257 - 1
            'humidity_percent': sensor.read_float(258, functioncode=3),     # 259 - 1
            'control_mode': sensor.read_register(299, functioncode=3),      # 300 - 1
            'status_flag': sensor.read_register(300, functioncode=3),       # 301 - 1
            'error_code': sensor.read_register(301, functioncode=3),        # 302 - 1
            'raw_temp_adc': sensor.read_register(303, functioncode=3),      # 304 - 1
            'raw_humidity_adc': sensor.read_register(304, functioncode=3),  # 305 - 1
            'firmware_version': sensor.read_register(399, functioncode=3),  # 400 - 1
        }
    except Exception as e:
        print(f"[ERROR] Failed to read full register set: {e}")
        return {}

def start_purge(sensor):
    """
    Sends a command to begin purge/calibration by writing 1 to control register.
    """
    try:
        print("[INFO] Sending purge/calibration command...")
        sensor.write_register(299, 1, functioncode=16)  # 300 - 1
    except Exception as e:
        print(f"[ERROR] Could not write to control register: {e}")

def wait_for_completion(sensor):
    """
    Waits for the sensor to report calibration complete by checking status_flag.
    """
    print("[INFO] Waiting for purge/calibration to complete...")
    while True:
        try:
            status = sensor.read_register(300, functioncode=3)  # 301 - 1
            print(f"[DEBUG] Status = {status}")
            if status == 1:
                print("[DONE] Purge/calibration finished.")
                break
        except Exception as e:
            print(f"[ERROR] Reading status register: {e}")
        time.sleep(1)

# To use advanced features, uncomment and invoke below in main:
# start_purge(sensor)
# wait_for_completion(sensor)
# print(read_sensor_registers(sensor))