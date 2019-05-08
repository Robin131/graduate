# -*- coding:utf-8 -*-
import abc
import time
import cPickle as pickle

# mininet simulator
from mininet.cli import CLI
from mininet.log import setLogLevel, info,error
from mininet.node import RemoteController, OVSSwitch, Controller
from mininet.link import TCLink

from Net import Net
from const import (
    LinkBandWidth,
    LinkType,
    flow_record,
    flow_seq_record,
    ThreadParameter,
    FilePath
)
from Util import Util
from Device import Host, Switch, Gateway
from ThreadPool import ThreadPool
from Util import Util as U
from ResultParser import MultiThreadOutFileResultParser

'''
    仿真网络层
'''
class NetSimulator(object):
    def __init__(self, datacenter):
        super(NetSimulator, self).__init__()
        self.datacenter = datacenter

    @abc.abstractmethod
    def simulate(self):
        pass

    # 获得属于同一个tenant的host组
    def get_tenant_hosts(self):
        dc = self.datacenter
        tenants = dc.tenants
        t_num = len(tenants)
        res = {}
        for h in self.datacenter.hosts:
            if h.t_id in res.keys():
                res[h.t_id].append(h)
            else:
                res[h.t_id] = []
        return res

class MininetSimulator(NetSimulator):
    def __init__(self, datacenter):
        super(MininetSimulator, self).__init__(datacenter)

        self.hs_bw = LinkBandWidth.host_switch_bw
        self.ss_bw = LinkBandWidth.switch_switch_bw
        self.gs_bw = LinkBandWidth.gateway_switch_bw
        self.ng_bw = LinkBandWidth.nat_gateway_bw

        self.link_type = TCLink

        self.net = None
        self.result_parser = MultiThreadOutFileResultParser(FilePath.server_res_path, FilePath.client_res_path)

    # simulate network for a dc, client represents CLI
    def simulate(self, controller=None, client=True, minute=1):
        # 删除上一次的测试文件
        U.del_file(FilePath.res_path)

        print('*****************************************')
        print('******     NET is establishing     ******')
        print('*****************************************')
        print
        setLogLevel("info")
        topo = self.datacenter.dc_topo

        if controller is None:
            self.net = Net(switch=OVSSwitch, controller=Controller)
            self.net.addController('c0')
        else:
            if controller["type"] == "remote":
                self.net = Net(switch=OVSSwitch, listenPort=controller["port"])
                mycontroller = RemoteController("RemoteController")
                self.net.controllers = [mycontroller]
                self.net.nameToNode["RemoteController"] = mycontroller
            else:
                self.net = Net(switch=OVSSwitch, controller=Controller)
                self.net.addController('c0')
        
        net = self.net

        hosts = topo.hosts
        switches = topo.switches
        gateways = topo.gateways

        # add node
        for h in hosts:
            net.addHost(h.name, ip=h.ip, mac=h.mac)
        for s in switches:
            net.addSwitch(s.name, ip=s.ip, mac=s.mac, dpid=Util.dpid_num_2_dpid_hex(s.dpid))
        for g in gateways:
            net.addSwitch(g.name, ip=g.ip, dpid=Util.dpid_num_2_dpid_hex(g.dpid))

        # add link
        for edge in topo.graph.edges:
            self.add_link(edge)

        if client:
            net.start()
            self.set_default_gateway()
            self.ping_all()
            # self.set_up_udp_listener()
            CLI(net)
            net.stop()
            return
        else:
            net.start()
            print('*****************************************')
            print('*** NET has been successfully created ***')
            print('*****************************************')
            print

            wait_time = 5
            print('*****************************************')
            print('***  please wait for {} ses to start  ***'.format(wait_time))
            print('*****************************************')
            print
            time.sleep(wait_time)


            self.set_default_gateway()
            print('*****************************************')
            print('***       Start to do Ping test       ***')
            print('*****************************************')
            print
            if self.ping_all():
                print('*****************************************')
                print('******       Pass Ping test       *******')
                print('*****************************************')
                print
            else:
                print('*****************************************')
                print('******       Fail Ping test       *******')
                print('*****************************************')
                print

            print('*****************************************')
            print('*****       Start to simulate       *****')
            print('*****************************************')
            print
            self.set_up_udp_listener()
            time.sleep(2)
            self.simulate_flow(minute=minute)
            pkt_loss = self.pkt_loss()
            if pkt_loss == -1:
                print('*****************************************')
                print('******     Result Parser Fail     *******')
                print('*****************************************')
            else:
                print('*****************************************')
                print('******     Total pkt loss is {}   '.format(round(pkt_loss, 4)))
                print('*****************************************')
            net.stop()

    # 为所有的主机打开udp监听端口
    def set_up_udp_listener(self):
        hosts = self.datacenter.hosts
        for h in hosts:
            self.net.set_up_udp_listener(h)
        return

    # 为所有的hosts设置网关ip
    def set_default_gateway(self):
        hosts = self.datacenter.hosts
        for h in hosts:
            self.net.set_default_gateway(h)
        return

    # 根据输入的流信息仿真流
    def simulate_flow(self, minute):
        for i in xrange(minute):
            flows = {}
            flow_seq = {}
            with open(flow_record(i), "rb") as f:
                flows = pickle.load(f)
                f.close()
            with open(flow_seq_record(i), "rb") as f:
                flow_seq = pickle.load(f)
                f.close()

            # 使用线程池模拟一分钟内的流量
            thread_pool = ThreadPool(thread_num=ThreadParameter.max_num)
            for i in xrange(60):
                fs = flow_seq[i]
                for idx in fs:
                    flow = flows[idx]
                    thread_pool.add_job(
                        func=self.net.udp_flow,
                        time_seq=i,
                        src=flow.src,
                        dst=flow.dst,
                        size=flow.size
                    )
            thread_pool.start()
        return

    # 依据拓扑边的属性添加连接
    def add_link(self, edge):
        node1 = edge[0]
        node2 = edge[1]

        link_type = Util.get_link_type(node1, node2)

        if link_type == LinkType.hs_link:
            if isinstance(node2, Switch):
                port_no, link_bw = node2.get_inner_port_no_with_device(node1)
                link_bw = LinkBandWidth.host_switch_bw if link_bw == 0 else link_bw
                self.net.addLink(node1.name, node2.name, 1, port_no, cls=self.link_type, bw=link_bw)
            else:
                port_no, link_bw = node1.get_inner_port_no_with_device(node2)
                link_bw = LinkBandWidth.host_switch_bw if link_bw == 0 else link_bw
                self.net.addLink(node2.name, node1.name, 1, port_no, cls=self.link_type, bw=link_bw)
            return

        if link_type == LinkType.ss_link or link_type == LinkType.gs_link or link_type == LinkType.gg_link:

            node1_port, bw = node1.get_inner_port_no_with_device(node2)
            node2_port, bw = node2.get_inner_port_no_with_device(node1)

            if bw == 0:
                if link_type == LinkType.ss_link:
                    bw = LinkBandWidth.switch_switch_bw
                elif link_type == LinkType.gs_link:
                    bw = LinkBandWidth.gateway_switch_bw
                elif link_type == LinkType.gg_link:
                    bw = LinkBandWidth.gateway_gateway_bw

            # print('{} -- {} with port {} -- {}'.format(node1.name, node2.name, node1_port, node2_port))
            self.net.addLink(node1.name, node2.name, node1_port, node2_port, cls=self.link_type, bw=bw)
            return

        # TODO 增加NAT连接
        return

    # 测试用ping all指令(仅测试能通信的机器对)
    # 目前仅支持同数据中心的机器测试
    def ping_all(self):
        # 同域同子网
        local_host_group = []
        t_hosts = self.get_tenant_hosts()
        for t_id, hosts in t_hosts.items():
            tenant = self.datacenter.get_tenant(t_id)
            subnet_host_dic = {}
            assert tenant is not None
            for ip in tenant.subnet:
                subnet_host_dic[ip] = []
            for h in hosts:
                for subnet in subnet_host_dic.keys():
                    if U.is_in_subnet(h.ip, subnet):
                        subnet_host_dic[subnet].append(h)
            for subnet, _hosts in subnet_host_dic.items():
                local_host_group.append(_hosts)

        # 至此local_host_group 包含了所有可通信的host列表
        status = True
        for hs in local_host_group:
            status =  status and self.net.ping_hosts(hs)
        return status

    # 计算整体丢包率
    def pkt_loss(self):
        try:
            return self.result_parser.parse_server()
        except:
            return -1

