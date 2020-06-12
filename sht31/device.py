import os
import re

HW2VERSION = {
    'BCM2708' : 1,
    'BCM2709' : 2,
    'BCM2835' : 3
}

REV1 = ['0000', '0002', '0003']

def get_default_bus():
    return 0 if is_first_revision() else 1

def is_first_revision():
    rev = os.popen('cat /proc/cpuinfo | grep Revision').read()
    match = re.search(r'Revision\s+:\s+.*(\w{4})$', rev)
    if not match:
        raise RuntimeError('Could not determine Raspberry Pi revision.')
    return match.group(1) in REV1

def pi_version():
    hw = os.popen('cat /proc/cpuinfo | grep Hardware').read()
    match = re.search(r'^Hardware\s+:\s+(\w+)$', hw)
    if not match or not match.group(1) in HW2VERSION:
        return None
    return HW2VERSION[match.group(1)]

