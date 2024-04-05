import struct
import numpy as np
from PIL import Image, ImageCms
from scipy.optimize import curve_fit

def parse_s15Fixed16Number(data: bytes):
    '''s15Fixed16Number
    16bit signed integer + 16bit unsigned integer as fraction
    0x8000 0000 = -32768 + 0/2^16
    0x0000 0000 = 0 + 0/2^16 = 0
    0x0001 0000 = 1 + 0/2^16 = 1.0
    0x7fff ffff = 32767 + 65535/2^16
    '''
    x = struct.unpack('>h', data[:2])[0] + struct.unpack('>H', data[2:4])[0] / 2**16
    y = struct.unpack('>h', data[4:6])[0] + struct.unpack('>H', data[6:8])[0] / 2**16
    z = struct.unpack('>h', data[8:10])[0] + struct.unpack('>H', data[10:])[0] / 2**16
    return x, y, z

def get_cXYZ(profile: bytes, colour: bytes):
    i = profile.index(colour+b'XYZ')
    offset = struct.unpack('>I', profile[i+4:i+8])[0]
    length = struct.unpack('>I', profile[i+8:i+12])[0]
    profile = profile[offset:offset+length]
    xyz = parse_s15Fixed16Number(profile[8:])
    return np.array(xyz)

def get_cTRC(profile: bytes, colour: bytes):
    i = profile.index(colour+b'TRC')
    offset = struct.unpack('>I', profile[i+4:i+8])[0]
    length = struct.unpack('>I', profile[i+8:i+12])[0]
    dlen = struct.unpack('>I', profile[offset+8:offset+12])[0]
    
    if dlen == 1: # u8Fixed8Number, uint8 int + uint8 frac
        ufixed8p8 = struct.unpack('>BB', profile[offset+12:offset+length])
        gamma = ufixed8p8[0] + ufixed8p8[1] / 2**8
        return gamma, 'gamma'
    else:
        profile = profile[offset+12:offset+length]
        curve = np.array(struct.unpack('>'+'H'*(len(profile)//2), profile))
        return curve, 'curve'

def table2gamma(table):
    x = np.linspace(0, 1, len(table))
    # 대충 닮게만 만들어도 잘 돼 한잔 해
    popt, _ = curve_fit(lambda x, gamma: x ** gamma, x, table/65535)
    return popt[0], 'gamma'
