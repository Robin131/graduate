# -*- coding:utf-8 -*-
import matplotlib.pyplot as plot
import networkx as nx


# -*- coding:utf-8 -*-
import matplotlib.pyplot as plot
import networkx as nx



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
                node_color.append('b')
            elif g.nodes[n]['type'] == 'Gateway':
                nodes.append(n)
                node_color.append('r')

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

if __name__ == '__main__':
    G = nx.Graph()

    G.add_node('s1', type='Switch')
    G.add_node('s2', type='Switch')
    G.add_node('h1', type='Host')
    G.add_node('g1', type='Gateway')

    G.add_edge('s1', 's2')
    G.add_edge('s1', 'h1')
    G.add_edge('g1', 's1')

    drawer = TopoDrawer(G)
    drawer.draw_switch_gateway()