# -*- coding:utf-8 -*-
import cPickle as pickle

# mininet simulator



'''
    仿真网络层
'''
class NetSimulator(object):
    def __init__(self, topo):
        super(NetSimulator, self).__init__()

        self.topo = topo



class MininetSinulator(NetSimulator):
    def __init__(self, topo):
        super(MininetSinulator, self).__init__(topo)

