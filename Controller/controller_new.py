# -*- coding: utf-8 -*-
import six
import networkx as nx

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.lib.packet import packet, ethernet
from ryu.lib.packet import lldp
from ryu.lib.packet import ipv4, tcp, udp, icmp, arp
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub

from SwitchManager2 import SwitchManager
from LLDPManager import LLDPListener
from MacManager2 import MacManager
from ArpManager2 import ArpManager
from HostManager2 import HostManager
from TopoManager2 import TopoManager
from FlowManager2 import FlowManager
from GatewayManager2 import GatewayManager
from MeterManager2 import MeterModifier
from Util2 import Util

class Controller(app_manager.RyuApp):
    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)

         # TODO modify arp table
        self.self.arp_table = {  # {tenant_id ->{ip -> mac}}
            1:
                {
                    # d1
                    '191.168.1.1': '00:00:00:00:00:01',
                    '191.168.1.4': '00:00:00:00:00:04',
                    '191.168.1.6': '00:00:00:00:00:06',
                    '191.168.111.1': '10:00:00:00:00:00',
                    # d2
                    '191.168.2.1': '00:00:00:00:00:21',
                },

            2:
                {
                    # d1
                    '191.168.1.3': '00:00:00:00:00:03',
                    '191.168.1.2': '00:00:00:00:00:02',
                    '191.168.1.5': '00:00:00:00:00:05',
                    '191.168.1.7': '00:00:00:00:00:07',
                    # d2
                    '191.168.2.2': '00:00:00:00:00:22'
                }
        }

        # TODO modify tenant priority
        # tenant_id -> tenant_level
        self.tenant_level = {
            1: 2,
            2: 1
        }

        # TODO modify subnet
        # record all potential subnet
        self.subnets = [
            '191.0.0.0/8',
            '192.0.0.0/8',
            '10.0.0.0/8'
        ]

        # TODO modify all datacenter id
        self.all_datacenter_id = [
            1,
            2
        ]

        # record for system
        # data in controller
        self.vmac_to_pmac = {  # {vmac -> vmac}
        }
        self.pmac_to_vmac = {  # {pmac -> vmac}
        }
        self.dpid_to_vmac = {}  # {dpid -> vmac}
        self.datapathes = {}  # {dpid -> datapath}
        self.dpid_to_ports = {}  # {dpid -> ports}     # datapath的端口信息
        self.dpid_to_dpid = {}  # {(dpid, port_id) -> dpid}
        self.switch_topo = nx.Graph()  # switch topo
        self.port_speed = {}  # {dpid -> {remote_dpid -> 'max_speed' - 'cur_speed'}}
        self.meters = {}  # {dpid -> {meter_id -> band_id}}
        self.gateways = {}  # {dpid -> {port_no -> datacenter_id}}
        self.gateway_vmac = {}  # {dpid -> vmac}
        self.host_queue = {}  # gateway_id -> queue for host
        self.switch_gateway_connection = {}  # (switch_id, gateway_id) -> (switch_port, gateway_port)
        self.host_gateway = {}  # {vmac -> gateway_id}

        # 流表修改组件
        self.flow_manager = FlowManager(
            datapathes=self.datapathes,
            gateways=self.gateways
        )

        # lldp数据包处理组件
        self.lldp_manager = LLDPListener(
            datapathes=self.datapathes,
            dpid_potrs=self.dpid_to_ports,
            dpid_to_dpid=self.dpid_to_dpid,
            topo=self.switch_topo,
            DEFAULT_TTL=self.DEFAULT_TTL,
            port_speed=self.port_speed,
            potential_gateways=self.potential_gateway
        )

        self.swtich_manager = SwitchManager(
            datapathes=self.datapathes,
            dpid_to_ports=self.dpid_to_ports,
            dpid_to_vmac=self.dpid_to_vmac,
            lldp_manager=self.lldp_manager,
            meters=self.meters,
            subnets=self.subnets,
            potential_gateway=self.potential_gateway
        )

        # 交换机注册（或注销）事件
        @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
        def switch_state_change_handler(self, ev):
            dp = ev.datapath
            dpid = dp.id

            if ev.state == MAIN_DISPATCHER:
                # check whether it connect twice
                if dpid in self.datapathes.keys():
                    return

                # install lldp packet flow entry, register ovs
                self.lldp_manager.install_lldp_flow(ev)
                self.swtich_manager.register_switch(ev)

                if dpid in self.potential_gateway:
                    self.gateway_manager.register_gateway(ev)


            elif ev.state == DEAD_DISPATCHER:
                self.swtich_manager.unregister_switch(dp)



















