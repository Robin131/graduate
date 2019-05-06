# -*- coding:utf-8 -*-
import time
import threading
from mininet.net import Mininet

from const import server_result_record, FilePath, client_result_record
from Util import Util as U

class Net(Mininet):

    def set_up_udp_listener(self, h):
        iperf_args = 'iperf -u '
        server = self.get(h.name)
        print('*** start server on {}***'.format(h.name))
        server.cmd(iperf_args + '-s -i 1 ' + '> ' + server_result_record(h.t_id, h.id) + '&')
        return

    def set_default_gateway(self, h):
        gw_ip = h.gw_ip
        host = self.get(h.name)
        print('*** set gw {} to host {}'.format(gw_ip, host.name))
        host.cmd('route add default gw {}'.format(gw_ip))
        return


    def udp_flow(self, src, dst, size):
        client = self.get(src.name)
        server = self.get(dst.name)

        iperf_args = 'iperf -u '
        size_args = '-n ' + str(size) + ' '
        period_args = '-t 1 '

        print('*** start flow on {} ***'.format(src.name))
        print('src:{}, dst: {}, size:{}'.format(src.ip, dst.ip, size))
        st = time.time()
        res_name = client_result_record(src.t_id, src.id)
        file_name = res_name.split('/')[-1]
        if U.file_is_in_path(file_name, FilePath.client_res_path):
            client.cmd(iperf_args + size_args + '-c ' + server.IP() + ' ' + '>> ' + res_name + '&')
        else:
            client.cmd(iperf_args + size_args + '-c ' + server.IP() + ' ' + '> ' + res_name + '&')
        et = time.time()

        print('--- consume time {} ---'.format(et - st))

        return
