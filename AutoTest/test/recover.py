import cPickle as pickle
import sys
sys.path.append('../..')

from AutoTest.Model.Network import pickle_file


if __name__ == '__main__':
    this_dc = 1
    with open(pickle_file, "rb") as f:
        network = pickle.load(f)

    dc = network.datacenters[this_dc]
    for s in dc.switches:
        if s.name == 's00100006' or s.name == 's00100001':
            s.show_inner_ports()

