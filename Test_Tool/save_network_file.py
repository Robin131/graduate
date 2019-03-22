from Model import Network
from Model import SMALL_SCALE, MEDIUM_SCALE, LARGE_SCALE
from Model import HIGH_PRIORITY, LOW_PRIORITY

from IPy import IP

fileName = 'network.pkl'

if __name__ == '__main__':

    network = Network(dc_num=2, tenant_num=3)
    tenant_scale = [SMALL_SCALE, SMALL_SCALE, SMALL_SCALE]
    tenant_priority = [LOW_PRIORITY, HIGH_PRIORITY, HIGH_PRIORITY]
    alter_IP = [IP('191.168.0.0/16'), IP('192.168.0.0/16'), IP('10.0.0.0/16')]
    topo_type = 'fullmesh'
    switch_host_density=10

    network.init(
        priority=tenant_priority,
        scale=tenant_scale,
        alter_IP=alter_IP,
        topo_type=topo_type,
        switch_host_density=switch_host_density
    )

    network.save_as_pickle(fileName)




















