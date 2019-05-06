# -*- coding:utf-8 -*-
import time
import threading
from mininet.net import Mininet

from const import server_result_record

class Net(Mininet):

    def set_up_udp_listener(self, h):
        iperf_args = 'iperf -u '
        server = self.get(h.name)
        print('*** start server on {}***'.format(h.name))
        server.cmd(iperf_args + '-s -i 1 ' + '> ' + server_result_record(h.t_id, h.id) + '&')
        return

    # TODO 将结果存入文件
    def udp_flow(self, src, dst, size):
        client = self.get(src.name)
        server = self.get(dst.name)

        iperf_args = 'iperf -u '
        size_args = '-n ' + str(size) + ' '
        period_args = '-t 1 '

        print('*** start flow on {} ***'.format(src.name))
        print('src:{}, dst: {}, size:{}'.format(src.ip, dst.ip, size))
        st = time.time()
        client.cmd(iperf_args + size_args + '-c ' + server.IP())
        et = time.time()

        print('--- consume time {} ---'.format(et - st))

        return
