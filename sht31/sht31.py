# based on https://github.com/ralf1070/Adafruit_Python_SHT31/blob/master/Adafruit_SHT31.py
# and https://github.com/adafruit/Adafruit_Python_GPIO/blob/master/Adafruit_GPIO/I2C.py

from device import get_default_bus
from binascii import hexlify
from time import sleep
import logging
import smbus

# SHT31D default address.
SHT31_I2CADDR = 0x44

# SHT31D Registers
SHT31_MEAS_HIGHREP_STRETCH = 0x2C06
SHT31_MEAS_MEDREP_STRETCH = 0x2C0D
SHT31_MEAS_LOWREP_STRETCH = 0x2C10
SHT31_MEAS_HIGHREP = 0x2400
SHT31_MEAS_MEDREP = 0x240B
SHT31_MEAS_LOWREP = 0x2416
SHT31_READSTATUS = 0xF32D
SHT31_CLEARSTATUS = 0x3041
SHT31_SOFTRESET = 0x30A2
SHT31_HEATER_ON = 0x306D
SHT31_HEATER_OFF = 0x3066

SHT31_STATUS_DATA_CRC_ERROR = 0x0001
SHT31_STATUS_COMMAND_ERROR = 0x0002
SHT31_STATUS_RESET_DETECTED = 0x0010
SHT31_STATUS_TEMPERATURE_ALERT = 0x0400
SHT31_STATUS_HUMIDITY_ALERT = 0x0800
SHT31_STATUS_HEATER_ACTIVE = 0x2000
SHT31_STATUS_ALERT_PENDING = 0x8000

class SHT31(object):
    def __init__(self, address=SHT31_I2CADDR, **kwargs):
        busnum = get_default_bus()
        self._logger = logging.getLogger('SHT31')
        self._bus = smbus.SMBus(busnum)
        self._address = address
        self._logger.debug('Created SHT31 Bus: {0}, Addr: {1:#0X}'.format(busnum, address))

    def _write_cmd(self, cmd):
        self._bus.write_byte_data(self._address, cmd >> 8, cmd & 0xFF)
        self._logger.debug('Wrote command: 0x%04X', cmd)

    def init(self):
        self.reset()
        status = self.read_status()
        return status is not None and status != 0xFFFF
    
    def reset(self):
        self._write_cmd(SHT31_SOFTRESET)
        sleep(0.01)

    def clear_status(self):
        self._write_cmd(SHT31_CLEARSTATUS)

    def read_status(self):
        self._write_cmd(SHT31_READSTATUS)
        data = self._bus.read_i2c_block_data(self._address, 0, 3)
        self._logger.debug('Read status data: 0x{0}'.format(hexlify(data))
        if data[2] != self._crc8(data[0:2]):
            self._logger.warning('Invalid CRC8 for read status')
            return None
        return data[0] << 8 | data[1]

    def is_data_crc_error(self):
        return bool(self.read_status() & SHT31_STATUS_DATA_CRC_ERROR)

    def is_command_error(self):
        return bool(self.read_status() & SHT31_STATUS_COMMAND_ERROR)

    def is_reset_detected(self):
        return bool(self.read_status() & SHT31_STATUS_RESET_DETECTED)

    def is_tracking_temperature_alert(self):
        return bool(self.read_status() & SHT31_STATUS_TEMPERATURE_ALERT)

    def is_tracking_humidity_alert(self):
        return bool(self.read_status() & SHT31_STATUS_HUMIDITY_ALERT)

    def is_heater_active(self):
        return bool(self.read_status() & SHT31_STATUS_HEATER_ACTIVE)

    def is_alert_pending(self):
        return bool(self.read_status() & SHT31_STATUS_ALERT_PENDING)

    def set_heater(self, doEnable = True):
        if doEnable:
            self._write_cmd(SHT31_HEATER_ON)
        else:
            self._write_cmd(SHT31_HEATER_OFF)

    def read_temperature_humidity(self):
        self._write_cmd(SHT31_MEAS_HIGHREP)
        sleep(0.015)
        data = self._bus.read_i2c_block_data(self._address, 0, 6)
        
        if data[2] != self._crc8(data[0:2]):
            self._logger.warning('Invalid CRC8 for read temperature')
            return (float("nan"), float("nan"))

        rawTemperature = data[0] << 8 | data[1]
        temperature = 175.0 * rawTemperature / 0xFFFF - 45.0

        if data[5] != self._crc8(data[3:5]):
            self._logger.warning('Invalid CRC8 for read humidity')
            return (float("nan"), float("nan"))

        rawHumidity = data[3] << 8 | data[4]
        humidity = 100.0 * rawHumidity / 0xFFFF

        return (temperature, humidity)

    def read_temperature(self):
        (temperature, _) = self.read_temperature_humidity()
        return temperature

    def read_humidity(self):
        (_, humidity) = self.read_temperature_humidity()
        return humidity

    def _crc8(self, buffer):
        """ Polynomial 0x31 (x8 + x5 +x4 +1) """
        polynomial = 0x31
        crc = 0xFF
  
        index = 0
        for index in range(0, len(buffer)):
            crc ^= buffer[index]
            for _ in range(8, 0, -1):
                if crc & 0x80:
                    crc = (crc << 1) ^ polynomial
                else:
                    crc = (crc << 1)
        return crc & 0xFF