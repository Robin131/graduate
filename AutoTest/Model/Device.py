# -*- coding:utf-8 -*-
import cPickle as pickle

'''
    设备基础类
'''
class Device(object):
    def __init__(self, name, id, ip, mac, dc_id):
        super(Device, self).__init__()

        self.name = name
        self.id = id
        self.ip = ip
        self.mac = mac
        self.dc_id = dc_id

    def equals(self, device):
        if self.name == device.name:
            return True
        return False

    def __str__(self):
        return 'id: %d, ip:%s, mac: %s, dc_id: %d'%(
            self.id, str(self.ip), self.mac, self.dc_id)
'''
    连通型设备
'''
class ConnectDevice(Device):
    def __init__(self, name, id, ip, mac, dc_id):
        super(ConnectDevice, self).__init__(name, id, ip, mac, dc_id)

        self.current_port = 1
        self.inner_ports = {}       # port_id -> (device, bandwidth)
        self.connected_device = []

    def add_inner_connect(self, device, bw=0):
        if device.name in self.connected_device:
            return
        self.inner_ports[self.current_port] = (device, bw)
        self.current_port += 1
        self.connected_device.append(device.name)

    def get_inner_port_no_with_device(self, device):
        for port_no, val in self.inner_ports.items():
            if device.equals(val[0]):
                return port_no, val[1]
            continue
        return -1, -1

    def show_inner_ports(self):
        print(self.name)
        for port_id, val in self.inner_ports.items():
            print({port_id: (val[0].name, val[1])})

'''
    Host类
'''
class Host(Device):
    def __init__(self, name, id, ip, mac, dc_id, t_id=0, gw_ip=''):
        super(Host, self).__init__(name, id, ip, mac, dc_id)

        self.t_id = t_id
        self.gw_ip = gw_ip

    def __str__(self):
        sup = super(Host, self).__str__()
        return sup + ', tenant: %d\n'%(self.t_id)

    def is_in(self, tenant):
        return self.t_id == tenant.tenant_id

'''
    Switch类
'''
# TODO 交换机端口信息是否要存储？
class Switch(ConnectDevice):
    def __init__(self, name, id, ip, mac, dc_id):
        super(Switch, self).__init__(name, id, ip, mac, dc_id)
        self.dpid = -1

'''
    Gateway class
    数据中心配置需要确定每个gateway在哪个数据中心中 & 每个端口连接哪个数据中心 {dp_if:{dc_id:port_id}}
'''
# TODO 记录该交换机通过那个端口连接哪个dc
class Gateway(Switch):
    def __init__(self, name, id, ip, mac, dc_id):
        super(Gateway, self).__init__(name, id, ip, mac, dc_id)

        self.outer_ports = {}  # port_id -> (device, datacenter)

    def add_outer_connect(self, device, dc):
        if device.name in self.connected_device:
            return
        self.outer_ports[self.current_port] = (device, dc)
        self.current_port += 1
        self.connected_device.append(device)

    # 返回连接某一数据中心的端口以及远端的gateway dpid
    # return port_no, peer_dpid
    def get_peer_with_remote_dc_id(self, dc_id):
        if dc_id == self.dc_id:
            return -1, -1
        for port_no, val in self.outer_ports.items():
            dc = val[1]
            if dc_id != dc.datacenter_id:
                continue
            remote_g = val[0]
            return port_no, remote_g.dpid
