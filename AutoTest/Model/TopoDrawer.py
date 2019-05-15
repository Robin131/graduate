# -*- coding:utf-8 -*-
import matplotlib.pyplot as plot
import networkx as nx

from const import DrawerArgs

class TopoDrawer(object):
    def __init__(self, graph):
        self.graph = graph

    def draw_switch(self):
        g = self.graph

        s_nodes = []
        s_edges = []

        for n in g.nodes:
            if g.nodes[n]['type'] == 'Switch':
                s_nodes.append(n)

        for e in g.edges:
            if g.nodes[e[0]]['type'] == 'Switch' and g.nodes[e[1]]['type'] == 'Switch':
                s_edges.append(e)

        pos = nx.spring_layout(g)
        nx.draw_networkx_nodes(g, pos=pos, nodelist=s_nodes, node_color='b')
        nx.draw_networkx_edges(g, pos=pos, edgelist=s_edges)
        self.show()

    def draw_switch_gateway(self):
        g = self.graph
        nodes = []
        node_color = []
        edges = []

        for n in g.nodes:
            if g.nodes[n]['type'] == 'Switch':
                nodes.append(n)
                node_color.append(DrawerArgs.switch_color)
            elif g.nodes[n]['type'] == 'Gateway':
                nodes.append(n)
                node_color.append(DrawerArgs.gateway_color)

        for e in g.edges:
            if g.nodes[e[0]]['type'] == 'Switch' and g.nodes[e[1]]['type'] == 'Switch':
                edges.append(e)
            elif g.nodes[e[0]]['type'] == 'Switch' and g.nodes[e[1]]['type'] == 'Gateway':
                edges.append(e)
            elif g.nodes[e[1]]['type'] == 'Switch' and g.nodes[e[0]]['type'] == 'Gateway':
                edges.append(e)
            elif g.nodes[e[0]]['type'] == 'Gateway' and g.nodes[e[1]]['type'] == 'Gateway':
                edges.append(e)

        pos = nx.spring_layout(g)
        nx.draw_networkx_nodes(g, pos=pos, nodelist=nodes, node_color=node_color)
        nx.draw_networkx_edges(g, pos=pos, edgelist=edges)

        self.show()

    def show(self):
        plot.show()