#!/usr/bin/env python3
# coding=utf-8

"""
Leo Monitor Python3 Server
Version: 1.0
Required: Python 3.5(+)
Author: Eugene Wu <kuretru@gmail.com>
URL: https://github.com/kuretru/Leo-Monitor
"""

SERVER_LISTEN = ('0.0.0.0', 8078)
WEB_LISTEN = ('127.0.0.1', 8077)

import json
import socketserver
import sys
import threading

CONFIG = {
    'title': '狮子监控',
    'clients': [{
        'name': '测试',
        'username': 'user',
        'password': '123456'
    }]
}

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


def load_config():
    with open('leo-monitor.json') as f:
        data = f.read()
    return json.loads(data)


class LeoMonitorRequestHandler(socketserver.StreamRequestHandler):

    def handle(self):
        print('Client %s:%d connected' % self.client_address)
        # TODO：黑名单机制
        try:
            self.send_auth_message()
            while True:
                self.receive_data_message()
        except EOFError:
            print('Client %s:%d disconnected' % self.client_address)
        except ConnectionError as e:
            print('Client %s:%d %s' % (self.client_address[0], self.client_address[1], e.strerror))
        finally:
            self.finish()

    def send_auth_message(self):
        payload = {
            'server': 'leo-monitor',
            'protocol': 1.0,
            'data': 'hello, need authentication'
        }
        self._send_message(MESSAGE_TYPE_AUTH, payload)

    def receive_auth_message(self):
        payload = self._receive_message(MESSAGE_TYPE_AUTH)

    def receive_data_message(self):
        payload = self._receive_message(MESSAGE_TYPE_DATA)
        print(payload)

    def _send_message(self, message_type: bytes, payload: dict):
        message = build_message(message_type, payload)
        self.wfile.write(message)

    def _receive_message(self, message_type: bytes):
        message = self.rfile.readline(MAX_BUFFER_SIZE)
        return parse_message(message_type, message)


def run_monitor_server():
    try:
        print('Starting LeoMonitor Server on %s:%d' % SERVER_LISTEN)
        with socketserver.ThreadingTCPServer(SERVER_LISTEN, LeoMonitorRequestHandler) as server:
            server.serve_forever()
    except OSError as e:
        print('Failed to Start LeoMonitor Server: %s' % e)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
    print('Stopped LeoMonitor Server')


def run_web_server():
    pass


if __name__ == '__main__':
    CONFIG = load_config()
    threading.Thread(target=run_monitor_server, name='Thread-Monitor').start()
    threading.Thread(target=run_web_server, name='Thread-Web').start()
