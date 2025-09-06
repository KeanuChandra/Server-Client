import socket
import numpy as np
import encodings
import time
import sys
import errno
import threading
import subprocess
import minimalmodbus


import os.path
import csv
from datetime import datetime


def temperature_data(sensor):
    """Reads temperature and humidity from the sensor."""
    try:

        temperature_raw = sensor.read_register(257, functioncode=3)
        humidity_raw = sensor.read_register(256, functioncode=3)
        

        temperature = temperature_raw / 100.0
        humidity = humidity_raw / 100.0
        
        return {
            'temperature': temperature,
            'humidity': humidity
        }
    except (IOError, ValueError) as e:
        print(f"Error reading from sensor: {e}")
        return None


if __name__ == "__main__":
    try:
        sensor = minimalmodbus.Instrument('/dev/ttyUSB0', 240) 
    except serial.serialutil.SerialException as e:
        print(f"Error: Could not open port /dev/ttyUSB0. Please check connection. Details: {e}")
        sys.exit(1)
        

    sensor.serial.baudrate = 9600
    sensor.serial.bytesize = 8
    sensor.serial.parity = minimalmodbus.serial.PARITY_NONE
    sensor.serial.stopbits = 2
    sensor.serial.timeout = 0.5  
    sensor.mode = minimalmodbus.MODE_RTU

    sensor.clear_buffers_before_each_transaction = True
    sensor.close_port_after_each_call = True
    

    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)


    current_date_str = datetime.now().strftime('%Y-%m-%d')
    file_path = os.path.join(data_dir, f"sensor_data_{current_date_str}.csv")
    

    file_exists = os.path.isfile(file_path)

    fieldnames = ['timestamp', 'temperature', 'humidity']

    # --- Main Loop to Read Data and Write to CSV ---
    try:
        with open(file_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()

            while True:
                my_data = temperature_data(sensor)
                
                if my_data:
                    print(f"Temperature: {my_data['temperature']}°C")
                    print(f"Humidity: {my_data['humidity']}%")
                    
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    row_to_write = {
                        'timestamp': timestamp,
                        'temperature': my_data['temperature'],
                        'humidity': my_data['humidity']
                    }

                    writer.writerow(row_to_write)

                    csvfile.flush()

                time.sleep(1)

    except KeyboardInterrupt:
        print("\nProgram stopped by user. Exiting.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
