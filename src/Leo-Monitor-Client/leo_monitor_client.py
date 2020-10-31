#!/usr/bin/env python3
# coding=utf-8

"""
Leo Monitor Python3 Client
Version: 1.0
Author: Eugene Wu <kuretru@gmail.com>
URL: https://github.com/kuretru/SingleNet-Robot
"""

SERVER = 'monitor.kuretru.com'
PORT = '8078'
USERNAME = 'user'
PASSWORD = '123456'
INTERVAL = 1

import os


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
