# -*- coding:utf-8 -*-
import networkx as nx
import random
import matplotlib.pyplot as plt

from math import sqrt


class DC_Topo(object):
    def __init__(self, hosts, switches, gateways):
        super(DC_Topo, self).__init__()

        self.graph = nx.Graph()
        self.hosts = hosts
        self.switches = switches
        self.gateways = gateways

    # 为两个交换机或一个交换机一个网关增加连接
    def add_inner_link(self, s1 ,s2, bw):
        # 确保是一个内部连接
        s1_g = s1 in self.gateways
        s1_s = s1 in self.switches
        s2_g = s2 in self.gateways
        s2_s = s2 in self.switches
        assert s1_g and s2_s or s1_s and s2_g or s1_s and s2_s

        self.graph.add_edge(
            s1, s2,
            bw=bw,
            port={
                s1.name: s1.current_port,
                s2.name: s2.current_port
            }
        )
        s1.add_inner_connect(s2, bw)
        s2.add_inner_connect(s1, bw)
        return

    # show how switches and hosts connect with others
    def show_structrue(self):
        g = self.graph
        T = nx.get_node_attributes(g, 'type')
        for n in self.graph.nodes:
            print(T[n])
            print(n.name)
            for e in g.edges:
                if n.equals(e[0]):
                    print('%s, %s' % (n.name, e[1].name))
                elif n.equals(e[1]):
                    print('%s, %s' % (n.name, e[0].name))
                else:
                    continue
            print('\n')

class FatTreeTopo(DC_Topo):
    def __init__(self, hosts, switches, gateways):
        super(FatTreeTopo, self).__init__(hosts, switches, gateways)

        self.pod = 0
        self.core_num = 0
        self.aggre_num = 0
        self.edge_num = 0
        self.density = 0

        self.core_switch = []
        self.aggre_switch = []
        self.edge_switch = []

    # TODO add bw to links
    def create_fattree_topo(self, bw):

        switches = self.switches
        hosts = self.hosts

        switch_num = len(switches)
        self.pod = int(sqrt(switch_num * 4.0 / 5.0))
        self.core_num = int((self.pod / 2) ** 2)
        self.aggre_num = int(self.pod * self.pod / 2)
        self.edge_num = self.aggre_num
        self.density = int((self.pod / 2) ** 2)         # TODO 此处可自定义密度

        # connect switches
        core_end = self.core_num
        aggre_end = core_end + self.aggre_num
        self.core_switch = switches[:core_end]
        self.aggre_switch = switches[core_end : aggre_end]
        self.edge_switch = switches[aggre_end:]

        self.graph.add_nodes_from(self.core_switch, type='Core')
        self.graph.add_nodes_from(self.aggre_switch, type='Aggr')
        self.graph.add_nodes_from(self.edge_switch, type='Edge')

        # no host in this datacenter
        if self.pod == 0:
            return

        # add link between core and aggregation
        end = int(self.pod / 2)
        for x in xrange(0, self.aggre_num):
            for i in xrange(x % end, self.core_num, end):
                self.add_inner_link(
                    self.core_switch[i],
                    self.aggre_switch[x],
                    bw=0
                )

        # add link between aggregation and edge
        for x in xrange(0, self.aggre_num, end):
            for i in xrange(0, end):
                for j in xrange(0, end):
                    self.add_inner_link(
                        self.aggre_switch[x + i],
                        self.edge_switch[x + j],
                        bw=0
                    )

        # connect hosts
        host_group = []
        self.graph.add_nodes_from(hosts, type='Host')
        host_index = range(len(hosts))
        while len(host_index) > self.density:
            pick = random.sample(host_index, self.density)
            host_group.append(pick)
            for i in pick:
                host_index.remove(i)
        host_group.append(host_index)

        for i in range(0, len(self.edge_switch)):
            if i >= len(host_group):
                break
            for h_index in host_group[i]:
                self.graph.add_edge(hosts[h_index],self.edge_switch[i])
                self.edge_switch[i].add_inner_connect(hosts[h_index], bw=0)

        # connect gateways
        for s in self.switches:
            for g in self.gateways:
                self.add_inner_link(s, g, bw=0)
        return


class FullMeshTopo(DC_Topo):
    def __init__(self, hosts, switches, gateways, density):
        super(FullMeshTopo, self).__init__(hosts, switches, gateways)

        self.density = density

    # TODO add bw to links
    def create_full_mesh_topo(self, bw):

        hosts = self.hosts
        switches = self.switches

        # connect switches
        self.graph.add_nodes_from(switches, type='Switch')
        for s1 in switches:
            for s2 in switches:
                if not s1.equals(s2):
                    self.add_inner_link(s1, s2, bw=0)

        # connect hosts
        host_group = []
        self.graph.add_nodes_from(hosts, type='Host')
        host_index = range(len(hosts))
        while len(host_index) > self.density:
            pick = random.sample(host_index, self.density)
            host_group.append(pick)
            for i in pick:
                host_index.remove(i)
        host_group.append(host_index)

        i = 0
        for s in switches:
            if i == len(host_group):
                break
            else:
                for h_index in host_group[i]:
                    self.graph.add_edge(s, hosts[h_index])
                    s.add_inner_connect(hosts[h_index], bw=0)
                i += 1

        # connect gateways
        for s in self.switches:
            for g in self.gateways:
                self.add_inner_link(s, g, bw=0)

        return


'''
    测试用线性拓扑
'''
class LinearTopo(DC_Topo):
    def __init__(self, hosts, switches, gateways, density):
        super(LinearTopo, self).__init__(hosts, switches, gateways)

        self.density = density

    def create(self, bw):
        hosts = self.hosts
        switches = self.switches

        # connect switch in line
        self.graph.add_nodes_from(switches, type='Switch')
        for i in xrange(len(switches)):
            if i == len(switches) - 1:
                break
            s1 = switches[i]
            s2 = switches[i + 1]
            self.add_inner_link(s1, s2, bw=0)

        # connect hosts
        host_group = []
        self.graph.add_nodes_from(hosts, type='Host')
        host_index = range(len(hosts))
        while len(host_index) > self.density:
            pick = random.sample(host_index, self.density)
            host_group.append(pick)
            for i in pick:
                host_index.remove(i)
        host_group.append(host_index)

        i = 0
        for s in switches:
            if i == len(host_group):
                break
            else:
                for h_index in host_group[i]:
                    self.graph.add_edge(s, hosts[h_index])
                    s.add_inner_connect(hosts[h_index], bw=0)
                i += 1

        # TODO connect gateways


        return
