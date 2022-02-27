from urllib.parse import unquote
from re import finditer
from base64 import b64decode
from struct import unpack

key = b'e806f6'

def _deckey(s) -> str:
    b = b64decode(unquote(s))
    return bytes([key[i % len(key)] ^ b[i] for i in range(len(b))])

def _decval(k, s):
    b = b64decode(unquote(s))
    key2 = k.encode('utf8') + key
    b = b[0:len(b) - (11 if b[-5] != 0 else 7)]
    return bytes([key2[i % len(key2)] ^ b[i] for i in range(len(b))])

def decryptxml(filename):
    result = {}

    with open(filename, 'r') as fp:
        content = fp.read()
    
    for re in finditer(r'<string name="(.*)">(.*)</string>', content):
        g = re.groups()
        try:
            key = _deckey(g[0]).decode('utf8')
        except:
            continue
        val = _decval(key, g[1])
        if key == 'UDID':
            val = ''.join([chr(val[4 * i + 6] - 10) for i in range(36)])
        elif len(val) == 4:
            val = str(unpack('i', val)[0])
        result[key] = val
        #except:
        #    pass
    return result