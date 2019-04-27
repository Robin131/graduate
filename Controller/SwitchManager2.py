# -*- coding: utf-8 -*-
import copy
from MacManager2 import MacManager
from FlowManager2 import FlowManager


# flow entry for switch
# 0 : src_pmac -> src_vmac                                              ok
# 1 : dst_vmac -> dst_pmac                                              ok
# 2 : receiving flow entry (send pkt to host)                           ok
# 3 : check whether ip_dst is public or private (yes 4, no 8)(arp)      ok
# 4 : check whether dst_vmac is a gateway address (yes 5, no 6)         ok
# 5 : add dst_mac according to ip, send to 6                            ok
# 6 : check whether dst_vmac is in local datacenter (yes 7, no 8)       ok
# 7 : send in local datacenter                                          ok
# 8 : send to gateway according to host_vmac                            ok

# 0 : ez
# 1 : ez （仅将在本ovs的数据包改变）
# 2 : ez
# 3 : 判断目标ip是公网ip还是私网ip，（如果是公网到8,私网到4）,arp直接送到controller
# 4 : 查看目的地mac是否是网关mac（是的话到5，否则到6）
# 5 : 根据ip替换目的地mac（使得本地流量包不经过网关），送至6
# 6 : 检查目的mac地址是否处于本数据中心（是的话送到7，否则到8）
# 7 : 本地路由
# 8 : 将数据包送至网关（根据host_mac地址的round robin结果）

# 不同数据包的处理流程
# 发往公网的数据包：0, 1, 2, 3, 8
# 同域同子网：0, 1, 2, 3, 4, 6, 7
# 同域跨子网：0, 1, 2, 3, 4, 5, 6, 7
# 跨域同子网：0, 1, 2, 4, 6, 8
# 跨域跨子网：0, 1, 2, 3, 4, 5, 6, 8

class SwitchManager(object):
    def __init__(self,
                 datapathes,
                 dpid_to_ports,
                 dpid_to_vmac,
                 lldp_manager,
                 meters,
                 subnets,
                 potential_gateway):
        super(SwitchManager, self).__init__()

        self.datapathes = datapathes
        self.dpid_to_ports = dpid_to_ports
        self.dpid_to_vmac = dpid_to_vmac
        self.lldp_manager = lldp_manager
        self.meters = meters
        self.subnets = subnets
        self.potential_gateway = potential_gateway

    def register_switch(self, ev):
        datapath = ev.datapath
        dpid = datapath.id
        self.datapathes[dpid] = datapath

        ports = copy.copy(datapath.ports)
        self.dpid_to_ports[dpid] = ports

        # choose datatcenter_id according to dpid
        # if dpid == 1 or dpid == 2 or dpid == 3 or dpid == 10 or dpid == 11 or dpid == 12:
        #     datacenter_id = 1
        # else:
        #     datacenter_id = 2
        # TODO only for datacenter 1 right now
        datacenter_id = 1
        vmac = MacManager.get_vmac_new_switch(dpid=dpid, datacenter_id=datacenter_id)
        self.dpid_to_vmac[dpid] = vmac
        self.lldp_manager.lldp_detect(datapath)

        if dpid in self.potential_gateway.keys():
            return

        FlowManager.install_subnet_flow(ev, self.subnets)       # 区别dst_ip是否为公网ip
        FlowManager.install_adjust_datacenter_flow(ev, datacenter_id)   # 判断dst_mac是否在本数据中心
        FlowManager.install_missing_flow_for_switch(ev)

        self.meters[dpid] = {}

    # TODO finish this function
    def unregister_switch(self, datapath):
        return

