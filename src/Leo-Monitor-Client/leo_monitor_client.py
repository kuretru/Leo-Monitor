#!/usr/bin/env python3
# coding=utf-8

"""
Leo Monitor Python3 Client
Version: 1.0
Required: Python 3.5(+)
Author: Eugene Wu <kuretru@gmail.com>
URL: https://github.com/kuretru/Leo-Monitor
"""

SERVER = 'monitor.kuretru.com'
PORT = '8078'
USERNAME = 'user'
PASSWORD = '123456'
INTERVAL = 1

import os
import time
import subprocess


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
    获取RAM和Swap的使用情况
    :return: RAM和Swap的使用情况(MB)
    """
    data = {}
    with open('/proc/meminfo') as f:
        for line in f.readlines():
            pair = line.split()
            data[pair[0]] = pair[1]
    memory = {}
    memory['total'] = int(data['MemTotal:'])
    memory['buffers'] = int(data['Buffers:'])
    memory['cached'] = int(data['Cached:'])
    memory['used'] = memory['total'] - int(data['MemAvailable:'])
    memory['realUsed'] = memory['total'] - (int(data['MemFree:']) + memory['buffers'] + memory['cached'])
    swap = {}
    swap['total'] = int(data['SwapTotal:'])
    swap['used'] = swap['total'] - int(data['SwapFree:'])
    return memory, swap


def _run_subprocess(args):
    output = subprocess.run(args, capture_output=True, check=True)
    return output.stdout.decode().replace('\n', '').strip()


def get_storage():
    """
    获取硬盘的使用情况
    :return:  硬盘的使用情况(GB)
    """
    command = 'df -Tlg --total -t ext4 -t ext3 -t ext2 -t xfs'
    output = _run_subprocess(command)
    data = output.splitlines()[-1].split()
    total = int(data[2])
    used = int(data[3])
    return {'total': total, 'used': used}
