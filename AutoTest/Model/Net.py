# -*- coding:utf-8 -*-
import time
import threading
from mininet.net import Mininet

from const import server_result_record

class Net(Mininet):

    def set_up_udp_listener(self, h):
        iperf_args = 'iperf -u '
        server = self.get(h.name)
        print('*** start server on {} ***'.format(h.name))
        threading.Thread(target=self.c1, args = (server, iperf_args, h))
        return


    def c1(self, server, iperf_args, h):
        server.cmd(iperf_args + '-s -i 1 ' + '> ' + server_result_record(h.id) + '&')

    # TODO 将结果存入文件
    def udp_flow(self, src, dst, size):
        client = self.get(src.name)
        server = self.get(dst.name)

        iperf_args = 'iperf -u '
        size_args = '-n ' + str(size) + ' '
        period_args = '-t 3 '

        print('*** start flow on {} ***'.format(src.name))
        print('src:{}, dst: {}, size:{}'.format(src.ip, dst.ip, size))
        st = time.time()
        client.cmd(iperf_args + period_args + '-c ' + server.IP())
        # threading.Thread(target=self.c2, args=(client, iperf_args, period_args, server)).start()
        et = time.time()

        print('--- consume time {} ---'.format(et - st))

        return

    def c2(self, client, iperf_args, period_args ,server):
        client.cmd(iperf_args + period_args + '-c ' + server.IP())