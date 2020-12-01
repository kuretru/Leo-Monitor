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

import socketserver
import sys

MESSAGE_START_CHAR = b'\xff\xff'
MESSAGE_TYPE = b'\x01'
MESSAGE_END_CHAR = b'\xfe\xef\n'


class LeoMonitorRequestHandler(socketserver.StreamRequestHandler):

    def handle(self):
        print(self.client_address)
        while True:
            data = self.rfile.readline()
            if not data:
                break
            print(data)


if __name__ == '__main__':
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
