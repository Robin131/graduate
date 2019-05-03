# -*- coding:utf-8 -*-
import abc
import time
import cPickle as pickle

# mininet simulator
from mininet.cli import CLI
from mininet.log import setLogLevel, info,error
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink

from Net import Net
from const import LinkBandWidth, LinkType
from Util import Util
from Device import Host, Switch, Gateway
from Datacenter import flow_record, flow_seq_record

'''
    仿真网络层
'''
class NetSimulator(object):
    def __init__(self, datacenter):
        super(NetSimulator, self).__init__()
        self.datacenter = datacenter

    @abc.abstractmethod
    def simulate(self):
        pass

class MininetSimulator(NetSimulator):
    def __init__(self, datacenter):
        super(MininetSimulator, self).__init__(datacenter)

        self.hs_bw = LinkBandWidth.host_switch_bw
        self.ss_bw = LinkBandWidth.switch_switch_bw
        self.gs_bw = LinkBandWidth.gateway_switch_bw
        self.ng_bw = LinkBandWidth.nat_gateway_bw

        self.link_type = TCLink

        self.net = Net(switch=OVSSwitch, listenPort = 6633)

    # simulate network for a dc
    def simulate(self, client=True, minute=1):
        setLogLevel("info")
        topo = self.datacenter.topo
        net = self.net

        mycontroller = RemoteController("RemoteController")
        self.net.controllers = [mycontroller]
        self.net.nameToNode["RemoteController"] = mycontroller

        hosts = topo.hosts
        switches = topo.switches
        gateways = topo.gateways

        # add node
        for h in hosts:
            net.addHost(h.name, ip=h.ip, mac=h.mac)
        for s in switches:
            net.addSwitch(s.name, ip=s.ip, mac=s.mac, dpid=Util.dpid_num_2_dpid_hex(s.dpid), datapath='user')
        for g in gateways:
            net.addSwitch(g.name, ip=g.ip, dpid=Util.dpid_num_2_dpid_hex(g.dpid))

        # add link
        for edge in topo.graph.edges:
            self.add_link(edge)

        if client:
            net.start()
            CLI(net)
            net.stop()
            return
        else:
            net.start()
            self.set_up_udp_listener()
            self.simulate_flow(minute=minute)


    # 为所有的主机打开udp监听端口
    def set_up_udp_listener(self):
        hosts = self.datacenter.hosts
        for h in hosts:
            self.net.set_up_udp_listener(h)
        return

    # 根据输入的流信息仿真流
    def simulate_flow(self, minute):
        for i in xrange(minute):
            st = time.time()
            flows = {}
            flow_seq = {}
            with open(flow_record(i), "rb") as f:
                flows = pickle.load(f)
                f.close()
            with open(flow_seq_record(i), "rb") as f:
                flow_seq = pickle.load(f)
                f.close()
            # 1 minute time seq
            for i in xrange(60):
                fs = flow_seq[i]
                for idx in fs:
                    flow = flows[i]
                    src = flow.src
                    dst = flow.dst
                    size = flow.size
                    self.net.udp_flow(src=src, dst=dst, size=size)
            et = time.time()
            print('--- consume time {} ---'.format(et - st))
        return




    # 依据拓扑边的属性添加连接
    def add_link(self, edge):
        node1 = edge[0]
        node2 = edge[1]

        link_type = Util.get_link_type(node1, node2)

        if link_type == LinkType.hs_link:
            if isinstance(node2, Switch):
                port_no, link_bw = node2.get_inner_port_no_with_device(node1)
                link_bw = LinkBandWidth.host_switch_bw if link_bw == 0 else link_bw
                self.net.addLink(node1.name, node2.name, 1, port_no, cls=self.link_type, bw=link_bw)
            else:
                port_no, link_bw = node1.get_inner_port_no_with_device(node2)
                link_bw = LinkBandWidth.host_switch_bw if link_bw == 0 else link_bw
                self.net.addLink(node2.name, node1.name, 1, port_no, cls=self.link_type, bw=link_bw)
            return

        if link_type == LinkType.ss_link or link_type == LinkType.gs_link or link_type == LinkType.gg_link:

            node1_port, bw = node1.get_inner_port_no_with_device(node2)
            node2_port, bw = node2.get_inner_port_no_with_device(node1)

            if bw == 0:
                if link_type == LinkType.ss_link:
                    bw = LinkBandWidth.switch_switch_bw
                elif link_type == LinkType.gs_link:
                    bw = LinkBandWidth.gateway_switch_bw
                elif link_type == LinkType.gg_link:
                    bw = LinkBandWidth.gateway_gateway_bw

            print('{} -- {} with port {} -- {}'.format(node1.name, node2.name, node1_port, node2_port))
            self.net.addLink(node1.name, node2.name, node1_port, node2_port, cls=self.link_type, bw=bw)
            return

        # TODO 增加NAT连接
        return

