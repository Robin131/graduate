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
    Host类
'''
class Host(Device):
    def __init__(self, name, id, ip, mac, dc_id, t_id=0):
        super(Host, self).__init__(name, id, ip, mac, dc_id)

        self.t_id = t_id

    def __str__(self):
        sup = super(Host, self).__str__()
        return sup + ', tenant: %d\n'%(self.t_id)

    def is_in(self, tenant):
        return self.t_id == tenant.tenant_id

'''
    Switch类
'''
# TODO 交换机端口信息是否要存储？
class Switch(Device):
    def __init__(self, name, id, ip, mac, dc_id):
        super(Switch, self).__init__(name, id, ip, mac, dc_id)

'''
    Gateway class
    数据中心配置需要确定每个gateway在哪个数据中心中 & 每个端口连接哪个数据中心 {dp_if:{dc_id:port_id}}
'''
# TODO 记录该交换机通过那个端口连接哪个dc
class Gateway(Switch):
    def __init__(self, name, id, ip, mac, dc_id):
        super(Gateway, self).__init__(name, id, ip, mac, dc_id)
        self.neighbor = {}

