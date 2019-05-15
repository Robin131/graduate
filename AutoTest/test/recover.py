import cPickle as pickle
import sys
sys.path.append('../..')

from AutoTest.Model.Network import pickle_file, config_dic
from AutoTest.Model.TopoDrawer import TopoDrawer

if __name__ == '__main__':
    this_dc = 1
    with open(pickle_file, "rb") as f:
        network = pickle.load(f)
        f.close()

    print(len(network.datacenters[this_dc].hosts))
    print(len(network.datacenters[this_dc].gateways))

    # drawer = TopoDrawer(network.datacenters[this_dc].dc_topo.graph)
    # drawer.draw_switch_gateway()

    # while(True):
    #    continue

    minute = 1
    client = False

    if client:
        network.set_up_mininet(dc_id=this_dc, client=True)
    else:
        network.generate_flow(dc_id=this_dc, minute=minute)
        network.set_up_mininet(dc_id=this_dc, client=False, minute=minute)

    # dc = network.datacenters[this_dc]
    # for s in dc.switches:
    #    if s.name == 's00100004':
    #        s.show_inner_ports()
