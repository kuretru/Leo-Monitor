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

MAX_BUFFER_SIZE = 4096

# START, START, TYPE, LENGTH, LENGTH, payload ... payload, CHECKSUM, END, END, END
MESSAGE_HEADER_LENGTH = 2 + 1 + 2 + 1 + 3
MESSAGE_START_CHAR = b'\xff\xff'
MESSAGE_TYPE_AUTH = b'\x01'
MESSAGE_TYPE_DATA = b'\x02'
MESSAGE_TYPE_PING = b'\x03'
MESSAGE_END_CHAR = b'\xfe\xef\n'


class ParseFailedError(Exception):
    pass


class LeoMonitorRequestHandler(socketserver.StreamRequestHandler):

    def handle(self):
        print(self.client_address)
        try:
            while True:
                self.handle_data_message()
        except EOFError:
            self.finish()

    def handle_auth_message(self):
        payload = self._parse_message(MESSAGE_TYPE_AUTH)

    def handle_data_message(self):
        payload = self._parse_message(MESSAGE_TYPE_DATA)
        print(payload)

    def _parse_message(self, message_type):
        message = self.rfile.readline(MAX_BUFFER_SIZE)
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
    threading.Thread(target=run_monitor_server, name='Thread-Monitor').start()
    threading.Thread(target=run_web_server, name='Thread-Web').start()
