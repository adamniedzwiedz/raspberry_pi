from sht31 import SHT31
from time import sleep
import logging
import sys

logging.basicConfig()
log = logging.getLogger('test')

def create_sht31():
    sht31 = SHT31()
    if not sht31.init():
        log.error('Cannot init SHT31')
        sys.exit(1)
    return sht31

if __name__ == "__main__":
    sht31 = create_sht31()

    while True:
        try:
            temp, hum = sht31.read_temperature_humidity()
            print('Temp             = {0:0.3f} deg C'.format(temp))
            print('Humidity         = {0:0.2f} %'.format(hum))
            sleep(5.0)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as err:
            log.error('Error occured {0}'.format(err))
            sleep(5.0)
            sht31 = create_sht31()