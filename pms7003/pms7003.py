# Based on https://github.com/tomek-l/pms7003/blob/master/pms7003/pms7003.py

import serial
import logging
from binascii import hexlify

class Pms7003Exception(Exception):
    def __init__(self, msg):
        super().__init__(msg)

FRAME_START = bytes([0x42, 0x4d])
FRAME_LENGTH = 30

FRAME_LABELS = [
    'pm1_0cf1',
    'pm2_5cf1',
    'pm10cf1',
    'pm1_0',
    'pm2_5',
    'pm10',
    'n0_3',
    'n0_5',
    'n1_0',
    'n2_5',
    'n5_0',
    'n10',
]

class Pms7003(object):

    def __init__(self, serial_device):
        self._logger = logging.getLogger('Pms7003')
        self._serial = serial.Serial(port=serial_device, baudrate=9600, bytesize=serial.EIGHTBITS,
                                     parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=2)

    def _get_frame(self):
        with self._serial as s:
            s.read_until(FRAME_START)
            frame = list(s.read(FRAME_LENGTH))
        if not self._is_valid_frame(frame):
            raise Pms7003Exception('Invalid frame')
        return frame

    def _parse_frame(self, frame):
        data = [frame[i] << 8 | frame[i+1] for i in range(0, len(frame), 2)]
        return data[1:-1]

    def _is_valid_frame(self, frame):
        if len(frame) != FRAME_LENGTH:
            self._logger.error('Invalid frame length {0}, data: 0x{1}'.format(len(frame), hexlify(frame)))
            return False
        checksum = frame[-2] << 8 | frame[-1]
        if checksum != sum(frame[:-2]) + sum(FRAME_START):
            self._logger.error('Invalid checksum {0:#0X}, data: 0x{1}'.format(checksum, hexlify(frame)))
            return False
        return True

    def read_measure(self):
        frame = self._get_frame()
        data = self._parse_frame(frame)
        return {FRAME_LABELS[i]: data[i] for i in range(0, len(FRAME_LABELS))}

    def close(self):
        if self._serial.is_open:
            self._serial.close()