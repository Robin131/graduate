# -*- coding:utf-8 -*-
import abc
import networkx as nx

# mininet simulator
from mininet.cli import CLI
from mininet.log import setLogLevel, info,error
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink

from const import LinkBandWidth, LinkType
from Util import Util
from Device import Host, Switch, Gateway

'''
    仿真网络层
'''
class NetSimulator(object):
    def __init__(self, topo):
        super(NetSimulator, self).__init__()
        self.topo = topo

    @abc.abstractmethod
    def simulate(self):
        pass

class MininetSimulator(NetSimulator):
    def __init__(self, topo):
        super(MininetSimulator, self).__init__(topo)

        self.hs_bw = LinkBandWidth.host_switch_bw
        self.ss_bw = LinkBandWidth.switch_switch_bw
        self.gs_bw = LinkBandWidth.gateway_switch_bw
        self.ng_bw = LinkBandWidth.nat_gateway_bw

        self.link_type = TCLink

        self.topo = topo
        self.net = Mininet(switch=OVSSwitch, listenPort = 6633)

    # simulate network for a dc
    def simulate(self):
        setLogLevel("info")
        topo = self.topo
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
            net.addSwitch(s.name, ip=s.ip, mac=s.mac, datapath='user')
        for g in gateways:
            net.addSwitch(g.name, ip=g.ip, dpid=Util.dpid_num_2_dpid_hex(g.dpid))

        # add link
        for edge in topo.graph.edges:
            self.add_link(edge)

        net.start()
        CLI(net)
        net.stop()

    # 依据拓扑边的属性添加连接
    def add_link(self, edge):
        node1 = edge[0]
        node2 = edge[1]

        link_type = Util.get_link_type(node1, node2)
        g = self.topo.graph
        bw = nx.get_edge_attributes(g, 'bw')
        ports = nx.get_edge_attributes(g, 'port')

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
            port = ports[node1, node2]
            node1_port = port[node1.name]
            node2_port = port[node2.name]
            link_bw = bw[node1, node2]

            if link_bw == 0:
                if link_type == LinkType.ss_link:
                    link_bw = LinkBandWidth.switch_switch_bw
                elif link_type == LinkType.gs_link:
                    link_bw = LinkBandWidth.gateway_switch_bw
                elif link_type == LinkType.gg_link:
                    link_bw = LinkBandWidth.gateway_gateway_bw

            self.net.addLink(node1.name, node2.name, node1_port, node2_port, cls=self.link_type, bw=link_bw)
            return

        # TODO 增加NAT连接
        return

