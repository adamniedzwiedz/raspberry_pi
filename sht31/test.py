from sht31 import SHT31
from time import sleep
import sys

if __name__ == "__main__":
    sht31 = SHT31()
    if not sht31.init():
        print('Cannot init SHT31')
        sys.exit(1)
    try:
        while True:
            temp = sht31.read_temperature()
            print('Temp             = {0:0.3f} deg C'.format(temp))
            hum = sht31.read_humidity()
            print('Humidity         = {0:0.2f} %'.format(hum))
            sleep(5.0)
    except KeyboardInterrupt:
        sys.exit(0)