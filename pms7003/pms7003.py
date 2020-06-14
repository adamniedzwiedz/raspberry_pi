# Based on https://github.com/tomek-l/pms7003/blob/master/pms7003/pms7003.py

import sys
import serial
import struct
import logging
from time import sleep
from collections import OrderedDict

class Pms7003Exception(Exception):
    def __init__(self, msg):
        super(Pms7003Exception, self).__init__(msg)

if sys.version_info > (3, 0):
    FRAME_START = bytes([0x42, 0x4d])
    READ_PASSIVE_CMD = FRAME_START + bytes([0xe2, 0x00, 0x00, 0x01, 0x71])
    SET_PASSIVE_CMD = FRAME_START + bytes([0xe1, 0x00, 0x00, 0x01, 0x70])
    SET_ACTIVE_CMD = FRAME_START + bytes([0xe1, 0x00, 0x01, 0x01, 0x71])
    SLEEP_CMD = FRAME_START + bytes([0xe4, 0x00, 0x00, 0x01, 0x73])
    WAKEUP_CMD = FRAME_START + bytes([0xe4, 0x00, 0x01, 0x01, 0x74])
else:
    FRAME_START = '\x42\x4d'

    READ_PASSIVE_CMD = FRAME_START + '\xe2\x00\x00\x01\x71'
    
    SET_PASSIVE_CMD = FRAME_START + '\xe1\x00\x00\x01\x70'
    SET_PASSIVE_CMD_RESP = FRAME_START + '\x00\x04\xe1\x00\x01\x74'

    SET_ACTIVE_CMD = FRAME_START + '\xe1\x00\x01\x01\x71'
    SET_ACTIVE_CMD_RESP = FRAME_START + '\x00\x04\xe1\x01\x01\x75'

    SLEEP_CMD = FRAME_START + '\xe4\x00\x00\x01\x73'
    SLEEP_CMD_RESP = FRAME_START + '\x00\x04\xe4\x00\x01\x77'
    
    WAKEUP_CMD = FRAME_START + '\xe4\x00\x01\x01\x74'
    WAKEUP_CMD_RESP = FRAME_START + '\x00\x04\xe4\x01\x01\x78'

FRAME_START_SUM = 0x42 + 0x4d
FRAME_DATA_LEN = 30
FRAME_CMD_LEN = 6

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
                                     parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=5)
    
    def _get_frame_format(self, frame_len):
        return '>{0}'.format('B' * frame_len)

    def _get_frame(self, frame_len):
        with self._serial as s:
            s.read_until(FRAME_START)
            frame_format = self._get_frame_format(frame_len)
            frame = struct.unpack(frame_format, s.read(frame_len))
        if not self._is_valid_frame(frame, frame_len):
            raise Pms7003Exception('Invalid frame')
        return frame

    def _parse_frame(self, frame):
        data = [frame[i] << 8 | frame[i+1] for i in range(0, len(frame), 2)]
        return data[1:-1]

    def _is_valid_frame(self, frame, frame_len):
        if len(frame) != frame_len:
            self._logger.error('Invalid frame length {0}, data: {1}'.format(len(frame), frame))
            return False
        checksum = frame[-2] << 8 | frame[-1]
        if checksum != sum(frame[:-2]) + FRAME_START_SUM:
            self._logger.error('Invalid checksum {0:#0X}, data: {1}'.format(checksum, frame))
            return False
        return True

    def _create_result(self, data, ordered):
        if ordered:
            return OrderedDict((DATA_LABELS[i], data[i]) for i in range(0, len(DATA_LABELS)))
        return {DATA_LABELS[i]: data[i] for i in range(0, len(DATA_LABELS))}

    def read_measure(self, ordered=False):
        frame = self._get_frame(FRAME_DATA_LEN)
        data = self._parse_frame(frame)
        return self._create_result(data, ordered)
    
    def close(self):
        if self._serial.is_open:
            self._serial.close()
    
    def open_serial_if_closed(self):
        if not self._serial.is_open:
            self._serial.open()

    def sleep(self):
        with self._serial as s:
            s.write(SLEEP_CMD)
            sleep(3.0)
            data = s.read(s.in_waiting)
            return SLEEP_CMD_RESP in data
    
    def wakeup(self, wait_s=30.0):
        with self._serial as s:
            s.write(WAKEUP_CMD)
            sleep(wait_s)
            data = s.read(s.in_waiting)
            return len(data) > 0
    
    def set_active_mode(self):
        with self._serial as s:
            s.write(SET_ACTIVE_CMD)
            sleep(1.0)
            data = s.read(s.in_waiting)
            return SET_ACTIVE_CMD_RESP in data

    def set_passive_mode(self):
        with self._serial as s:
            s.write(SET_PASSIVE_CMD)
            sleep(1.0)
            data = s.read(s.in_waiting)
            return SET_PASSIVE_CMD_RESP in data
    
    def trigger_measure(self, ordered=False):
        with self._serial as s:
            s.write(READ_PASSIVE_CMD)
            sleep(1.0)
            frame = s.read(s.in_waiting)
            if not frame.startswith(FRAME_START):
                raise Pms7003Exception('No frame')
            frame_format = self._get_frame_format(FRAME_DATA_LEN)
            frame = struct.unpack(frame_format, frame[2:])
            if not self._is_valid_frame(frame, FRAME_DATA_LEN):
                raise Pms7003Exception('Invalid frame')
            data = self._parse_frame(frame)
            return self._create_result(data, ordered)
