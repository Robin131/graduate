# -*- coding:utf-8 -*-
import gc
import abc
from math import exp,ceil, floor
from scipy import stats
from random import choice

from Util import Util as U
from const import SimulateModelType, SimulateModelParameter, SimulateFlowParameter


'''
    数据流基类
'''
class Flow(object):
    def __init__(self, src, dst, size, duration=0, start_time=0):
        self.src = src
        self.dst = dst
        self.size = size
        self.duration = duration
        self.start_tmie = start_time



'''
    流产生器基类(每个数据中心含有一个)
    需要注意的问题：
        每个交换机的flow数为每分钟1500-4000个           **作为参数 flow_num_per_min (per  host)
        每个流的间隔时间为300-2000微秒(0.3 ~ 2 毫秒)
        流的大小和数量呈重尾分布                        **考虑作为参数
        80%的流是内部流量                              **作为参数
        流量变化有周期性                               **作为参数
        时间长度                                      **作为参数
    可变参数：
        inner_percent
'''

class FlowGenerator(object):

    def __init__(self, datacenter, **kwargs):
        super(FlowGenerator, self).__init__()

        self.datacenter = datacenter
        self.hosts = datacenter.hosts

        self.inner_percent = 0
        self.outer_percent = 0
        self.flow_per_host_per_min = SimulateFlowParameter.flow_per_host_per_min


        self.model = None
        self.host_dic = {}              # {tenant_id -> {ip: [hosts]}}
        self.flows = {}                 # {flow_id -> flow}
        self.flow_seq = {}              # {time_seq -> [flow_id]}


        self.init(kwargs)

    # 解析可变参数列表
    def decode_kwargs(self, kwargs):
        if 'inner_percent' in kwargs.keys():
            self.inner_percent = kwargs['inner_percent']
            self.outer_percent = 1 - self.inner_percent
        else:
            self.inner_percent = SimulateFlowParameter.inner_percent
            self.outer_percent = 1 - self.inner_percent

    def init(self, kwargs):
        self.decode_kwargs(kwargs)
        self.divide_hosts()
        self.flow_model = self.set_flow_model()

    # 根据租户及其不同子网划分host
    def divide_hosts(self):
        host_dic = self.host_dic
        for t in self.datacenter.tenants:
            dic = host_dic[t.tenant_id] = {}
            for ip in t.subnets:
                dic[ip] = []
        for h in self.hosts:
            t_id = h.t_id
            for subnet in host_dic[t_id].keys():
                if U.is_in_subnet(h.ip, subnet):
                    host_dic[t_id][subnet].append(h)
        return

    # 随机生成一对可以通信的hosts
    def inner_pair(self):
        h1 = choice(self.hosts)
        dic = self.host_dic[h1.t_id]
        hosts = []
        for subnet in dic.keys():
            if U.is_in_subnet(h1.ip, subnet):
                hosts = dic[subnet]
        assert len(hosts) > 0
        if hosts == 1:
            return h1, h1
        h2 = h1
        while h2 == h1:
            h2 = choice(hosts)
        return h1, h2

    # 获得生成流的模型
    @abc.abstractmethod
    def set_flow_model(self):
        pass

    # 生成时间间隔为一分钟的域内流量
    @abc.abstractmethod
    def generate_inner_flow(self):
        pass

    # 生成时间间隔为一分钟的域外流量
    @abc.abstractmethod
    def generate_outer_flow(self):
        pass


'''
    流数量与流大小符合重尾分布的流模型
    可调整参数
        正态分布的平均数 mu
        正态分布的方差 sigma
'''
class LognormFlowGenerator(FlowGenerator):
    def __init__(self, datacenter, **kwargs):
        self.parameter = kwargs

        super(LognormFlowGenerator, self).__init__(datacenter, **kwargs)

        self.model_type = SimulateModelType.LOGNORM


    def set_flow_model(self):
        para = self.parameter
        mu = para['mu'] if 'mu' in para.keys() else SimulateModelParameter.parameter[self.model_type]['mu']
        sigma = para['sigma'] if 'sigma' in para.keys() else SimulateModelParameter.parameter[self.model_type]['sigma']
        return stats.lognorm(s=sigma, scale=exp(mu))

    # 生成不含时间信息的流
    def generate_inner_flow_per_min(self):
        flow_per_min = self.flow_per_host_per_min * len(self.hosts)
        # 每分钟的内部流量总数
        inner_flow_per_min = ceil(flow_per_min * self.inner_percent)
        flows = []
        for i in xrange(inner_flow_per_min):
            size = self.model.rvs()
            src, dst = self.inner_pair()
            if src == dst:
                continue
            flow = Flow(src=src, dst=dst, size=size)
            flows.append(flow)
        return flows

    # 模拟时间周期生成每秒要发送的百分比（目前先使用均匀分布）
    def generate_percent_per_time_unit(self):
        duration = 60
        unit = 1
        percent_per_unit = 1.0 / duration
        percent = [percent_per_unit] * 60
        return percent

    # TODO 通过概率分布得到一分钟内的流个数
    def generate_inner_flow_num_per_min(self):
        flow_per_min = self.flow_per_host_per_min * len(self.hosts)
        return ceil(flow_per_min * self.inner_percent)

    # 生成一分钟的内部流量
    def generate_inner_flow(self):
        flow_per_min = self.flow_per_host_per_min * len(self.hosts)
        # 每分钟的内部流量总数
        inner_flow_per_min = self.generate_inner_flow_num_per_min()

        percents = self.generate_percent_per_time_unit()

        flow_id = 0
        time_seq = 0
        for i in xrange(len(percents)):
            self.flow_seq[time_seq] = []
            flow_num = floor(percents[i] * inner_flow_per_min)
            sizes = self.model.rvs(size=flow_num)
            for s in sizes:
                src, dst = self.inner_pair()
                if src == dst:
                    continue
                flow = Flow(src=src, dst=dst, size=s, start_time=time_seq)
                self.flows[flow_id] = flow
                self.flow_seq[time_seq].append(flow)
                flow_id += 1
            time_seq += 1
        return self.flows, self.flow_seq

    # 生成一分钟外部的流量
    def generate_outer_flow(self):
        return
