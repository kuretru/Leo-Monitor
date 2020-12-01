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
MODE = '4'  # 连接模式：4->仅使用IPv4，6->仅使用IPv6，4,6->使用IPv4通信保持IPv6链接，6,4->使用IPv6通信保持IPv4链接
USERNAME = 'user'
PASSWORD = '123456'
INTERVAL = 1
NETWORKS = ('ens3',)

import json
import os
import socket
import subprocess
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
