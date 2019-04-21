# -*- coding:utf-8 -*-

from math import ceil

from Util import Util
from Device import Switch, Gateway
from Topo import FatTreeTopo, FullMeshTopo

'''
    Datacenter class
'''
class Datacenter(object):
    def __init__(self, datacenter_id):
        super(Datacenter, self).__init__()

        self.datacenter_id = datacenter_id
        self.tenants = []
        self.switches = []
        self.hosts = []
        self.gateways = []
        self.mac_pool = None
        self.switch_ip_pool = None
        self.gateway_ip_pool = None
        self.topo_conf = None
        self.dc_topo = None
        self.gateway_density = 0

    def __str__(self):
        res = 'Datacenter: %d\n tenant: [' %(self.datacenter_id)
        for t in self.tenants:
            res += str(t.tenant_id) + ', '
        res += ']'
        return res
    '''
        methods to generate components
    '''
    def gen_switches(self):
        topo_type = self.topo_conf[0]
        density = self.topo_conf[1]
        # only generate switches without generate topo
        if topo_type == 'fattree':
            # calculate num of swithces
            host_num = len(self.hosts)
            # fat tree pod
            pod_num = pow(host_num * 4.0, 1.0/3.0)
            pod_num = ceil(pod_num)
            if pod_num % 2 == 1:
                pod_num += 1
            switch_num = int(pod_num * pod_num * 5 / 4)
            for i in range(switch_num):
                switch_name = Util.generate_switch_name(self.datacenter_id, i)
                ip = self.get_usable_switch_ip()
                mac = self.mac_pool.get()
                switch = Switch(name=switch_name, id=i, ip=ip, mac=mac, dc_id=self.datacenter_id)
                self.switches.append(switch)
            return
        elif topo_type == 'fullmesh':
            host_num = len(self.hosts)
            switch_num = int(ceil(float(host_num) / density))
            for i in range(switch_num):
                switch_name = Util.generate_switch_name(self.datacenter_id, i)
                ip = self.get_usable_switch_ip()
                mac = self.mac_pool.get()
                switch = Switch(name=switch_name, id=i, ip=ip, mac=mac, dc_id=self.datacenter_id)
                self.switches.append(switch)
            return

    def gen_gateways(self):
        assert len(self.switches) != 0
        num = int(ceil(len(self.switches) / self.gateway_density))
        for i in range(num):
            name = Util.generate_gateway_name(self.datacenter_id, i)
            ip = self.get_usable_gateway_ip()
            mac = self.mac_pool.get()
            g = Gateway(name=name, id=i, ip=ip, mac=mac, dc_id=self.datacenter_id)
            self.gateways.append(g)
        return

    '''
        methods to create topo
    '''
    def gen_topo(self):
        if self.topo_conf[0] == 'fattree':
            self.create_fattree_topo()
        elif self.topo_conf[1] == 'fullmesh':
            self.create_full_mesh_topo()
        else:
            return

    def create_fattree_topo(self):
        self.dc_topo = FatTreeTopo(self.switches, self.hosts)
        self.dc_topo.create_fattree_topo(bw={})

    def create_full_mesh_topo(self, density):
        self.dc_topo = FullMeshTopo(self.switches, self.hosts, density)
        self.dc_topo.create_full_mesh_topo()

    '''
        methods to get components or relationship
    '''
    def get_tenant_arp_table(self):
        res = {}
        for t in self.tenants:
            tenant_arp_table = t.get_arp_table()
            res[t.tenant_id] = tenant_arp_table
        return res

    '''
        Util
    '''
    def get_usable_switch_ip(self):
        return self.switch_ip_pool.get()

    # TODO 目前仅支持唯一ip
    def get_usable_gateway_ip(self):
        return self.gateway_ip_pool.get_with_index(0)