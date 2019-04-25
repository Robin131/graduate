# -*- coding:utf-8 -*-

import cPickle as pickle
import gc

from random import randint, sample
from IPy import IP
from util import *
from math import ceil, exp
from Topo import FatTreeTopo, FullMeshTopo
from scipy import stats

from mininet.cli import CLI
from mininet.log import setLogLevel, info,error
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink



arp_file = './data/arp_table.pkl'


'''
    Tenant Para
'''
HIGH_PRIORITY = 1               # with Qos
LOW_PRIORITY = 2
SMALL_SCALE = 1                 # only in 1 datacenter with host_num (3, 10), subnet (1, 2)
MEDIUM_SCALE = 2                # only in 2 datacenter with host_num (10, 30), subnet (1, 3)
LARGE_SCALE = 3                 # in all datacenters with host_num (10, 30), subnet (1, 3)
SMALL_HOST_NUM_LOW_BOUND = 3
SMALL_HOST_NUM_HIGH_BOUND = 10
MEDIUM_HOST_NUM_LOW_BOUND = 10
MEDIUM_HOST_NUM_HIGH_BOUND = 30
LARGE_HOST_NUM_LOW_BOUND = 10
LARGE_HOST_NUM_HIGH_BOUND = 30
SMALL_SUBNET_NUM_LOW_BOUND = 1
SMALL_SUBNET_NUM_HIGH_BOUND = 2
MEDIUM_SUBNET_NUM_LOW_BOUND = 1
MEDIUM_SUBNET_NUM_HIGH_BOUND = 3
LARGE_SUBNET_NUM_LOW_BOUND = 1
LARGE_SUBNET_NUM_HIGH_BOUND = 3
SMALL_DC_NUM = 1
MEDIUM_DC_NUM = 2
MAX_MAC_NUM = 1000
GATEWAY_NUM_TO_CORE = 2
GATEWAY_NUM_TO_SWITCH = 6               # 一台网关对应的交换机数量

'''
    Flow Generator Para
'''
LOGNORM = 'lognorm'

class Pool(object):
    def __init__(self, pool):
        super(Pool, self).__init__()

        self.pool = pool if type(pool) == list else list(pool)

    def __str__(self):
        return str(self.pool)

    def get(self):
        s = self.pool[0]
        self.pool.remove(s)
        return s

class Device(object):
    def __init__(self, name, id, ip, mac, dc_id):
        super(Device, self).__init__()

        self.name = name
        self.id = id
        self.ip = ip
        self.mac = mac
        self.dc_id = dc_id

    def equals(self, device):
        if self.name == device.name:
            return True
        return False

    def __str__(self):
        return 'id: %d, ip:%s, mac: %s, dc_id: %d'%(
            self.id, str(self.ip), self.mac, self.dc_id)

'''
    Host class   
'''
class Host(Device):
    def __init__(self, name, id, ip, mac, dc_id, t_id):
        super(Host, self).__init__(name, id, ip, mac, dc_id)

        self.name = name
        self.t_id = t_id

    def __str__(self):
        sup = super(Host, self).__str__()
        return sup + ', tenant: %d\n'%(self.t_id)

    def is_in(self, tenant):
        return self.t_id == tenant.tenant_id



'''
    Switch class        
'''
class Switch(Device):
    def __init__(self, name, id, ip, mac, dc_id):
        super(Switch, self).__init__(name, id, ip, mac, dc_id)


'''
    Gateway class
    数据中心配置需要确定每个gateway在哪个数据中心中 & 每个端口连接哪个数据中心 {dp_if:{dc_id:port_id}}
'''

class Gateway(Switch):
    def __init__(self, name, id, ip, mac, dc_id):
        super(Gateway, self).__init__(name, id, ip, mac, dc_id)


'''
    Tenant class
'''
class Tenant(object):
    def __init__(self, tenant_id, priority=LOW_PRIORITY, scale=MEDIUM_SCALE):
        super(Tenant, self).__init__()

        self.tenant_id = tenant_id
        self.priority = priority
        self.scale = scale
        self.datacenters = []
        self.hosts = []
        self.subnet = []

        self.subnet_num = 0
        self.dc_num = 0
        self.hosts_num = 0

    def __str__(self):
        res = 'Tenant %d\n priority: %d, scale: %d, datacenter: ['%(self.tenant_id, self.priority, self.scale)
        for dc in self.datacenters:
            res += str(dc.datacenter_id) + ', '
        res += ']'
        return res

    def add_host(self, id):
        self.hosts.append(id)

    def set_priority(self, priority):
        self.priority = priority

    def set_scale(self, scale, max_dc):
        # check host before reset priority
        if len(self.hosts) != 0:
            return
        self.scale = scale

        # generate hosts number, subnet number, dc number
        if self.scale == SMALL_SCALE:
            self.hosts_num = randint(SMALL_HOST_NUM_LOW_BOUND, SMALL_HOST_NUM_HIGH_BOUND)
            self.subnet_num = randint(SMALL_SUBNET_NUM_LOW_BOUND, SMALL_SUBNET_NUM_HIGH_BOUND)
            self.dc_num = SMALL_DC_NUM
        elif self.scale == MEDIUM_SCALE:
            self.hosts_num = randint(MEDIUM_HOST_NUM_LOW_BOUND, MEDIUM_HOST_NUM_HIGH_BOUND)
            self.subnet_num = randint(MEDIUM_SUBNET_NUM_LOW_BOUND, MEDIUM_SUBNET_NUM_HIGH_BOUND)
            self.dc_num = MEDIUM_DC_NUM
        elif self.scale == LARGE_SCALE:
            self.hosts_num = randint(LARGE_HOST_NUM_LOW_BOUND, LARGE_HOST_NUM_HIGH_BOUND)
            self.subnet_num = randint(LARGE_SUBNET_NUM_LOW_BOUND, LARGE_SUBNET_NUM_HIGH_BOUND)
            self.dc_num = max_dc
        else:
            print('Never should you reach here, please report a bug for tenant scale value')

    # generate hosts with proper ip and mac
    # distribute hosts to datacenter
    def gen_hosts(self, alter_subnet, mac_pool):
        # generate hosts
        assert len(alter_subnet) >= self.subnet_num
        # generate ip pools
        IPs = sample(alter_subnet, self.subnet_num)
        ip_pools = []
        for ip in IPs:
            self.subnet.append(ip)
            pool = Pool(ip)
            ip_pools.append(pool)
        for i in range(0, self.hosts_num):
            id = i
            # get an ip from pool
            ip_pool = sample(ip_pools, 1)[0]
            ip = ip_pool.get()
            # get a mac from pool
            mac = mac_pool.get()
            # get a datacenter
            dc = sample(self.datacenters, 1)[0]
            host_name = generate_host_name(self.tenant_id, id)
            host = Host(name=host_name, id=id, ip=ip, mac=mac, dc_id=dc.datacenter_id,t_id=self.tenant_id)
            self.hosts.append(host)
            dc.hosts.append(host)
        return

    # {ip -> mac}
    def get_arp_table(self):
        res = {}
        for host in self.hosts:
            res[str(host.ip)] = host.mac
        return res

    # {mac -> tenant_id}
    def get_mac_id_table(self):
        res = {}
        for h in self.hosts:
            res[h.mac] = self.tenant_id
        return res

'''
    Datacenter class
'''
class Datacenter(object):
    def __init__(self, datacenter_id):
        super(Datacenter, self).__init__()

        self.datacenter_id = datacenter_id
        self.tenants = []                     # array for all tenants
        self.switches = []                    # array for all switches
        self.hosts = []                       # array for all hosts
        self.gateways = []
        self.dc_topo = None

    def __str__(self):
        res = 'Datacenter: %d\n tenant: [' %(self.datacenter_id)
        for t in self.tenants:
            res += str(t.tenant_id) + ', '
        res += ']'
        return res

    '''
        methods to generate components
    '''
    def gen_switches(self, mac_pool, topo_type='fattree', density=10):
        # only generate switches without generate topo
        if topo_type == 'fattree':
            # calculate num of swithces
            host_num = len(self.hosts)
            # fat tree pod
            pod_num = pow(host_num * 4.0, 1.0/3.0)
            pod_num = ceil(pod_num)
            if pod_num % 2 == 1:
                pod_num += 1
            switch_num = int(pod_num * pod_num * 5 / 4)
            for i in range(switch_num):
                switch_name = generate_switch_name(self.datacenter_id, i)
                switch = Switch(name=switch_name, id=i, ip=None, mac=mac_pool, dc_id=self.datacenter_id)
                self.switches.append(switch)
            return
        elif topo_type == 'fullmesh':
            host_num = len(self.hosts)
            switch_num = int(ceil(float(host_num) / density))
            for i in range(switch_num):
                switch_name = generate_switch_name(self.datacenter_id, i)
                switch = Switch(name=switch_name, id=i, ip=None, mac='', dc_id=self.datacenter_id)
                self.switches.append(switch)
            return

    # TODO add an ip pool for switch and gateway
    def gen_gateways(self, mac_pool):
        assert len(self.switches) != 0
        num = int(ceil(len(self.switches) / GATEWAY_NUM_TO_SWITCH))
        for i in range(num):
            name = generate_gateway_name(self.datacenter_id, i)
            ip = generate_ip_4_gateway(self.datacenter_id, i)
            mac = mac_pool.get()
            g = Gateway(name=name, id=i, ip=ip, mac=mac, dc_id=self.datacenter_id)
            self.gateways.append(g)
        return

    '''
        methods to create topo
    '''
    def create_fattree_topo(self):
        self.dc_topo = FatTreeTopo(self.switches, self.hosts)
        self.dc_topo.create_fattree_topo(bw={})

    def create_full_mesh_topo(self, density):
        self.dc_topo = FullMeshTopo(self.switches, self.hosts, density)
        self.dc_topo.create_full_mesh_topo()

    '''
        methods to get components or relationship
    '''
    def get_tenant_arp_table(self):
        res = {}
        for t in self.tenants:
            tenant_arp_table = t.get_arp_table()
            res[t.tenant_id] = tenant_arp_table
        return res



'''
    Network class
'''
class Network(object):
    def __init__(self, dc_num=2, tenant_num=3):
        super(Network, self).__init__()

        self.datacenters = []
        self.tenants = []
        self.alter_IP = []                  # list of IP
        self.mac_pool = None                # Pool of Mac
        self.net = None                     # Mininet instance
        self.hosts = []
        self.switches = []

        self.gen_datacenter(dc_num=2)
        self.gen_tenant(tenant_num=3)

        # current datacenter id for testing

    # start a network
    def init(self, priority, scale, alter_IP, topo_type, **kwargs):
        self.set_tenant_priority(priority)              # 设置租户优先级
        self.set_tenant_scale(scale)                    # 设置租户的大小（影响host数量）
        self.set_alter_IP(alter_IP)                     # 可使用的的网段
        self.generate_mac_pool()                        # 生成简单mac地址池
        self.allocate_tenant_2_datacenter()             # 分配租户和数据中心的关系
        self.allocate_hosts_2_tenants()                 # 为租户分配host
        self.allocate_switch_2_datacenter(topo_type=topo_type)      # 为dc生成交换机
        self.allocate_gateway_2_datacenter()  # 生成网关（目前仅支持网管与switch的全连接）

        if topo_type == 'fullmesh':                     # 生成拓扑结构
            self.create_full_mesh_topo_4_dc(density=kwargs['switch_host_density'])
        elif topo_type == 'fattree':
            self.create_fattree_topo_4_dc()
        self.allocate_gateway_2_datacenter()            # 生成网关（目前仅支持网管与switch的全连接）
        return

    '''
        methods to generate components
    '''
    # instantiate datacenters
    def gen_datacenter(self, dc_num):
        for i in range(dc_num):
            dc = Datacenter(datacenter_id=i)
            self.datacenters.append(dc)

    # instantiate tenants
    def gen_tenant(self, tenant_num):
        for i in range(tenant_num):
            t = Tenant(tenant_id=i)
            self.tenants.append(t)

    def generate_mac_pool(self):
        self.mac_pool = Pool(generate_MACs(MAX_MAC_NUM))

    '''
        methods to set components
    '''
    def set_alter_IP(self, alter_IP):
        for ip in alter_IP:
            self.alter_IP.append(ip)
        return

    # set tenant priority
    def set_tenant_priority(self, pri_array):
        assert len(self.tenants) == len(pri_array)
        i = 0
        for t in self.tenants:
            t.set_priority(pri_array[i])
            i += 1
        return

    # set tenant scale (only)
    def set_tenant_scale(self, scl_array):
        assert len(self.tenants) == len(scl_array)
        i = 0
        for t in self.tenants:
            t.set_scale(scl_array[i], len(self.datacenters))
            i += 1
        return

    '''
        methods to create relationship for different components
    '''
    def allocate_tenant_2_datacenter(self):
        for t in self.tenants:
            dc_num = t.dc_num
            dcs = sample(self.datacenters, dc_num)
            for dc in dcs:
                t.datacenters.append(dc)
                dc.tenants.append(t)
        return

    def allocate_hosts_2_tenants(self):
        for t in self.tenants:
            t.gen_hosts(self.alter_IP, self.mac_pool)
        return

    def allocate_switch_2_datacenter(self, topo_type='fattree'):
        for dc in self.datacenters:
            dc.gen_switches(mac_pool=self.mac_pool, topo_type=topo_type)

    def allocate_gateway_2_datacenter(self):
        for dc in self.datacenters:
            dc.gen_gateways(self.mac_pool)
        return

    def create_fattree_topo_4_dc(self):
        for dc in self.datacenters:
            dc.create_fattree_topo()
        return

    '''
        methods to create topo with networkx
    '''
    def create_full_mesh_topo_4_dc(self, density):
        for dc in self.datacenters:
            dc.create_full_mesh_topo(density=density)
        return

    '''
        method to log components and relationship
    '''
    def show_tenants_hosts(self):
        for t in self.tenants:
            print('Tenant id: %d\n' %(t.tenant_id))
            for h in t.hosts:
                print(h)

    def show_datacenters(self):
        for dc in self.datacenters:
            print(dc)

    def show_tenants(self):
        for t in self.tenants:
            print(t)

    def show_ips(self):
        print(self.alter_IP)

    def show_mac_pool(self):
        print(self.mac_pool)

    def show_all_switches(self):
        for dc in self.datacenters:
            print(dc.datacenter_id)
            print(len(dc.hosts))
            print(len(dc.switches))

    '''
        get components or relationships
    '''
    # get arp table for each datacenter
    # format: {dc_id -> {tenant_id -> {ip -> mac}}}
    def get_arp_tables_4_dc(self):
        res = {}
        for dc in self.datacenters:
            dc_arp_table = dc.get_tenant_arp_table()
            res[dc.datacenter_id] = dc_arp_table
        return res

    # get relationship between host_mac and tenant_id
    def get_mac_tenant_table(self):
        res = {}
        for t in self.tenants:
            mac_tenant_table = t.get_mac_id_table()
            res = dict(mac_tenant_table.itmes() + res.items())
        return res

    # get tenant priority
    def get_tenant_priority_table(self):
        res = {}
        for t in self.tenants:
            res[t.tenant_id] = t.priority
        return res

    def get_all_hosts(self):
        if len(self.hosts) == 0:
            for t in self.tenants:
                self.hosts = self.hosts + t.hosts
        return self.hosts

    def get_all_switches(self):
        if len(self.switches) == 0:
            for dc in self.datacenters:
                self.switches += dc.switches
        return self.switches

    def get_datacenter(self, datacenter_id):
        for dc in self.datacenters:
            if dc.datacenter_id == datacenter_id:
                return dc
        return None

    '''
        save and load instance and tables in file with pickle
    '''
    def save_as_pickle(self, file_name):
        with open(file_name, "wb") as f:
            pickle.dump(self, f)
            f.close()

    # {tenant_id -> {ip : host}}
    def arp_table(self):
        arp_table = {}
        for t in self.tenants:
            t_id = t.tenant_id
            arp_table[t_id] = {}
            for h in t.hosts:
                ip = str(h.ip)
                mac = str(h.mac)
                arp_table[t_id][ip] = mac
        return arp_table

    # mac -> tenant_id
    def host_pmac(self):
        dict = {}
        for t in self.tenants:
            t_id = t.tenant_id
            for h in t.hosts:
                mac = str(h.mac)
                dict[mac] = t_id
        return dict

    # tenant_id -> tenant_level
    def tenant_level(self):
        dict = {}
        for t in self.tenants:
            dict[t.tenant_id] = t.priority
        return dict

    # subnets
    def all_subnet(self):
        return [str(ip) for ip in self.alter_IP]

    # TODO 将网络参数写入文件
    def save_records(self):
        return

    '''
        methods to setup network with Mininet
    '''
    # choose OVSSwitch as default switch type
    # listenPort as 6633
    # TODO set ipBase and gateway info
    def init_net(self, datacenter_id, bw={}):

        setLogLevel("info")
        self.net = Mininet(switch=OVSSwitch, listenPort=6633)
        link_type = TCLink         # TODO default link_type

        net = self.net
        mycontroller = RemoteController("RemoteController")
        net.controllers = [mycontroller]
        net.nameToNode["RemoteController"] = mycontroller

        dc = self.get_datacenter(datacenter_id)
        assert dc is not None

        hosts = dc.dc_topo.hosts
        switches = dc.dc_topo.switches
        gateways = dc.dc_topo.gateways

        # add hosts and switches
        for h in hosts:
            net.addHost(h.name, ip=str(h.ip), mac=h.mac)

        for s in switches:
            net.addSwitch(s.name, ip=str(s.ip), mac=s.mac)

        for g in gateways:
            net.addSwitch(g.name, ip=str(g.ip), mac=g.mac)

        # add link for switches and hosts
        for edge in dc.dc_topo.graph.edges:
            net.addLink(edge[0].name, edge[1].name, cls=link_type)

        net.start()
        CLI(net)
        net.stop()

'''
    流量生成器生成的流文件
    源device，目的device，流大小，持续时间
'''
class Flow(object):

    def __init__(self, src, dst, size, period):
        super(Flow, self).__init__()

        self.src = src
        self.dst = dst
        self.size = size
        self.period = period



'''
    流产生器
    每个交换机的flow数为每分钟1500-4000个           **作为参数 flow_num_per_min (per  host)
    每个流的间隔时间为300-2000微秒(0.3 ~ 2 毫秒)
    流的大小和数量呈重尾分布                        **考虑作为参数
    80%的流是内部流量                              **作为参数
    流量变化有周期性                               **作为参数
    时间长度                                      **作为参数
    
'''
class FlowGenenrator(object):

    def __init__(self, hosts, flow_num_per_min, dc_num, inner_percent=0.8, save=True, fluc_rate=0.1, stats_type=LOGNORM, **kwargs):
        super(FlowGenenrator, self).__init__()

        self.hosts = hosts
        self.tenant_host_dic = self.divide_hosts()      # {t_id -> {dc_id -> [hosts]}}
        self.dc_ids = self.dc_check()           # 数据中心数量及取值

        self.stats_para = kwargs
        self.model = self.stats_model(stats_type)

        self.fluc_rate = fluc_rate      # 流大小的波动频率
        self.flow_num_per_min = flow_num_per_min
        self.save = save
        self.inner_percent = inner_percent

        self.flows = []
        self.external_ip = []               # TODO  设置外部ip



    # 根据租户划分hosts
    def divide_hosts(self):
        hosts = self.hosts
        dic = self.tenant_host_dic
        for h in hosts:
            if h.t_id not in dic.keys():
                dic[h.t_id] = {}
            if h.dc_id not in dic[h.t_id].keys():
                dic[h.t_id][h.dc_id] = []
            dic[h.t_id][h.dc_id].append(h)
        return dic

    # 数据中心id取值
    def dc_check(self):
        dc_ids = []
        for h in self.hosts:
            dc_id = h.dc_id
            if not dc_id in dc_ids:
                dc_ids.append(dc_id)
        return dc_ids

    # 生成对应的统计模型
    def stats_model(self, stats_type):
        param = self.stats_para
        # 对数正态函数
        if stats_type == LOGNORM:
            if param is None:
                sigma = 500                 # TODO  确定默认值
                mu = 5 * 1000               # TODO  确定默认值
            sigma = param['sigma']
            mu = param['mu']

            return stats.lognorm(s=sigma, scale=exp(mu))
        else:
            raise Exception

    # 检查cdf
    def model_cdf(self, value):
        return self.model.cdf(value)

    # 随机抽取域内交换机通信
    def random_inner_pair(self, dc_id):
        dic = self.tenant_host_dic
        t_ids = dic.keys()
        t_id = randint(0, len(t_ids) - 1)
        hosts = dic[t_id][dc_id]
        hl = len(hosts)
        src = randint(0, hl - 1)
        dst = randint(0, hl - 1)
        while src == dst:
            dst = randint(0, hl - 1)
        return hosts[src], hosts[dst]


    # TODO 根据流大小确定持续时间
    def generate_flow_period(self, flow_size):
        return 1

    def generate_flow(self):
        # 逐个数据中心的生成流量
        for dc_id in self.dc_ids:
            self.generate_inner_flow(dc_id)
            self.generate_outter_flow(dc_id)

    def generate_inner_flow(self, dc_id):
        flow_num_host = int(ceil(self.flow_num_per_min * self.inner_percent))   # 每个host每分钟的内部流数量
        flow_num_total = flow_num_host * len(self.hosts)

        # 按概率分布生成流大小
        flow_byte = self.model.rvs(size=flow_num_total)
        for fb in flow_byte:
            src, dst = self.random_inner_pair(dc_id)
            flow = Flow(src=src, dst=dst, size=fb, period=self.generate_flow_period(fb))
            self.flows.append(flow)
        del flow_byte
        gc.collect()

    def generate_outter_flow(self, dc_id):
        return

































