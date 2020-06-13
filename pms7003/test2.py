from pms7003 import Pms7003, Pms7003Exception
from time import sleep
import logging
import sys

logging.basicConfig()
log = logging.getLogger('test2')
SERIAL_PORT = '/dev/ttyS0'

if __name__ == "__main__":
    pms = Pms7003(SERIAL_PORT)

    while True:
        try:
            for name, value in pms.read_measure(True).items():
                print('{0} = {1}'.format(name, value))
            print('-' * 20)
            sleep(5.0)
        except Pms7003Exception as err:
            log.error(err)
            sleep(5.0)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as err:
            log.error('Error occured {0}'.format(err))
            sleep(5.0)
            pms.close()
            pms = Pms7003(SERIAL_PORT)
