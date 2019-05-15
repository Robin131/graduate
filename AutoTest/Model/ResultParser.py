# -*- coding:utf-8 -*-

import os
import re

from const import FilePath, IperfArg
import matplotlib.pyplot as plot

class ResultParser(object):
    def __init__(self):
        return

'''
    基于多线程的out文件输出结果解释类
    目前支持总体丢包率
'''
class MultiThreadOutFileResultParser(ResultParser):
    def __init__(self, server_path=FilePath.server_res_path, client_path=FilePath.client_res_path):
        super(MultiThreadOutFileResultParser, self).__init__()

        self.sever_path = server_path
        self.client_path = client_path

    # 返回总的丢包率
    def parse_server(self):

        pkt_loss_arg = r'([0-9]+)\ *\/\ *([0-9]+)'
        pkt_received = 0
        pkt_sent = 0

        # iperf bug for too many pkts
        max_pkt = IperfArg.max_pkt

        ls = os.listdir(self.sever_path)
        for file in ls:
            if os.path.isdir(file):
                continue
            file = self.sever_path + '/' + file
            with open(file, 'r') as f:
                raw = f.readlines()
                for line in raw:
                    result = re.search(pkt_loss_arg, line)
                    if result:
                        sent = int(result.group(2))
                        received = sent - int(result.group(1))
                        if sent >= max_pkt:
                            continue
                        pkt_sent += sent
                        pkt_received += received
                    else:
                        continue
        pkt_loss = (pkt_sent - pkt_received) / float(pkt_sent)
        return pkt_loss

    # 返回每一个主机的丢包率 {t_id->{h_id->pkt_loss}}
    def hosts_pkt_loss(self):
        pkt_loss_arg = r'([0-9]+)\ *\/\ *([0-9]+)'
        max_pkt = IperfArg.max_pkt

        tmp = {}
        res = {}

        ls = os.listdir(self.sever_path)
        for file in ls:
            name = file
            if os.path.isdir(file):
                continue
            file = self.sever_path + '/' + file
            with open(file, 'r') as f:
                pkt_received = 0
                pkt_sent = 0
                pkt_loss = 0
                raw = f.readlines()
                for line in raw:
                    result = re.search(pkt_loss_arg, line)
                    if result:
                        sent = int(result.group(2))
                        received = sent - int(result.group(1))
                        if sent >= max_pkt:
                            continue
                        pkt_sent += sent
                        pkt_received += received
                    else:
                        continue

                pkt_loss = (pkt_sent - pkt_received) / float(pkt_sent) if pkt_sent != 0 else 0
                tmp[name.split('.')[0]] = pkt_loss

        for h in tmp.keys():
            parse = h.split('_')
            t_id = int(parse[1][1:])
            h_id = int(parse[2][1:])
            if t_id not in res.keys():
                res[t_id] = {}
            res[t_id][h_id] = tmp[h]

        return res

    # 绘制所有主机的丢包率
    def draw_hosts_pkt_loss(self, t_id=-1):
        avg_pkt_loss = self.parse_server() * 100
        pkt_loss = self.hosts_pkt_loss()
        hosts = []
        title = ''
        if t_id == -1:
            for t_id, dic in pkt_loss.items():
                for h_id, loss in dic.items():
                    hosts.append(loss * 100)
            title = '数据中心主机的丢包率'
        else:
            assert t_id in pkt_loss.keys()
            for h_id, loss in pkt_loss[t_id]:
                hosts.append(loss * 100)
            title = '租户' + str(t_id) + '主机的丢包率'

        # 柱状图
        name_list = ['' * len(hosts)]
        rects = plot.bar(range(len(hosts)), hosts, color='r')
        index = range(len(name_list))
        plot.xticks(index, name_list)
        plot.ylabel("pkt_loss(%)")  # X轴标签
        plot.plot(range(len(hosts)), [avg_pkt_loss] * len(hosts), '-.', linewidth=3.0)
        for rect in rects:
            height = rect.get_height()
            #plot.text(rect.get_x() + rect.get_width() / 2, height, str(height) + '%', ha='center', va='bottom')

        # 平均数

        plot.savefig(FilePath.pkt_loss_fig_path)





