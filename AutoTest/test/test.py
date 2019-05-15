# -*- coding:utf-8 -*-
from AutoTest.Model.ResultParser import MultiThreadOutFileResultParser


if __name__ == '__main__':
    parser = MultiThreadOutFileResultParser()
    parser.draw_hosts_pkt_loss()