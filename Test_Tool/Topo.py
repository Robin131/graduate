import networkx as nx
import random
import matplotlib.pyplot as plt

from math import sqrt


class DC_Topo(object):
    def __init__(self):
        super(DC_Topo, self).__init__()

        self.graph = nx.Graph()
        self.hosts = []
        self.switches = []

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
    def __init__(self,switches, hosts):
        super(FatTreeTopo, self).__init__()

        self.pod = 0
        self.core_num = 0
        self.aggre_num = 0
        self.edge_num = 0
        self.density = 0

        self.switches = switches
        self.hosts = hosts

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
        self.density = int((self.pod / 2) ** 2)

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
                self.graph.add_edge(
                        self.core_switch[i],
                        self.aggre_switch[x],
                )

        # add link between aggregation and edge
        for x in xrange(0, self.aggre_num, end):
            for i in xrange(0, end):
                for j in xrange(0, end):
                    self.graph.add_edge(
                        self.aggre_switch[x + i],
                        self.edge_switch[x + j]
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
                self.graph.add_edge(
                    hosts[h_index],
                    self.edge_switch[i]
                )
        return


class FullMeshTopo(DC_Topo):
    def __init__(self, switches, hosts, density):
        super(FullMeshTopo, self).__init__()

        self.switches = switches
        self.hosts = hosts
        self.density = density

    def create_full_mesh_topo(self):

        # TODO
        # print(len(self.switches))
        # print(len(self.hosts))
        # print(self.density)

        hosts = self.hosts
        switches = self.switches

        # connect switches
        self.graph.add_nodes_from(switches, type='Switch')
        for s1 in switches:
            for s2 in switches:
                if not s1.equals(s2):
                    self.graph.add_edge(s1, s2)

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
                i += 1

        # if switches[0].dc_id == 1:
        #     self.show_structrue()

        return















