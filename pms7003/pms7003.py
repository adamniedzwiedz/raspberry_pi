# Based on https://github.com/tomek-l/pms7003/blob/master/pms7003/pms7003.py

import sys
import serial
import struct
import logging
from collections import OrderedDict

class Pms7003Exception(Exception):
    def __init__(self, msg):
        super().__init__(msg)

if sys.version_info > (3, 0):
    FRAME_START = bytes([0x42, 0x4d])
else:
    FRAME_START = '\x42\x4d'

FRAME_START_SUM = 0x42 + 0x4d
FRAME_LENGTH = 30

FRAME_FORMAT = '>{0}'.format('B' * FRAME_LENGTH)
DATA_LABELS = [
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
            frame = struct.unpack(FRAME_FORMAT, s.read(FRAME_LENGTH))
        if not self._is_valid_frame(frame):
            raise Pms7003Exception('Invalid frame')
        return frame

    def _parse_frame(self, frame):
        data = [frame[i] << 8 | frame[i+1] for i in range(0, len(frame), 2)]
        return data[1:-1]

    def _is_valid_frame(self, frame):
        if len(frame) != FRAME_LENGTH:
            self._logger.error('Invalid frame length {0}, data: {1}'.format(len(frame), frame))
            return False
        checksum = frame[-2] << 8 | frame[-1]
        if checksum != sum(frame[:-2]) + FRAME_START_SUM:
            self._logger.error('Invalid checksum {0:#0X}, data: {1}'.format(checksum, frame))
            return False
        return True

    def read_measure(self, ordered=False):
        frame = self._get_frame()
        data = self._parse_frame(frame)
        if ordered:
            return OrderedDict((DATA_LABELS[i], data[i]) for i in range(0, len(DATA_LABELS)))
        return {DATA_LABELS[i]: data[i] for i in range(0, len(DATA_LABELS))}
    
    def close(self):
        if self._serial.is_open:
            self._serial.close()