# -*- coding:utf-8 -*-

from mininet.net import Mininet

result_record = lambda i: '../Data/server_{}.out'.format(i)

class Net(Mininet):

    def set_up_udp_listener(self, h):
        iperf_args = 'iperf -u '
        server = self.get(h.name)
        print('*** start server on {} ***'.format(h.name))
        server.cmd(iperf_args + '-s -i 1 ' + '> ' + result_record(h.id) + '&')
        return

    # TODO 将结果存入文件
    def udp_flow(self, src, dst, size):
        client = self.get(src.name)
        server = self.get(dst.name)

        iperf_args = 'iperf -u '
        size_args = '-n ' + str(size) + ' '
        print('*** start flow on {} ***'.format(src.name))
        client.cmd(iperf_args + size_args + '-c ' + server.IP())
        return

