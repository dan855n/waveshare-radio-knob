#!/usr/bin/env python3
"""Read SDR-Control's local Hamlib CAT frequency and update Dan's USB dial.
Only sends `f` (read frequency) to the CAT server. Never sends radio controls.
"""
import argparse
import json
import logging
import signal
import socket
import time
from pathlib import Path
import serial
from serial.tools import list_ports

ROOT = Path(__file__).resolve().parent
STATUS = ROOT / 'status.json'
DEVICE_SERIAL = ''
RUNNING = True


def parse_frequency(line):
    text = line.decode('ascii').strip()
    if not text.isdecimal():
        raise ValueError('CAT did not return a frequency')
    hz = int(text)
    if not 0 < hz <= 999999999:
        raise ValueError('Frequency outside display range')
    return hz


def write_status(**values):
    values['updated_at'] = time.time()
    temporary = STATUS.with_suffix('.tmp')
    temporary.write_text(json.dumps(values, indent=2) + '\n')
    temporary.replace(STATUS)


def open_dial():
    for port in list_ports.comports():
        if (port.serial_number or '').upper() == DEVICE_SERIAL:
            device = serial.Serial(None, 115200, timeout=0, write_timeout=1)
            device.dtr = True
            device.rts = False
            device.port = port.device
            device.open()
            return device
    raise OSError('Radio knob not connected')


def stop(*_):
    global RUNNING
    RUNNING = False


def main():
    global DEVICE_SERIAL
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True, help='USB serial number of your knob (not the device path)')
    args = parser.parse_args()
    DEVICE_SERIAL = args.serial.upper()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    previous_error = None
    while RUNNING:
        device = None
        try:
            device = open_dial()
            with socket.create_connection(('127.0.0.1', 4532), timeout=1) as cat:
                cat.settimeout(1)
                with cat.makefile('rb') as response:
                    logging.info('Connected to radio frequency server and USB dial')
                    previous_error = None
                    last_status = 0
                    buffer = b''
                    acknowledgement = ''
                    while RUNNING:
                        cat.sendall(b'f\n')
                        hz = parse_frequency(response.readline(64))
                        device.write(f'FREQ {hz}\n'.encode('ascii'))
                        now = time.monotonic()
                        if now - last_status >= 2:
                            device.write(b'STATUS\n')
                            last_status = now
                        buffer += device.read(4096)
                        while b'\n' in buffer:
                            line, buffer = buffer.split(b'\n', 1)
                            if line.startswith(b'RADIO_DIAL '):
                                acknowledgement = line.decode('ascii', errors='replace').strip()
                        if len(buffer) > 8192:
                            buffer = b''
                        write_status(state='connected', frequency_hz=hz, device=device.port,
                                     firmware_status=acknowledgement)
                        time.sleep(0.2)
        except (OSError, ValueError, UnicodeError, serial.SerialException) as error:
            message = str(error)
            if message != previous_error:
                logging.info('Waiting: %s', message)
                previous_error = message
            write_status(state='waiting', reason=message)
            time.sleep(1)
        finally:
            if device is not None:
                device.close()
    write_status(state='stopped')


if __name__ == '__main__':
    main()
