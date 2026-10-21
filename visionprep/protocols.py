"""Modbus TCP codecs and taskbook robot command construction.

Nothing connects or moves automatically. The optional client connects only
when its context manager is explicitly entered by the caller.
"""
from contextlib import AbstractContextManager
import math
import socket
import struct

def word(v, name='word'):
    if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 65535:
        raise ValueError(name + ' must be an integer in 0..65535')
    return v

def unit(v):
    if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 255:
        raise ValueError('Unit id must be 0..255')
    return v

def read_request(transaction, unit_id, address, count=1):
    word(transaction);unit(unit_id);word(address)
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 125 or address + count > 65536:
        raise ValueError('Invalid holding-register range')
    return struct.pack('>HHHBBHH', transaction, 0, 6, unit_id, 3, address, count)

def write_request(transaction, unit_id, address, value):
    word(transaction);unit(unit_id);word(address);word(value)
    return struct.pack('>HHHBBHH', transaction, 0, 6, unit_id, 6, address, value)

def parse_response(data, transaction, unit_id, function, expected_count=None, expected_echo=None):
    if len(data) < 9:
        raise ValueError('Truncated Modbus response')
    tid, protocol, length, uid = struct.unpack('>HHHB', data[:7])
    if tid != transaction or protocol != 0 or uid != unit_id or length != len(data) - 6 or not 3 <= length <= 254:
        raise ValueError('Invalid MBAP header or mismatched transaction')
    if data[7] == function | 0x80:
        if len(data) != 9:
            raise ValueError('Invalid exception response length')
        raise ValueError('Modbus exception code ' + str(data[8]))
    if data[7] != function:
        raise ValueError('Unexpected function code')
    if function == 3:
        if expected_count is None or data[8] != expected_count * 2 or len(data) != 9 + data[8]:
            raise ValueError('Invalid register byte count')
        return list(struct.unpack('>' + 'H' * expected_count, data[9:]))
    if function == 6:
        if len(data) != 12:
            raise ValueError('Invalid write response length')
        echo = struct.unpack('>HH', data[8:12])
        if expected_echo is None or echo != tuple(expected_echo):
            raise ValueError('Write acknowledgement does not match request')
        return echo
    raise ValueError('Only functions 03 and 06 are implemented')

def receive_exact(connection, size):
    chunks = bytearray()
    while len(chunks) < size:
        part = connection.recv(size - len(chunks))
        if not part:
            raise ConnectionError('Connection closed inside a Modbus frame')
        chunks.extend(part)
    return bytes(chunks)

class ModbusTcpClient(AbstractContextManager):
    def __init__(self, host, port=502, unit_id=1, timeout=2):
        self.host, self.port, self.unit_id, self.timeout = host, port, unit(unit_id), timeout
        self.connection = None
        self.transaction = 0
    def __enter__(self):
        self.connection = socket.create_connection((self.host, self.port), timeout=self.timeout)
        return self
    def __exit__(self, *exc):
        if self.connection:
            self.connection.close()
            self.connection = None
    def exchange(self, function, address, value):
        if function not in (3,6):
            raise ValueError('Only functions 03 and 06 are implemented')
        if self.connection is None:
            raise RuntimeError('Client is not connected')
        self.transaction = (self.transaction + 1) & 65535
        request = read_request(self.transaction, self.unit_id, address, value) if function == 3 else write_request(self.transaction, self.unit_id, address, value)
        self.connection.sendall(request)
        header = receive_exact(self.connection, 7)
        length = struct.unpack('>H', header[4:6])[0]
        if not 3 <= length <= 254:
            raise ValueError('Invalid announced frame length')
        data = header + receive_exact(self.connection, length - 1)
        return parse_response(data, self.transaction, self.unit_id, function,
                              expected_count=value if function == 3 else None,
                              expected_echo=(address, value) if function == 6 else None)
    def read_holding(self, address=0, count=1):
        return self.exchange(3, address, count)
    def write_holding(self, address=1, value=0):
        return self.exchange(6, address, value)

ROBOT_COMMANDS = {'home':'$h', 'vacuum_on':'M3S1000', 'blow':'M3S500', 'pump_off':'M3S0',
                  'absolute_mode':'m20g90g00', 'position':'?'}

def robot_command(action):
    if action not in ROBOT_COMMANDS:
        raise ValueError('Unknown robot action')
    return ROBOT_COMMANDS[action]

def robot_move(x, y, z, a, limits):
    """Build a command string; limits must be supplied for the actual machine.

    The repository example limits are explicitly synthetic, not machine limits.
    """
    values = [float(v) for v in [x,y,z,a]]
    if len(limits) != 4:
        raise ValueError('Four axis limit pairs are required')
    for name, value, pair in zip('xyza', values, limits):
        if len(pair) != 2 or not all(math.isfinite(float(v)) for v in pair) or pair[0] > pair[1]:
            raise ValueError('Invalid axis limits')
        lower, upper = float(pair[0]), float(pair[1])
        if not math.isfinite(value) or not lower <= value <= upper:
            raise ValueError('Out of configured range: ' + name)
    return ''.join(name + (f'{value:.3f}'.rstrip('0').rstrip('.') if value != 0 else '0') for name, value in zip('xyza', values))
