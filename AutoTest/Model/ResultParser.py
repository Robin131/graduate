# -*- coding:utf-8 -*-

import os
import re

from const import FilePath

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


    def parse_server(self):

        pkt_loss_arg = r'([0-9]+)\ *\/\ *([0-9]+)'
        pkt_received = 0
        pkt_sent = 0

        ls = os.listdir(self.sever_path)
        for file in ls:
            if os.path.isdir(file):
                continue
            with open(file, 'r') as f:
                raw = f.readlines()
                for line in raw:
                    result = re.search(pkt_loss_arg, line)
                    if result.groups():
                        pkt_sent += result.group(1)
                        pkt_received += result.group(2)
                    else:
                        continue
        pkt_loss = pkt_sent - pkt_received / pkt_sent
        print(pkt_loss)

