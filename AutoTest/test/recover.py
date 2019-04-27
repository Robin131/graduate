import cPickle as pickle
import sys
sys.path.append('../..')

from AutoTest.Model.Network import pickle_file, config_dic


if __name__ == '__main__':
    this_dc = 1
    with open(pickle_file, "rb") as f:
        network = pickle.load(f)
        f.close()


    network.set_up_mininet(this_dc)


    # dc = network.datacenters[this_dc]
    # for s in dc.switches:
    #    if s.name == 's00100004':
    #        s.show_inner_ports()
