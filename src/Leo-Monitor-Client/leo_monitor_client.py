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
import time


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
    x = _get_cpu_usage()
    time.sleep(INTERVAL)
    y = _get_cpu_usage()
    data = [y[i] - x[i] for i in range(len(y))]
    usage = data[0] + data[2] + data[3]
    if usage == 0:
        return 100
    return int((usage - data[3]) * 100 / usage)


def get_memory():
    """
    获取RAM和Swap的使用率
    :return: RAM和Swap的使用率
    """
    data = {}
    with open('/proc/meminfo') as f:
        for line in f.readlines():
            pair = line.split()
            data[pair[0]] = pair[1]
    mem_total = int(data['MemTotal:'])
    mem_free = int(data['MemFree:'])
    mem_available = int(data['MemAvailable:'])
    buffers = int(data['Buffers:'])
    cached = int(data['Cached:'])
    mem_used = mem_total - mem_available
    real_used = mem_total - (mem_free + buffers + cached)
    swap_total = int(data['SwapTotal::'])
    swap_free = int(data['SwapFree:'])
    swap_used = swap_total - swap_free
    memory = {
        'total': mem_total,
        'used': mem_used,
        'realUsed': real_used,
        'buffers': buffers,
        'cached': cached
    }
    swap = {
        'total': swap_total,
        'used': swap_used
    }
    return memory, swap
