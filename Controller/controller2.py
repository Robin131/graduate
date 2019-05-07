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
from Cofiguration import DictionaryConfiguration

class Controller(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    DEFAULT_TTL = 120           # default ttl for LLDP packet
    PORT_INQUIRY_TIME = 10      # default time interval for port inquiry
    PORT_SPEED_CAL_INTERVAL = 5     # default time interval to calculate port speed
    GATEWAY_FLOW_INQUIRY_TIME = 1  # default time interval for gateway flow table inquiry
    GATEWAY_PORT_INQUIRY_TIME = 1  # default time interval for gateway datacenter port inquiry
    IP_REPLACE_MAC_TIMEOUT = 50     # default timeout for the table which modify mac_dst according to ip
    GATEWAY_BALANCE_TIME = 2        # default time interval for gateway balance adjustment

    # port_speed
    DEFAULT_SS_BW = 300        # default bandwidth between switch
    DEFAULT_GG_BW = 1250000    # default bandwidth between gateway in different datacenter

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)

        self.this_dc_id = 1
        conf = DictionaryConfiguration(self.this_dc_id)

        # configurations for the system
        # arp table for different tenants
        self.arp_table = conf.arp_table

        # pmac -> tenant_id
        self.host_pmac = conf.host_pmac

        # tenant_id -> tenant_level
        self.tenant_level = conf.tenant_level

        # record all potential subnet
        self.subnets = conf.subnets

        # record all potential gateway
        # 'NAT' : port_no
        # datacenter_id : port_no
        self.potential_gateway = conf.potential_gateway

        # remote datacenter_id -> {dpid -> peer}
        # if there is no peer, then peer is -1
        self.gateways_datacenter_port = conf.gateway_datacenter_port

        # record all potential gateway_ip
        # datacenter_id -> [gateway_ip]s
        self.gateway_ip = conf.gateway_ip

        # record speed for tenant
        # tenant_id -> speed
        self.tenant_speed = conf.tenant_speed

        # record all datacenter_id
        self.all_datacenter_id = conf.all_datacenter_id


        # record for system
        # data in controller
        self.vmac_to_pmac = {                               # {vmac -> vmac}
        }
        self.pmac_to_vmac = {                               # {pmac -> vmac}
        }
        self.dpid_to_vmac = {}                              # {dpid -> vmac}
        self.datapathes = {}                                # {dpid -> datapath}
        self.dpid_to_ports = {}                             # {dpid -> ports}
        self.dpid_to_dpid = {}                              # {(dpid, port_id) -> dpid}
        self.switch_topo = nx.Graph()                       # switch topo
        self.port_speed = {}                                # {dpid -> {remote_dpid -> 'max_speed' - 'cur_speed'}}
        self.meters = {}                                    # {dpid -> {meter_id -> band_id}}
        self.gateways = {}                                  # {dpid -> {port_no -> datacenter_id}}
        self.gateway_vmac = {}                              # {dpid -> vmac}
        self.host_queue = {}                                # gateway_id -> queue for host
        self.switch_gateway_connection = {}                 # (switch_id, gateway_id) -> (switch_port, gateway_port)
        self.host_gateway = {}                              # {vmac -> gateway_id}

        # components
        self.flow_manager = FlowManager(
            datapathes=self.datapathes,
            gateways=self.gateways
        )
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
        self.arp_manager = ArpManager(
            arp_table=self.arp_table,
            pmac_to_vmac=self.pmac_to_vmac,
            gateway_ip=self.gateway_ip,
            gateways=self.gateways,
            dpid_to_vmac=self.dpid_to_vmac,
            switch_gateway_connection=self.switch_gateway_connection,
            datapathes=self.datapathes,
            host_gateway=self.host_gateway
        )
        self.mac_manager = MacManager(
            tenant_level=self.tenant_level
        )
        self.meter_manager = MeterModifier(
            meters=self.meters
        )
        self.host_manager = HostManager(
            host_pmac=self.host_pmac,
            mac_manager=self.mac_manager,
            pmac_to_vmac=self.pmac_to_vmac,
            vmac_to_pmac=self.vmac_to_pmac,
            tenant_speed=self.tenant_speed,
            meter_manager=self.meter_manager
        )
        self.topo_manager = TopoManager(
            topo=self.switch_topo,
            dpid_to_dpid=self.dpid_to_dpid
        )
        self.gateway_manager = GatewayManager(
            gateways=self.gateways,
            potential_gateway = self.potential_gateway,
            gateway_flow_table_inquire_time=self.GATEWAY_FLOW_INQUIRY_TIME,
            datapathes=self.datapathes,
            gateway_port_inquire_time=self.GATEWAY_PORT_INQUIRY_TIME,
            gateway_datacenter_port_max_speed=self.DEFAULT_GG_BW,
            balance_time_interval=self.GATEWAY_BALANCE_TIME,
            all_datacenter_id=self.all_datacenter_id,
            topo_manager=self.topo_manager,
            meter_manager=self.meter_manager
        )


        # hub
        self.init_hub = hub.spawn(self.init_controller)
        # self.gateway_statistics_inquiry_hub = hub.spawn(self.gateway_manager.inquiry_gateway_flow_table_info)
        # self.gateways_datacenter_port_hub = hub.spawn(self.gateway_manager.inquiry_gateway_datacenter_port)
        # self.gateway_banlance_hub = hub.spawn(self.gateway_manager.gateway_balance_hub)
        # self.gateway_init_record_hub = hub.spawn(self.gateway_manager.init_gateway_record)

        # test hub
        # self.test_hub = hub.spawn(self.test)

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

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        dpid = dp.id

        # choose datacenter_id according to dpid
        if dpid in [1, 2, 3, 10, 11, 12]:
            this_datacenter_id = 1
        else:
            this_datacenter_id = 2

        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        pkt = packet.Packet(msg.data)
        in_port = msg.match['in_port']

        i = iter(pkt)
        eth_pkt = six.next(i)
        assert type(eth_pkt) == ethernet.ethernet
        dst = eth_pkt.dst
        src = eth_pkt.src

        special_pkt = six.next(i)

        # check the type of this pkt
        # lldp
        if type(special_pkt) == lldp.lldp:
            self.lldp_manager.lldp_packet_in(ev)
            return
        # arp packet
        elif type(special_pkt) == arp.arp:
            # test
            # print('a arp packte is coming===============')
            # print('the src is ' + str(src))
            tenant_id = MacManager.get_tenant_id_with_vmac(src)
            self.arp_manager.handle_arp(
                datapath=dp,
                in_port=in_port,
                tenant_id=tenant_id,
                pkt=pkt
            )
            return

        # check if the source has no record
        if not src in self.pmac_to_vmac.keys() and not src in self.vmac_to_pmac.keys():
            # first check whether this is pmac for host(not a vmac for host or switch, not a pmac for port that connect ovs)
            if src in self.host_pmac.keys():
                # test
                print('new host coming!!==============' + src)
                self.host_manager.register_host(ev)

        # if src is a vmac, which means this host has been registered
        elif src in self.vmac_to_pmac.keys():
            # first check whether dst is a host vmac (for table 7)
            if dst in self.vmac_to_pmac.keys():
                print('pkt from ' + src + ' to ' + dst)

                # find the route
                dst_dpid = MacManager.get_dpid_with_vmac(dst)
                path = self.topo_manager.get_path(dpid, dst_dpid)
                # install flow entry for only this switch
                datapath = self.datapathes[dpid]
                port = path[0][1]
                self.flow_manager.install_wildcard_sending_flow(
                    dp=datapath,
                    out_port=port,
                    dst_dpid=dst_dpid,
                    buffer_id=msg.buffer_id
                )

                # finally send the packet
                if len(path) > 0:
                    out_port = path[0][1]
                    actions = [parser.OFPActionOutput(out_port)]
                else:
                    actions = []
                data = None
                if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                    data = msg.data
                out_packet = parser.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
                                                 in_port=in_port, actions=actions, data=data)
                dp.send_msg(out_packet)

            # come from table 6, add mac dst according to ip
            elif dst == FlowManager.TABLE6_MISSING_FLOW_ADDRESS:
                assert type(special_pkt) == ipv4.ipv4

                # find dst_vmac
                ip_dst = special_pkt.dst
                tenant_id = MacManager.get_tenant_id_with_vmac(src)
                dst_pmac = self.arp_table[tenant_id][ip_dst]
                dst_vmac = self.pmac_to_vmac[dst_pmac]

                match = parser.OFPMatch(eth_type=0x800, ipv4_dst=ip_dst)
                actions = [parser.OFPActionSetField(eth_dst=dst_vmac)]
                instructions = [
                    parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions),
                    parser.OFPInstructionGotoTable(table_id=6)
                ]
                idle_timeout = self.IP_REPLACE_MAC_TIMEOUT
                FlowManager.add_flow_with_timeout(dp, 1, match, instructions, idle_timeout=idle_timeout,
                                                  table_id=5, buffer_id=msg.buffer_id)
                data = None
                if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                    data = msg.data

                dst_datacenter_id = MacManager.get_datacenter_id_with_vmac(dst_vmac)
                if dst_datacenter_id == this_datacenter_id:
                    switch_id = MacManager.get_dpid_with_vmac(src)
                    dst_switch_id = MacManager.get_dpid_with_vmac(dst_vmac)
                    path = self.topo_manager.get_path(switch_id, dst_switch_id)
                    port = path[0][1]
                    actions = [parser.OFPActionSetField(eth_dst=dst_vmac),
                            parser.OFPActionOutput(port)]
                else:
                    gateway_id = self.host_gateway[src]
                    switch_id = MacManager.get_dpid_with_vmac(src)
                    port = self.switch_gateway_connection[(switch_id, gateway_id)][0]
                    actions = [parser.OFPActionSetField(eth_dst=dst_vmac),
                            parser.OFPActionOutput(port)]

                out_packet = parser.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
                                                 in_port=in_port, actions=actions, data=data)
                dp.send_msg(out_packet)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        dpid = dp.id

        if dpid in self.gateways.keys():
            self.gateway_manager.gateway_statistics_handler(ev)

        return
    #
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        dpid = dp.id

        if dpid in self.gateways.keys():
            self.gateway_manager.gateway_port_reply_handler(ev)

        return

    def init_controller(self):
        hub.sleep(9)

        # test part
        print('start to init')

        # detect connections between switch and gateway
        self._check_switch_gateway_connection()
        # init arp manager for gateway round robin
        self.arp_manager.init_arp()
        # install flow entry for table 4 on ovs (to adjust whether dst is a gateway or not)
        # del the missing flow in table 2 in every ovs and install new one (for register host)
        for dpid in self.datapathes.keys():
            if dpid in self.gateways.keys():
                continue
            else:
                self.flow_manager.install_gateway_adjustment_flow_entry(dpid)
                FlowManager.substitute_missing_flow(self.datapathes[dpid])
                FlowManager.install_arp_flow_entry(self.datapathes[dpid])
        # install statistics flow entry on gateway
        for gw_id in self.gateways.keys():
            dpids = Util.difference_between_list(self.datapathes.keys(), self.gateways.keys())
            if gw_id in [10, 11, 12]:
                this_datacenter_id = 1
            else:
                this_datacenter_id = 2
            for datacenter_id in self.all_datacenter_id:
                if datacenter_id != this_datacenter_id:
                    FlowManager.install_statistics_flow(self.datapathes[gw_id], dpids, this_datacenter_id, self.all_datacenter_id)

        # init record for gateway
        # self.gateway_manager.init_gateway_record()




    def _check_switch_gateway_connection(self):
        for dpid in self.datapathes.keys():
            if dpid in self.gateways.keys():
                continue
            else:
                for gw_id in self.gateways.keys():
                    # find the port connecting to gateway
                    port1 = self.topo_manager.get_path(dpid, gw_id)[0][1]
                    port2 = self.topo_manager.get_path(gw_id, dpid)[0][1]

                    self.switch_gateway_connection[(dpid, gw_id)] = (port1, port2)
        return


    # test hub
    def test(self):
        hub.sleep(10)
        while True:
            hub.sleep(1)
            print(self.gateway_manager.gateway_port_speed)
            print('===================================')
        # hub.sleep(10)
        # f = open('test.txt', 'w')
        # i = 0
        # while(True):
        #     hub.sleep(1)
        #     f.write(str(i) + '\n')
        #     print(i)
        #     i += 1
        #     f.write(str(self.gateway_manager.gateway_port_speed))
        #     f.write('\n')
        #     print(self.gateway_manager.gateway_port_speed)
        #
        #     if i >= 30:
        #         f.close()
        return

























