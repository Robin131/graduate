from IPy import IP

from Test_Tool.Model import Network
from Test_Tool.Model import SMALL_SCALE, MEDIUM_SCALE, LARGE_SCALE
from Test_Tool.Model import HIGH_PRIORITY, LOW_PRIORITY

if __name__ == '__main__':

    network = Network(dc_num=1, tenant_num=2)
    tenant_scale = [MEDIUM_SCALE, MEDIUM_SCALE, MEDIUM_SCALE]

