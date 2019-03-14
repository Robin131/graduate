# -*- coding: utf-8 -*-
from ryu.lib import hub

from FlowManager2 import FlowManager
from Util2 import Util

# flow entry for switch for gateway
# -1: check whether this pkt is to NAT (yes Nat, no 0)
# 0 : check whether priority 1 (yes 3, no 1)
# 1 : send pkt to other gateway for Qos (go 2)                                              ok
# 2 : statistics (go 3)                                                                     ok
# 3 : check whether from NAT or arp from NAT (arp to controller, nat to 6, others to 4)     ok
# 4 : check whether mac_dst is to this datacenter (yes 6, no 5)                             ok
# 5 : send to other datacenters                                                             ok
# 6 : send to local switch                                                                  ok

class GatewayManager(object):
    def __init__(self,
                 gateways,
                 potential_gateway,
                 gateway_flow_table_inquire_time,
                 gateway_port_inquire_time,
                 gateway_datacenter_port_max_speed,
                 balance_time_interval,
                 datapathes,
                 all_datacenter_id,
                 topo_manager,
                 meter_manager):
        super(GatewayManager, self)

        self.gateways = gateways
        self.potential_gateway = potential_gateway
        self.gateway_flow_table_inquire_time = gateway_flow_table_inquire_time
        self.gateway_port_inquire_time = gateway_port_inquire_time
        self.gateway_datacenter_port_max_speed = gateway_datacenter_port_max_speed
        self.balance_time_interval = balance_time_interval
        self.datapathes = datapathes
        self.all_datacenter_id = all_datacenter_id
        self.topo_manager = topo_manager
        self.meter_manager = meter_manager

        self.balance_threshold = 0.9       # threshold need for balance
        self.free_threshold = 0.6           # threshold that can be seen as free

        self.dpid_flow = {}                 # gw_id -> {datacenter_id -> {dpid(switch) -> speed}}
        self.temp_dpid_flow = {}            # gw_id -> {datacenter_id ->{dpid -> {'duration', 'byte_count'}}}
        self.gateway_port_speed = {}        # gw_id -> {datacenter_id -> speed}
        self.temp_port_speed = {}           # gw_id -> {datacenter_id -> {'duration', 'rx_bytes', 'tx_bytes'}}

    def register_gateway(self, ev):
        datapath = ev.datapath
        dpid = datapath.id

        if dpid in [10, 11, 12]:
            datacenter_id = 1
        else:
            datacenter_id = 2

        if dpid in self.potential_gateway.keys():
            self.gateways[dpid] = self.potential_gateway[dpid]

        FlowManager.install_missing_flow_for_gateway(datapath)
        FlowManager.install_this_datacenter_flow(datapath, datacenter_id)
        FlowManager.check_priority_on_gateway(datapath)

        record = self.gateways[dpid]
        for (key, value) in record.items():
            if key == 'NAT':
                FlowManager.install_NAT_flow_for_gateway(datapath, value)
            # port to other datacenters
            elif isinstance(key, int):
                FlowManager.install_other_datacenter_flow(datapath, key, value)

        return

    # a hub to init gateway record
    def init_gateway_record(self):
        for gw_id in self.gateways.keys():
            self.temp_dpid_flow[gw_id] = {}
            if gw_id in [10, 11, 12]:
                this_datacenter_id = 1
            else:
                this_datacenter_id = 2
            for dpid in self.datapathes.keys():
                if dpid in self.gateways.keys():
                    continue
                elif gw_id in [10, 11, 12] and dpid in [4, 5]:
                    continue
                elif gw_id in [13, 14, 15] and dpid in [1, 2, 3]:
                    continue

                for datacenter_id in self.all_datacenter_id:
                    if datacenter_id != this_datacenter_id:
                        # dpid_flow
                        Util.add3DimDict(self.dpid_flow, gw_id, datacenter_id, dpid, 0)

                        # temp_dpid_flow
                        Util.add3DimDict(self.temp_dpid_flow[gw_id], datacenter_id, dpid, 'duration', 0)
                        Util.add3DimDict(self.temp_dpid_flow[gw_id], datacenter_id, dpid, 'byte_count', 0)



            for dst, port_no in self.gateways[gw_id].items():
                if dst == 'NAT':
                    continue
                # gateway_port_speed
                Util.add2DimDict(self.gateway_port_speed, gw_id, dst, 0)
                # temp_port_speed
                Util.add3DimDict(self.temp_port_speed, gw_id, dst, 'duration', 0)
                Util.add3DimDict(self.temp_port_speed, gw_id, dst, 'rx_bytes', 0)
                Util.add3DimDict(self.temp_port_speed, gw_id, dst, 'tx_bytes', 0)


    # a hub to inquire flow table info on gateway
    def inquiry_gateway_flow_table_info(self):
        hub.sleep(10)
        while (True):
            hub.sleep(self.gateway_flow_table_inquire_time)
            table_ids = [2]
            for gw_id in self.gateways.keys():
                gw = self.datapathes[gw_id]
                parser = gw.ofproto_parser

                for id in table_ids:
                    req = parser.OFPFlowStatsRequest(datapath=gw, table_id=id)
                    gw.send_msg(req)
    #
    # # a hub to inquire gre port connecting datacenters
    def inquiry_gateway_datacenter_port(self):
        hub.sleep(10)
        while (True):
            hub.sleep(self.gateway_port_inquire_time)
            for gw_id in self.gateways.keys():
                for dst, port_no in self.gateways[gw_id].items():
                    if type(dst) == int:
                        datapath = self.datapathes[gw_id]
                        ofp_parser = datapath.ofproto_parser

                        req = ofp_parser.OFPPortStatsRequest(datapath, 0, port_no)
                        datapath.send_msg(req)

    # handle gateway statistics info
    def gateway_statistics_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        gw_id = datapath.id

        for stat in ev.msg.body:
            eth_src = stat.match.get('eth_src')
            if eth_src is None:
                continue

            # decode dpid
            hex_str = ''
            for i in range(len(eth_src[1])):
                if i == 0:
                    continue
                elif eth_src[1][i] == 'f':
                    hex_str += eth_src[0][i]
            dpid = int(hex_str, 16)

            # decode datacenter
            eth_dst = stat.match.get('eth_dst')
            if eth_dst is None:
                continue
            hex_str = eth_dst[0][0]
            datacenter_id = int(hex_str, 16)

            # record flow amount
            byte_count = stat.byte_count
            duration = stat.duration_sec
            byte_difference = abs(self.temp_dpid_flow[gw_id][datacenter_id][dpid]['byte_count'] - byte_count)
            time_interval = abs(duration - self.temp_dpid_flow[gw_id][datacenter_id][dpid]['duration'])
            if time_interval == 0:
                speed = 0
            else:
                speed = byte_difference / time_interval

            self.temp_dpid_flow[gw_id][datacenter_id][dpid]['duration'] = duration
            self.temp_dpid_flow[gw_id][datacenter_id][dpid]['byte_count'] = byte_count
            self.dpid_flow[gw_id][datacenter_id][dpid] = speed
        return
    #
    # # handle datacenter port info
    def gateway_port_reply_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        dpid = dp.id

        for stat in ev.msg.body:
            port_no = stat.port_no
            duration = stat.duration_sec
            rx_bytes = stat.rx_bytes
            tx_bytes = stat.tx_bytes

            # get dst_datacenter_id
            dst_datacenter_id = self.get_dst_datacenter_id(dpid, port_no)

            all_bytes = abs(self.temp_port_speed[dpid][dst_datacenter_id]['rx_bytes'] - rx_bytes) + \
                abs(self.temp_port_speed[dpid][dst_datacenter_id]['tx_bytes'] - tx_bytes)
            time_interval = abs(duration - self.temp_port_speed[dpid][dst_datacenter_id]['duration'])
            if time_interval == 0:
                speed = 0
            else:
                speed = all_bytes / time_interval

            # update record
            self.temp_port_speed[dpid][dst_datacenter_id]['duration'] = duration
            self.temp_port_speed[dpid][dst_datacenter_id]['rx_bytes'] = rx_bytes
            self.temp_port_speed[dpid][dst_datacenter_id]['tx_bytes'] = tx_bytes

            self.gateway_port_speed[dpid][dst_datacenter_id] = speed

        return
    #
    # a hub to balance gateway
    def gateway_balance_hub(self):
        hub.sleep(11)
        while(True):
            hub.sleep(self.balance_time_interval)
            max_speed = self.gateway_datacenter_port_max_speed

            for gw_id in self.gateway_port_speed.keys():
                if gw_id in [13, 14, 15]:
                    continue
                for datacenter_id, speed in self.gateway_port_speed[gw_id].items():
                    # check whether too fast
                    if speed >= self.balance_threshold * max_speed:
                        print('*************************************')
                        print(self.gateway_port_speed)
                        print(self.dpid_flow)
                        # hub.sleep(1)
                        self.adjust_balance(datacenter_id, gw_id)
                        return
                    else:
                        continue
        return
    #
    # try to balance gateway for ports to datacenter_id
    def adjust_balance(self, datacenter_id, gw_id):
        # first check whether there is enough ability
        # port ability
        number = len([10, 11, 12])
        max_speed = self.gateway_datacenter_port_max_speed
        ability = number * max_speed

        actual = 0
        for id in [10, 11, 12]:
            for dpid in self.dpid_flow[id][datacenter_id].keys():
                actual += self.dpid_flow[id][datacenter_id][dpid]

        # test
        print(actual)
        print(ability)



        # able to send all pkts
        if True:
            free_gateway = self._find_free_gateway(datacenter_id)
            if free_gateway == -1:
                print('no free gateway ++++++++++++++++++++++++++++')
                print(self.gateway_port_speed)
                # TODO no free gateway
                return
            else:
                path = self.topo_manager.get_path(gw_id, free_gateway)
                print(gw_id)
                print(free_gateway)
                print(path)
                # pick some switches to free gateway
                dpids, speed = self._find_switches_for_free_gateway(gw_id, datacenter_id)
                # lead these dpids to free_gateway
                for dpid in dpids:
                    # TODO create log to recover
                    FlowManager.install_balance_flow_entry_for_gateway(self.datapathes[gw_id], dpid,
                                                                       1, path[0][1])
                return
        # unable to send all pkts
        else:
            print('adjusting=========================================')
            free_gateway = self._find_free_gateway(datacenter_id)
            dpids = []
            speed = 0
            if free_gateway == -1:
                # TODO no free gateway
                return
            else:
                path = self.topo_manager.get_path(gw_id, free_gateway)
                # pick some switches to free gateway
                dpids, speed = self._find_switches_for_free_gateway(gw_id, datacenter_id)
                # lead these dpids to free_gateway
                # see whether need to install meter to free_gateway
                original_speed = self.gateway_port_speed[free_gateway][datacenter_id]
                if True:
                # if original_speed + speed > max_speed:
                    # need to install meter
                    # meter_id = self.meter_manager.add_meter(datapath=self.datapathes[free_gateway],
                    #                                         speed=speed_difference)
                    # for dpid in dpids:
                    #     # TODO create log to recover
                    #     FlowManager.install_balance_flow_entry_for_gateway(self.datapathes[gw_id], dpid,
                    #                                                        self.datacenter_id, path[0][1],
                    #                                                        meter_id)

                    # send to queue
                    queue_id = 1
                    print('set to queue+++++++++++++++++++++++++++++++++')
                    for dpid in dpids:
                        FlowManager.install_gateway_balance_flow_with_queue(gateway=self.datapathes[gw_id],
                                                                            dpid=dpid,
                                                                            this_datacenter_id=1,
                                                                            queue_id=queue_id,
                                                                            port_no=path[0][1])
                else:
                    for dpid in dpids:
                        # TODO create log to recover
                        FlowManager.install_balance_flow_entry_for_gateway(self.datapathes[gw_id], dpid, 1, path[0][1])

                # TODO here are only for the test
                # set s2 on g1 to q2 on port 6
                FlowManager.install_gateway_balance_flow_with_queue(gateway=self.datapathes[gw_id],
                                                                    dpid=2,
                                                                    this_datacenter_id=1,
                                                                    queue_id=2,
                                                                    port_no=6)

                # set s3 on g3 to q3 on port 6
                FlowManager.install_gateway_balance_flow_with_queue(gateway=self.datapathes[12],
                                                                    dpid=3,
                                                                    this_datacenter_id=1,
                                                                    queue_id=3,
                                                                    port_no=6)


                # # check whether need to install meter for gw_id
                # if self.gateway_port_speed[gw_id][datacenter_id] - speed > max_speed:
                #     # TODO here only find the second biggest switch to add meter
                #     mark = 0
                #     mark_speed = 0
                #     for dpid in self.dpid_flow[gw_id][datacenter_id].keys():
                #         if dpid in dpids:
                #             continue
                #         if self.dpid_flow[gw_id][datacenter_id][dpid] > speed:
                #             mark = dpid
                #             mark_speed = self.dpid_flow[gw_id][datacenter_id][dpid]
                #     # TODO a fixed meter with 0.6
                #     meter_id = self.meter_manager.add_meter(datapath=self.datapathes[gw_id],
                #                                             speed=mark_speed * 0.6)
                #     FlowManager.install_limit_speed_flow_entry_for_gateway(self.datapathes[gw_id],
                #                                                            mark,
                #                                                            self.datacenter_id,
                #                                                            meter_id)
                # # check whether other gateway need to install speed limit entry
                # for id in self.gateways.keys():
                #     if id == gw_id or id == free_gateway:
                #         continue
                #     else:
                #         if self.gateway_port_speed[id][datacenter_id] > max_speed * self.balance_threshold:
                #             # TODO here only find the second biggest switch to add meter
                #             mark = 0
                #             mark_speed = 0
                #             for dpid in self.dpid_flow[id][datacenter_id].keys():
                #                 if dpid in dpids:
                #                     continue
                #                 if self.dpid_flow[id][datacenter_id][dpid] > speed:
                #                     mark = dpid
                #                     mark_speed = self.dpid_flow[id][datacenter_id][dpid]
                #             # TODO a fixed meter with 0.8
                #             meter_id = self.meter_manager.add_meter(datapath=self.datapathes[id],
                #                                                     speed=mark_speed * 0.8)
                #             FlowManager.install_limit_speed_flow_entry_for_gateway(self.datapathes[id],
                #                                                                    mark,
                #                                                                    self.datacenter_id,
                #                                                                    meter_id)
        return
    #
    # # get dst_datacenter_id according to gw_id and port_no
    def get_dst_datacenter_id(self, gw_id, port_no):
        for dst, port in self.gateways[gw_id].items():
            if port == port_no:
                return dst
            else:
                continue
        return

    # find a free gateway that can be borrowed
    def _find_free_gateway(self, datacenter_id):
        max_speed = self.gateway_datacenter_port_max_speed
        for gw_id in [10, 11, 12]:
            if self.gateway_port_speed[gw_id][datacenter_id] < self.free_threshold * max_speed:
                return gw_id

        return -1

    # find some switches for free gateway
    def _find_switches_for_free_gateway(self, gw_id, datacenter_id):
        # TODO change to a better way, now just choose the biggest one
        # mark = 0
        # mark_speed = 0
        # for dpid in self.dpid_flow[gw_id][datacenter_id].keys():
        #     if self.dpid_flow[gw_id][datacenter_id][dpid] > mark_speed:
        #         mark = dpid
        #         mark_speed = self.dpid_flow[gw_id][datacenter_id][dpid]
        #
        # return [mark], mark_speed
        return [1], self.dpid_flow[gw_id][datacenter_id][1]

