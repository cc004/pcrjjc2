from msgpack import packb, unpackb
from random import randint
from hashlib import md5, sha1
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad
from base64 import b64encode, b64decode
from random import choice

from msgpack.exceptions import ExtraData
from hoshino.aiorequests import post

defaultHeaders = {
    'Accept-Encoding' : 'gzip',
    'User-Agent' : 'Dalvik/2.1.0 (Linux, U, Android 5.1.1, PCRT00 Build/LMY48Z)',
    'Content-Type': 'application/octet-stream',
    'Expect': '100-continue',
    'X-Unity-Version' : '2018.4.21f1',
    'APP-VER' : '3.1.0',
    'BATTLE-LOGIC-VERSION' : '4',
    'BUNDLE-VER' : '',
    'DEVICE' : '2',
    'DEVICE-ID' : '7b1703a5d9b394e24051d7a5d4818f17',
    'DEVICE-NAME' : 'OPPO PCRT00',
    'GRAPHICS-DEVICE-NAME' : 'Adreno (TM) 640',
    'IP-ADDRESS' : '10.0.2.15',
    'KEYCHAIN' : '',
    'LOCALE' : 'Jpn',
    'PLATFORM-OS-VERSION' : 'Android OS 5.1.1 / API-22 (LMY48Z/rel.se.infra.20200612.100533)',
    'REGION-CODE' : '',
    'RES-VER' : '00017004'
}

class ApiException(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code

class pcrclient:

    @staticmethod
    def _makemd5(str) -> str:
        return md5((str + 'r!I@nt8e5i=').encode('utf8')).hexdigest()
    
    def __init__(self, udid, short_udid, viewer_id, platform, proxy):
        
        self.viewer_id = viewer_id
        self.short_udid = short_udid
        self.udid = udid
        self.headers = {}
        self.proxy = proxy

        for key in defaultHeaders.keys():
            self.headers[key] = defaultHeaders[key]

        self.headers['SID'] = pcrclient._makemd5(viewer_id + udid)
        self.apiroot = f'https://api{"" if platform == "1" else platform}-pc.so-net.tw'
        self.headers['platform'] = '1'

        self.shouldLogin = True

    @staticmethod
    def createkey() -> bytes:
        return bytes([ord('0123456789abcdef'[randint(0, 15)]) for _ in range(32)])

    def _getiv(self) -> bytes:
        return self.udid.replace('-', '')[:16].encode('utf8')

    def pack(self, data: object, key: bytes) -> tuple:
        aes = AES.new(key, AES.MODE_CBC, self._getiv())
        packed = packb(data,
            use_bin_type = False
        )
        return packed, aes.encrypt(pad(packed, 16)) + key

    def encrypt(self, data: str, key: bytes) -> bytes:
        aes = AES.new(key, AES.MODE_CBC, self._getiv())
        return aes.encrypt(pad(data.encode('utf8'), 16)) + key

    def decrypt(self, data: bytes):
        data = b64decode(data.decode('utf8'))
        aes = AES.new(data[-32:], AES.MODE_CBC, self._getiv())
        return aes.decrypt(data[:-32]), data[-32:]

    def unpack(self, data: bytes):
        data = b64decode(data.decode('utf8'))
        aes = AES.new(data[-32:], AES.MODE_CBC, self._getiv())
        dec = unpad(aes.decrypt(data[:-32]), 16)
        return unpackb(dec,
            strict_map_key = False
        ), data[-32:]

    alphabet = '0123456789'

    @staticmethod
    def _encode(dat: str) -> str:
        return f'{len(dat):0>4x}' + ''.join([(chr(ord(dat[int(i / 4)]) + 10) if i % 4 == 2 else choice(pcrclient.alphabet)) for i in range(0, len(dat) * 4)]) + pcrclient._ivstring()

    @staticmethod
    def _ivstring() -> str:
        return ''.join([choice(pcrclient.alphabet) for _ in range(32)])

    async def callapi(self, apiurl: str, request: dict, noerr: bool = False):
        key = pcrclient.createkey()

        try:    
            if self.viewer_id is not None:
                request['viewer_id'] = b64encode(self.encrypt(str(self.viewer_id), key))

            packed, crypted = self.pack(request, key)
            self.headers['PARAM'] = sha1((self.udid + apiurl + b64encode(packed).decode('utf8') + str(self.viewer_id)).encode('utf8')).hexdigest()
            self.headers['SHORT-UDID'] = pcrclient._encode(self.short_udid)

            resp = await post(self.apiroot + apiurl,
                data = crypted,
                headers = self.headers,
                timeout = 5,
                proxies = self.proxy,
                verify = False)
            response = await resp.content
            
            response = self.unpack(response)[0]

            data_headers = response['data_headers']

            if 'viewer_id' in data_headers:
                self.viewer_id = data_headers['viewer_id']

            if 'required_res_ver' in data_headers:
                self.headers['RES-VER'] = data_headers['required_res_ver']
            
            data = response['data']
            if not noerr and 'server_error' in data:
                data = data['server_error']
                code = data_headers['result_code']
                print(f'pcrclient: {apiurl} api failed code = {code}, {data}')
                raise ApiException(data['message'], data['status'])

            print(f'pcrclient: {apiurl} api called')
            return data
        except:
            self.shouldLogin = True
            raise
    
    async def login(self):
        
        await self.callapi('/check/check_agreement', {})
        await self.callapi('/check/game_start', {})
        await self.callapi('/load/index', {
            'carrier': 'Android'
        })

        self.shouldLogin = False
