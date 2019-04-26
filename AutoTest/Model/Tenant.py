# -*- coding:utf-8 -*-
from random import sample

from Util import Pool, Util
from Device import Host

'''
    Tenant class
'''
class Tenant(object):
    def __init__(self, tenant_id, mac_pool):
        super(Tenant, self).__init__()

        self.tenant_id = tenant_id
        self.priority = 0
        self.datacenters = []
        self.hosts = []
        self.subnet = []                    # list of ip str

        self.mac_pool = mac_pool
        self.ip_pool = []                   # list of ip pool

        self.host_num = 0


    def __str__(self):
        res = 'Tenant %d\n priority: %d, scale: %d, datacenter: ['%(self.tenant_id, self.priority, self.scale)
        for dc in self.datacenters:
            res += str(dc.datacenter_id) + ', '
        res += ']'
        return res

    '''
        生成组件，用于初始化
    '''
    # 设置子网,生成ip池
    def set_subnet_pool(self, ip, max_host):
        self.subnet.append(ip)
        ip_pool = Pool(Util.generate_IPs(ip, max_host))
        self.ip_pool.append(ip_pool)
        for dc in self.datacenters:
            if ip not in dc.subnets:
                dc.subnets.append(ip)
        return

    # 生成hosts
    def gen_hosts(self):
        hosts = []
        for i in xrange(self.host_num):
            name = Util.generate_host_name(self.tenant_id, i + 1)
            h_id = i + 1
            ip = self.get_usable_ip()
            mac = self.get_usable_mac()
            dc = sample(self.datacenters, 1)[0]
            dc_id = dc.datacenter_id
            h = Host(name, h_id, ip, mac, dc_id, self.tenant_id)
            self.hosts.append(h)
            dc.hosts.append(h)
            hosts.append(h)
        return hosts

    '''
        获取组件的值
    '''
    def get_usable_ip(self):
        ip_pool = sample(self.ip_pool, 1)[0]
        return ip_pool.get()

    def get_usable_mac(self):
        return self.mac_pool.get()

    '''
        获取controller配置信息
    '''
    # {ip -> mac}
    def get_arp_table(self):
        res = {}
        for host in self.hosts:
            res[str(host.ip)] = host.mac
        return res