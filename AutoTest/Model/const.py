# -*- coding:utf-8 -*-

flow_record = lambda i: '../Data/flow/flow{}.pkl'.format(i)             # 第i分钟的流️信息
flow_seq_record = lambda i: '../Data/flow/flow_seq{}.pkl'.format(i)     # 第i分钟的流序列信息
pickle_file = '../Data/network.pkl'                                     # network文件
config_dic = '../Data/config.pkl'                                       # 配置信息文件
server_result_record = lambda i: '../Data/server_res/server_{}.out'.format(i)      # 服务器结果信息



class TenantPriority(object):
    priority = {
        "LOW": 1,
        "HIGH": 2
    }
    LOW = 1,
    HIGH = 2

class LinkBandWidth(object):
    host_switch_bw = 10
    switch_switch_bw = 10
    gateway_switch_bw = 10
    nat_gateway_bw = 10
    gateway_gateway_bw = 10

class LinkType(object):
    hs_link = 1
    ss_link = 2
    gs_link = 3
    ng_link = 4
    gg_link = 5

class SimulateModelType(object):
    LOGNORM = 1

class SimulateModelParameter(object):
    # {type -> {parameters}}
    parameter = {
        SimulateModelType.LOGNORM:{
            'mu': 10,
            'sigma': 1
        }
    }

class SimulateFlowParameter(object):
    inner_percent = 0.8
    outer_percent = 1 - inner_percent
    flow_per_host_per_min = 30

