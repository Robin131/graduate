# -*- coding:utf-8 -*-
import matplotlib.pyplot as plt
import networkx as nx

if __name__ == '__main__':
    G = nx.Graph()

    G.add_node('s1', type='Switch')
    G.add_node('s2', type='Switch')
    G.add_node('h1', type='Host')

    G.add_edge('s1', 's2')
    G.add_edge('s1', 'h1')

    for n in G.nodes:
        if G.nodes[n]['type'] == 'Switch':
            print n

    for e in G.edges:
        print e[0], e[1]