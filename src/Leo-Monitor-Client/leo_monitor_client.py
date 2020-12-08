#!/usr/bin/env python3
# coding=utf-8

"""
Leo Monitor Python3 Client
Version: 1.0
Required: Python 3.5(+)
Author: Eugene Wu <kuretru@gmail.com>
URL: https://github.com/kuretru/Leo-Monitor
"""

SERVER = '192.168.28.8'  # 服务端域名(地址)
PORT = 8078  # 服务端监听端口
MODE = '4'  # 连接模式：4->仅使用IPv4，6->仅使用IPv6，4+6->使用IPv4通信保持IPv6链接，6+4->使用IPv6通信保持IPv4链接
USERNAME = 'user'
PASSWORD = '123456'
INTERVAL = 1
NETWORKS = ('ens3',)

import json
import os
import socket
import sys
import threading
import time

last_cpu_usage = []
last_network_traffic = []


def get_uptime():
    """
    获取操作系统自启动到现在经过的时间
    :return: 操作系统自启动到现在经过的时间(单位：秒)
    """
    with open('/proc/uptime') as f:
        line = f.readline()
    data = line.split()
    return int(float(data[0]))


def get_loadavg():
    """
    获取操作系统的平均负载
    :return: 操作系统1/5/15分钟内的平均负载
    """
    data = os.getloadavg()
    data = [round(i, 4) for i in data]
    return data


def _get_cpu_usage():
    with open('/proc/stat') as f:
        line = f.readline()
    data = line.split()[1:5]
    data = [int(i) for i in data]
    return data


def get_cpu_usage():
    """
    获取CPU的使用率
    :return: CPU的使用率(百分比)
    """
    global last_cpu_usage
    x = last_cpu_usage
    y = _get_cpu_usage()
    data = [y[i] - x[i] for i in range(len(y))]
    last_cpu_usage = y
    usage = data[0] + data[2] + data[3]
    if usage == 0:
        return 100
    return int((usage - data[3]) * 100 / usage)


def get_memory():
    """
    获取RAM和Swap的使用情况
    :return: RAM和Swap的使用情况(MB)
    """
    raw = {}
    with open('/proc/meminfo') as f:
        for line in f.readlines():
            pair = line.split()
            raw[pair[0]] = pair[1]
    data = {}
    data['total'] = int(raw['MemTotal:'])
    data['buffers'] = int(raw['Buffers:'])
    data['cached'] = int(raw['Cached:'])
    data['used'] = data['total'] - int(raw['MemAvailable:'])
    data['realUsed'] = data['total'] - (int(raw['MemFree:']) + data['buffers'] + data['cached'])
    data['swapTotal'] = int(raw['SwapTotal:'])
    data['swapUsed'] = data['swapTotal'] - int(raw['SwapFree:'])
    return data


def _run_subprocess(args):
    import subprocess
    output = subprocess.run(args.split(), stdout=subprocess.PIPE, check=True)
    return output.stdout.decode()


def get_storage():
    """
    获取硬盘的使用情况
    :return: 硬盘的使用情况(GB)
    """
    command = 'df -TlBM --total -t ext4 -t ext3 -t ext2 -t xfs'
    output = _run_subprocess(command)
    data = output.splitlines()[-1].split()
    total = int(data[2][:-1])
    used = int(data[3][:-1])
    return {'total': total, 'used': used}


def _get_network_traffic():
    data = [0, 0]
    with open('/proc/net/dev') as f:
        lines = f.readlines()[2:]
    for line in lines:
        record = line.split()
        if record[0][:-1] not in NETWORKS:
            continue
        data[0] += int(record[1])
        data[1] += int(record[9])
    return data


def get_network_traffic():
    """
    获取网络的使用情况(聚合)
    :return: 每秒传输速度及累计流量(Byte)
    """
    global last_network_traffic
    x = last_network_traffic
    y = _get_network_traffic()
    diff = [y[i] - x[i] for i in range(len(y))]
    last_network_traffic = y
    data = {
        'receiveSpeed': diff[0] / INTERVAL,
        'transmitSpeed': diff[1] / INTERVAL,
        'receiveTotal': y[0],
        'transmitTotal': y[1]
    }
    return data


def build_payload():
    data = {
        'uptime': get_uptime(),
        'load': get_loadavg(),
        'cpu': get_cpu_usage(),
        'memory': get_memory(),
        'storage': get_storage(),
        'network': get_network_traffic()
    }
    return data


MAX_BUFFER_SIZE = 4096
# START, START, TYPE, LENGTH, LENGTH, payload ... payload, CHECKSUM, END, END, END
MESSAGE_HEADER_LENGTH = 2 + 1 + 2 + 1 + 3
MESSAGE_START_CHAR = b'\xff\xff'
MESSAGE_TYPE_AUTH = b'\x01'
MESSAGE_TYPE_DATA = b'\x02'
MESSAGE_TYPE_PING = b'\x03'
MESSAGE_END_CHAR = b'\xfe\xef\n'


def build_message(message_type: bytes, payload: dict):
    payload = json.dumps(payload).encode('utf-8')
    payload_length = len(payload)
    message = bytearray(MESSAGE_HEADER_LENGTH + payload_length)
    message[0:2] = MESSAGE_START_CHAR[:]
    message[2] = message_type[0]
    message[3] = (payload_length & 0xffff) >> 8
    message[4] = payload_length & 0xff
    message[5:5 + payload_length] = payload[:]
    message[-3:] = MESSAGE_END_CHAR[:]
    return bytes(message)


def parse_message(message_type: bytes, message: bytes):
    message_length = len(message)
    if not message:
        raise EOFError
    if message_length < MESSAGE_HEADER_LENGTH or (message_length == MAX_BUFFER_SIZE and '\n' not in message):
        raise ParseFailedError('Illegal protocol or packet size too large')
    if message[0:2] != MESSAGE_START_CHAR[:]:
        raise ParseFailedError('Illegal protocol start char')
    if message[-3:] != MESSAGE_END_CHAR[:]:
        raise ParseFailedError('Illegal protocol end char')
    if message_type[0] != message[2]:
        raise ParseFailedError('Wrong message type')
    payload_length = (message[3] << 8) | message[4]
    if payload_length != message_length - MESSAGE_HEADER_LENGTH:
        # TODO：待处理payload内含\n问题
        raise ParseFailedError('Illegal payload size')
    payload = message[5: 5 + payload_length]
    payload = json.loads(payload.decode('utf-8'))
    return payload


def hmac_sha256(message: str, key: str):
    import hmac
    import hashlib
    return hmac.new(
        key.encode('utf-8'), msg=message.encode('utf-8'), digestmod=hashlib.sha256
    ).hexdigest().lower()


class ParseFailedError(Exception):
    pass


class ProtocolError(Exception):
    pass


class LeoMonitorClient:

    def __init__(self, protocol='IPv4', mode='Data'):
        self.protocol = protocol
        self.mode = mode

    def start(self):
        thread = threading.Thread(target=self._run_client, name='Thread-%s-%s' % (self.protocol, self.mode))
        thread.start()

    def _run_client(self):
        family = socket.AF_INET if self.protocol == 'IPv4' else socket.AF_INET6
        while True:
            with socket.socket(family, socket.SOCK_STREAM) as s:
                s.connect((SERVER, PORT))
                self.receive_auth_message(s)
                while True:
                    message = build_message(MESSAGE_TYPE_DATA, build_payload())
                    s.send(message)
                    time.sleep(INTERVAL)

    def receive_auth_message(self, s: socket):
        payload = self._receive_message(s, MESSAGE_TYPE_AUTH)
        if payload['server'] != 'leo-monitor':
            raise ProtocolError('Wrong API server')
        if payload['protocol'] != 1.0:
            raise ProtocolError('Wrong protocol version')
        if payload['data'] != 'hello, need authentication':
            raise ProtocolError('Wrong authentication message')

    def send_auth_message(self, s: socket):
        import uuid
        nonce = uuid.uuid4().hex.lower()
        payload = {
            'username': USERNAME,
            'password': hmac_sha256(PASSWORD, nonce),
            'nonce': nonce,
            'type': self.mode.lower()
        }
        self._send_message(s, MESSAGE_TYPE_AUTH, payload)

    def _send_message(self, s: socket, message_type: bytes, payload: dict):
        message = build_message(message_type, payload)
        s.send(message)

    def _receive_message(self, s: socket, message_type: bytes):
        message = s.makefile(mode='b').readline()
        return parse_message(message_type, message)


if __name__ == '__main__':
    print('Starting LeoMonitor Client')
    last_cpu_usage = _get_cpu_usage()
    last_network_traffic = _get_network_traffic()
    if MODE == '4':
        LeoMonitorClient('IPv4', 'Data').start()
    elif MODE == '6':
        LeoMonitorClient('IPv6', 'Data').start()
    elif MODE == '4+6':
        LeoMonitorClient('IPv4', 'Data').start()
        LeoMonitorClient('IPv6', 'Heart').start()
    elif MODE == '6+4':
        LeoMonitorClient('IPv6', 'Data').start()
        LeoMonitorClient('IPv4', 'Heart').start()
    else:
        print('Wrong client mode')
        sys.exit(1)
    print('Stopped LeoMonitor Client')
