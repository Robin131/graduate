# -*- coding:utf-8 -*-
import json
import cPickle as pickle


from Errors import Errors
from Datacenter import Datacenter
from Tenant import Tenant
from Util import Pool, Util
from const import TenantPriority, pickle_file, config_dic


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
        dic = json.loads(js)
        file.close()
        return dic

    # init from conf file
    def init(self):
        dic = self.read_conf()
        self.conf_dic = dic
        self.gen_mac_pool()
        self.gen_datacenters()
        self.gen_alter_ips()
        self.gen_tenants()
        self.set_topo_type()
        self.gen_switch()
        self.gen_gateway()
        self.gen_inner_topo()
        self.gen_outer_topo()
        self.allocate_dpid()

        # print(len(self.datacenters[1].gateways))
        # print(self.get_dc_statistics())
        # dc_config = self.dc_config_info()
        # print(dc_config)

    def gen_datacenters(self):
        if self.conf_dic == {}:
            pass
        if "datacenters" not in self.conf_dic.keys():
            raise Errors.conf_no_datacenters
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
            raise Errors.no_conf
        if "mac_num" not in self.conf_dic.keys():
            raise Errors.conf_no_mac_num
        dic = self.conf_dic
        mac_num = dic["mac_num"]
        self.mac_pool = Pool(Util.generate_MACs(mac_num))

    def gen_alter_ips(self):
        if self.conf_dic == {}:
            pass
        if "alter_ip" not in self.conf_dic.keys():
            raise Errors.conf_no_mac_num
        dic = self.conf_dic
        ips = dic['alter_ip']
        for id, ip in ips.items():
            id = int(id)
            self.alter_IP[id] = ip
        return

    # 生成租户
    def gen_tenants(self):
        if self.conf_dic == {}:
            pass
        if "tenant" not in self.conf_dic.keys():
            raise Errors.conf_no_tenant
        tenants = self.conf_dic["tenant"]
        for t_id, t_info in tenants.items():
            t_id = int(t_id)
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
            hosts = t.gen_hosts()
            self.hosts.extend(hosts)
        return

    # 为数据中心设置拓扑类型
    def set_topo_type(self):
        if self.conf_dic == {}:
            pass
        if "topo_type" not in self.conf_dic.keys():
            raise Errors.conf_no_topo_type
        topo_conf = self.conf_dic["topo_type"]
        for dc_id, dc in self.datacenters.items():
            dc.topo_conf = topo_conf

    # 为数据中心生成交换机，最大数目为50
    def gen_switch(self):
        if self.conf_dic == {}:
            pass
        if "switch_ip" not in self.conf_dic.keys():
            raise Errors.conf_no_switch_ip
        if "hosts_per_switch" not in self.conf_dic.keys():
            raise Errors.conf_no_hosts_per_switch
        switch_ip = self.conf_dic['switch_ip']
        hosts_per_switch = self.conf_dic['hosts_per_switch']
        for dc_id, dc in self.datacenters.items():
            dc.switch_ip_pool = Pool(Util.generate_IPs(switch_ip, 50))
            dc.switch_density = hosts_per_switch
            dc.gen_switch()
        return

    # 为数据中心生成网关，最大数目为10个，且ip唯一
    def gen_gateway(self):
        if self.conf_dic == {}:
            pass
        if "hosts_per_gateway" not in self.conf_dic.keys():
            raise Errors.conf_no_hosts_per_gateway
        if "gateway_ip" not in self.conf_dic.keys():
            raise Errors.conf_no_gateway_ip
        host_per_gateway = self.conf_dic['hosts_per_gateway']
        gateway_ip = self.conf_dic['gateway_ip']
        for _, dc in self.datacenters.items():
            dc.gateway_ip_pool = Pool(Util.generate_IPs(gateway_ip, 10))
            dc.gateway_density = host_per_gateway
            dc.gen_gateways()
        return

    # 为数据中心生成内部拓扑
    def gen_inner_topo(self):
        for _, dc in self.datacenters.items():
            dc.gen_topo()

    # 生成数据中心间的连接关系
    def gen_outer_topo(self):
        for dc_id1, dc1 in self.datacenters.items():
            for dc_id2, dc2 in self.datacenters.items():
                if dc_id1 == dc_id2:
                    continue
                dc2_g_num = len(dc2.gateways)
                for i in range(len(dc1.gateways)):
                    dc1.gateways[i].add_outer_connect(
                        dc2.gateways[i % dc2_g_num],
                        dc2
                    )
        return

    # 为交换机和网关分配dpid
    def allocate_dpid(self):
        for _, dc in self.datacenters.items():
            dc.allocate_dpid()
        return


    '''
        建立mininet仿真
        需要输入本数据中心的id（需要在本地恢复Network配置后调用）
    '''
    def set_up_mininet(self, dc_id, client=True, minute=1):
        if dc_id not in self.datacenters.keys():
            raise Errors.datacenter_id_not_covered
        self.datacenters[dc_id].set_up_mininet(client=client, minute=minute)
        return

    # 为某个数据中心生成仿真的数据流记录
    def generate_flow(self, dc_id, minute=1):
        if dc_id not in self.datacenters.keys():
            raise Errors.datacenter_id_not_covered
        dc = self.datacenters[dc_id]
        dc.generate_flow(minute=1)
        return


    '''
        返回数据中心需要的配置信息，对于每个数据中心，格式为
        'arp_table': 每个租户的arp信息
        'host_mac': 每个主机mac地址与t_id的对应关系
        'tenant_level':t_id与优先级关系
        'subnets': 所有ip网段
        'potential_gateway': gw_dpid -> {dc_id, port_id}
        'gateway_datacenter_port': {dc_id -> {gw_dpid -> peer}}
        'gateway_id': 可能的gateway ip
        'tenant_speed': 传输速率
        'all_datacenter_id': 所有的数据中心id
    '''

    def dc_config_info(self):
        config = {}
        for dc_id, dc in self.datacenters.items():
            dc_config = {}
            arp_table = dc.get_arp_table()
            dc_config['arp_table'] = arp_table
            host_mac = dc.get_mac_tenant_table()
            dc_config['host_mac'] = host_mac
            tenant_level = dc.get_tenant_priority()
            dc_config['tenant_level'] = tenant_level
            dc_config['subnets'] = dc.subnets
            potential_gateway = dc.get_potential_gateway()
            dc_config['potential_gateway'] = potential_gateway
            gateway_datacenter_port = self.get_gateway_datacenter_port(dc_id)
            dc_config['gateway_datacenter_port'] = gateway_datacenter_port
            dc_config['gateway_ip'] = dc.get_gateway_ips()
            dc_config['tenant_speed'] = {}
            dc_config['all_datacenter_id'] = [dc_id_ for dc_id_ in self.datacenters.keys()]

            config[dc_id] = dc_config
        return config


    # 获取某个数据中心各个网关连接其他数据中心网关的情况
    def get_gateway_datacenter_port(self, dc_id):
        res = {}
        dc = self.datacenters[dc_id]
        for dc_id1, dc1 in self.datacenters.items():
            if dc_id1 == dc_id:
                continue
            gateway = {}
            for g in dc.gateways:
                dpid = g.dpid
                port_no, peers = g.get_peer_with_remote_dc_id(dc_id1)
                gateway[dpid] = peers
            res[dc_id1] = gateway
        return res

    # 将Network以及配置文件进行保存，同时生成对应时长的数据流文件
    def save(self, minute):
        # 自身
        with open(pickle_file, "wb") as f:
            pickle.dump(self, f)
            f.close()
        # 配置文件
        with open(config_dic, "wb") as f:
            pickle.dump(self.dc_config_info(), f)
            f.close()

    # TODO 获取dc统计数量，用于debug
    def get_dc_statistics(self):
        res = {}
        for dc_id, dc in self.datacenters.items():
            d = {}
            d['real_switch_num'] = len(dc.switches)
            d['real_host_num'] = len(dc.hosts)
            d['real_gateway_num'] = len(dc.gateways)
            res[dc_id] = d
        return res


