# -*- coding:utf-8 -*-
import json

from Errors import Errors
from Datacenter import Datacenter
from Tenant import Tenant
from Util import Pool, Util
from const import TenantPriority


'''
    Network class
'''
class Network(object):
    def __init__(self, conf):
        super(Network, self).__init__()

        self.datacenters = {}               # id -> dc
        self.tenants = {}                   # id -> tenant
        self.alter_IP = {}                  # id -> subnet_ip
        self.mac_pool = None                # Pool of Mac
        self.net = None                     # Mininet instance
        self.hosts = []                     # host list
        self.switches = []

        self.conf_file = conf
        self.conf_dic = {}
        self.init()

    def read_conf(self):
        file = open(self.conf_file, 'r')
        js = file.read()
        dic = json.load(js)
        file.close()
        return dic

    # init from conf file
    def init(self):
        dic =self.read_conf()
        self.conf_dic = dic

        self.gen_mac_pool()
        self.gen_datacenters()
        self.gen_alter_ips()
        self.gen_tenants()
        self.set_topo_type()
        self.gen_switch()
        self.gen_gateway()
        self.gen_topo()

    def gen_datacenters(self):
        if self.conf_dic == {}:
            pass
        dic = self.conf_dic
        datacenter_ids = dic["datacenters"]
        if len(datacenter_ids) == 0:
            raise Errors.no_datacenter_error
        for id in datacenter_ids:
            self.datacenters[id] = Datacenter(id)
            self.datacenters[id].mac_pool = self.mac_pool
        return

    def gen_mac_pool(self):
        if self.conf_dic == {}:
            pass
        dic = self.conf_dic
        mac_num = dic["mac_num"]
        self.mac_pool = Pool(Util.generate_MACs(mac_num))

    def gen_alter_ips(self):
        if self.conf_dic == {}:
            pass
        dic = self.conf_dic
        ips = dic['alter_ip']
        for id, ip in ips.items():
            self.alter_IP[id] = ip
        return

    # 生成租户，
    def gen_tenants(self):
        if self.conf_dic == {}:
            pass
        tenants = self.conf_dic["tenant"]
        for t_id, t_info in tenants.items():
            t = Tenant(t_id, self.mac_pool)
            self.tenants[t_id] = t
            # 设置优先级
            t.priority = TenantPriority.priority[t_info["priority"]]
            # 设置租户和dc的关系
            for dc_id, dc in self.datacenters.items():
                t.datacenters.append(dc)
                self.datacenters[dc_id].tenants.append(t)
            # 设置网段 (存在预置host不在网段的可能)
            host_num = t_info['host_num']
            for ip_id in t_info['alter_ip']:
                ip = self.alter_IP[ip_id]
                t.set_subnet_pool(ip, host_num)
            # 生成的host
            t.host_num = host_num
            t.gen_hosts()
        return

    # 为数据中心设置拓扑类型
    def set_topo_type(self):
        if self.conf_dic == {}:
            pass
        topo_conf = self.conf_dic["topo_type"]
        for dc_id, dc in self.datacenters.items():
            dc.topo_conf = topo_conf

    # 为数据中心生成交换机，最大数目为50
    def gen_switch(self):
        if self.conf_dic == {}:
            pass
        switch_ip = self.conf_dic['switch_ip']
        for dc_id, dc in self.datacenters.items():
            dc.switch_ip_pool = Pool(Util.generate_IPs(switch_ip, 50))
            dc.gen_switch()
        return

    # 为数据中心生成网关，最大数目为10个，且ip唯一
    def gen_gateway(self):
        if self.conf_dic == {}:
            pass
        host_per_gateway = self.conf_dic['hosts_per_gateway']
        gateway_ip = self.conf_dic['gateway_ip']
        for _, dc in self.datacenters.items():
            dc.gateway_ip_pool = Pool(Util.generate_IPs(gateway_ip, 10))
            dc.gateway_density = host_per_gateway
            dc.gen_gateways()
        return

    # 为数据中心生成拓扑
    def gen_topo(self):
        for _, dc in self.datacenters.items():
            dc.gen_topo()





