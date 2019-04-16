from ryu.lib.packet import packet, ethernet, arp
from multiprocessing import Queue
import six

from FlowManager2 import FlowManager
from MacManager2 import MacManager


class ArpManager(object):
    def __init__(self,
                 arp_table,
                 pmac_to_vmac,
                 gateway_ip,
                 gateways,
                 dpid_to_vmac,
                 switch_gateway_connection,
                 datapathes,
                 host_gateway):
        super(ArpManager, self).__init__()

        self.arp_table = arp_table
        self.pmac_to_vmac = pmac_to_vmac
        self.gateway_ip = gateway_ip
        self.gateways = gateways
        self.dpid_to_vmac = dpid_to_vmac
        self.switch_gateway_connection = switch_gateway_connection
        self.datapathes = datapathes
        self.host_gateway = host_gateway

        self.gateway_round_robin_queue = {}             # {datacenter_id -> Queue}

    # create an arp pkt according to original pkt and dst_vmac
    def _create_arp_pkt(self, original_pkt, dst_vmac):
        i = iter(original_pkt)
        pkt_ethernet = six.next(i)
        assert type(pkt_ethernet) == ethernet.ethernet
        pkt_arp = six.next(i)
        assert type(pkt_arp) == arp.arp

        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=pkt_ethernet.ethertype,
                                           dst=pkt_arp.src_mac, src=dst_vmac))
        pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                                 src_mac=dst_vmac,
                                 src_ip=pkt_arp.dst_ip,
                                 dst_mac=pkt_arp.src_mac,
                                 dst_ip=pkt_arp.src_ip))
        pkt.serialize()
        return pkt

    def handle_arp(self, datapath, in_port, tenant_id, pkt):

        i = iter(pkt)
        pkt_ethernet = six.next(i)
        assert type(pkt_ethernet) == ethernet.ethernet

        src_vmac = pkt_ethernet.src

        pkt_arp = six.next(i)
        assert type(pkt_arp) == arp.arp

        # test
        print(str(pkt_arp.src_mac) + ' ask mac for ' + pkt_arp.dst_ip)

        parser = datapath.ofproto_parser
        dst_ip = pkt_arp.dst_ip
        src_ip = pkt_arp.src_ip
        dst_pmac = ''

        # TODO deal with arp reply becuase there is something wired in Ping process
        if not pkt_arp.opcode == arp.ARP_REQUEST:
            print('Its a reply from ' + pkt_ethernet.src + ' and is to ' + dst_ip)
            return

        # first check whether it is requesting a gateway mac
        if dst_ip in self.gateway_ip:
            # check which datacenter this src is in
            datacenter_id = MacManager.get_datacenter_id_with_vmac(src_vmac)

            if src_vmac in ['12:00:01:00:01:01',
                            '12:00:01:00:02:01',
                            '11:00:02:00:03:02',
                            '12:00:01:00:01:08']:
                gateway_id = 10
                gateway_vmac = self.dpid_to_vmac[gateway_id]
            elif src_vmac in ['11:00:02:00:01:02',
                              '11:00:02:00:02:02']:
                gateway_id = 11
                gateway_vmac = self.dpid_to_vmac[gateway_id]
            elif src_vmac in ['11:00:02:00:01:03',
                              '12:00:01:00:03:01']:
                gateway_id = 12
                gateway_vmac = self.dpid_to_vmac[gateway_id]
            elif src_vmac in ['21:00:02:00:05:01']:
                gateway_id = 14
                gateway_vmac = self.dpid_to_vmac[gateway_id]
            elif src_vmac in ['22:00:01:00:04:01']:
                gateway_id = 13
                gateway_vmac = self.dpid_to_vmac[gateway_id]
            else:
                return

            # test
            print(gateway_id)
            print(gateway_vmac)

            # fake a arp pkt and answer, wait to send
            pkt = self._create_arp_pkt(pkt, gateway_vmac)
            actions = [parser.OFPActionOutput(port=in_port)]
            out = datapath.ofproto_parser.OFPPacketOut(
                datapath=datapath, in_port=datapath.ofproto.OFPP_CONTROLLER,
                buffer_id=datapath.ofproto.OFP_NO_BUFFER, actions=actions,
                data=pkt
            )


            #install flow entry for switch in table 8
            src_dpid = MacManager.get_dpid_with_vmac(src_vmac)
            dp = self.datapathes[src_dpid]
            ofproto = dp.ofproto
            parser = datapath.ofproto_parser

            out_port = self.switch_gateway_connection[(src_dpid, gateway_id)][0]

            match = parser.OFPMatch(eth_src=src_vmac)
            actions = [parser.OFPActionOutput(out_port)]
            instructions = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

            FlowManager.add_flow(dp, 1, match, instructions, table_id=8, buffer_id=None)

            # send the pkt
            datapath.send_msg(out)

            self.host_gateway[src_vmac] = gateway_id
            return

        # TODO NAT ask for host
        elif False:
            return
        # it is one host requesting another host ip
        else:
            # check if it is master host asking
            if src_vmac == '12:00:01:00:01:08':
                for tenant_id in self.arp_table.keys():
                    if dst_ip in self.arp_table[tenant_id].keys():
                        dst_pmac = self.arp_table[tenant_id][dst_ip]
                    else:
                        continue
                dst_vmac = self.pmac_to_vmac[dst_pmac]
                # fake a arp pkt and answer
                pkt = self._create_arp_pkt(pkt, dst_vmac)
                actions = [parser.OFPActionOutput(port=in_port)]
                out = datapath.ofproto_parser.OFPPacketOut(
                    datapath=datapath, in_port=datapath.ofproto.OFPP_CONTROLLER,
                    buffer_id=datapath.ofproto.OFP_NO_BUFFER, actions=actions,
                    data=pkt
                )
                # gateway
                dst_datacenter_id = MacManager.get_datacenter_id_with_vmac(dst_vmac)
                src_datacenter_id = MacManager.get_datacenter_id_with_vmac(src_vmac)
                if dst_datacenter_id != src_datacenter_id:
                    if not src_vmac in self.host_gateway.keys():
                        # need to install gateway flow entry
                        if src_vmac in ['12:00:01:00:01:01',
                                        '12:00:01:00:02:01',
                                        '11:00:02:00:03:02',
                                        '12:00:01:00:01:08']:
                            gateway_id = 10
                            gateway_vmac = self.dpid_to_vmac[gateway_id]
                        elif src_vmac in ['11:00:02:00:01:02',
                                          '11:00:02:00:02:02']:
                            gateway_id = 11
                            gateway_vmac = self.dpid_to_vmac[gateway_id]
                        elif src_vmac in ['11:00:02:00:01:03',
                                          '12:00:01:00:03:01']:
                            gateway_id = 12
                            gateway_vmac = self.dpid_to_vmac[gateway_id]
                        elif src_vmac in ['21:00:02:00:05:01']:
                            gateway_id = 14
                            gateway_vmac = self.dpid_to_vmac[gateway_id]
                        elif src_vmac in ['22:00:01:00:04:01']:
                            gateway_id = 13
                            gateway_vmac = self.dpid_to_vmac[gateway_id]
                        else:
                            return

                        # install flow entry
                        src_dpid = MacManager.get_dpid_with_vmac(src_vmac)
                        print(src_dpid)
                        print('++++++++++++++++++++++++++++++++++++++++++++++')
                        dp = self.datapathes[src_dpid]
                        ofproto = dp.ofproto
                        parser = datapath.ofproto_parser

                        out_port = self.switch_gateway_connection[(src_dpid, gateway_id)][0]

                        match = parser.OFPMatch(eth_src=src_vmac)
                        actions = [parser.OFPActionOutput(out_port)]
                        instructions = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

                        FlowManager.add_flow(dp, 1, match, instructions, table_id=8, buffer_id=None)
                        self.host_gateway[src_vmac] = gateway_id

                datapath.send_msg(out)
                return

            # check if it is asking master host
            if dst_ip == '191.168.111.1':
                dst_vmac = '12:00:01:00:01:08'
                # fake a arp pkt and answer
                pkt = self._create_arp_pkt(pkt, dst_vmac)
                actions = [parser.OFPActionOutput(port=in_port)]
                out = datapath.ofproto_parser.OFPPacketOut(
                    datapath=datapath, in_port=datapath.ofproto.OFPP_CONTROLLER,
                    buffer_id=datapath.ofproto.OFP_NO_BUFFER, actions=actions,
                    data=pkt
                )

                # gateway
                dst_datacenter_id = MacManager.get_datacenter_id_with_vmac(dst_vmac)
                src_datacenter_id = MacManager.get_datacenter_id_with_vmac(src_vmac)
                if dst_datacenter_id != src_datacenter_id:
                    if not src_vmac in self.host_gateway.keys():
                        # need to install gateway flow entry
                        if src_vmac in ['12:00:01:00:01:01',
                                        '12:00:01:00:02:01',
                                        '11:00:02:00:03:02',
                                        '12:00:01:00:01:08']:
                            gateway_id = 10
                            gateway_vmac = self.dpid_to_vmac[gateway_id]
                        elif src_vmac in ['11:00:02:00:01:02',
                                          '11:00:02:00:02:02']:
                            gateway_id = 11
                            gateway_vmac = self.dpid_to_vmac[gateway_id]
                        elif src_vmac in ['11:00:02:00:01:03',
                                          '12:00:01:00:03:01']:
                            gateway_id = 12
                            gateway_vmac = self.dpid_to_vmac[gateway_id]
                        elif src_vmac in ['21:00:02:00:05:01']:
                            gateway_id = 14
                            gateway_vmac = self.dpid_to_vmac[gateway_id]
                        elif src_vmac in ['22:00:01:00:04:01']:
                            gateway_id = 13
                            gateway_vmac = self.dpid_to_vmac[gateway_id]
                        else:
                            return

                        # install flow entry
                        src_dpid = MacManager.get_dpid_with_vmac(src_vmac)
                        print(src_dpid)
                        print('++++++++++++++++++++++++++++++++++++++++++++++')
                        dp = self.datapathes[src_dpid]
                        ofproto = dp.ofproto
                        parser = datapath.ofproto_parser

                        out_port = self.switch_gateway_connection[(src_dpid, gateway_id)][0]

                        match = parser.OFPMatch(eth_src=src_vmac)
                        actions = [parser.OFPActionOutput(out_port)]
                        instructions = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

                        FlowManager.add_flow(dp, 1, match, instructions, table_id=8, buffer_id=None)
                        self.host_gateway[src_vmac] = gateway_id

                datapath.send_msg(out)
                return

            # if there is record for this dst_ip, get dst_pmac from arp_table
            if dst_ip in self.arp_table[tenant_id].keys():
                dst_pmac = self.arp_table[tenant_id][dst_ip]
            else:
                return

        if not dst_pmac in self.pmac_to_vmac.keys():
            print('arp error:no such host recorded for ip:', dst_ip)
            print(dst_pmac)
            return
        dst_vmac = self.pmac_to_vmac[dst_pmac]
        # test
        # print('This packet is from ' + pkt_ethernet.src + ' and is to ' + dst_ip)
        print('reply ' + str(pkt_arp.src_mac) + ', the mac for ' + pkt_arp.dst_ip +
              ' is ' + str(dst_vmac))

        # check whether this pkt is in other datacenters
        # if it is, install flow entry to table 8 (send to gateway)
        dst_datacenter_id = MacManager.get_datacenter_id_with_vmac(dst_vmac)
        src_datacenter_id = MacManager.get_datacenter_id_with_vmac(src_vmac)
        if dst_datacenter_id != src_datacenter_id:
            if not src_vmac in self.host_gateway.keys():
                # need to install gateway flow entry
                if src_vmac in ['12:00:01:00:01:01',
                                '12:00:01:00:02:01',
                                '11:00:02:00:03:02',
                                '12:00:01:00:01:08']:
                    gateway_id = 10
                    gateway_vmac = self.dpid_to_vmac[gateway_id]
                elif src_vmac in ['11:00:02:00:01:02',
                                  '11:00:02:00:02:02']:
                    gateway_id = 11
                    gateway_vmac = self.dpid_to_vmac[gateway_id]
                elif src_vmac in ['11:00:02:00:01:03',
                                  '12:00:01:00:03:01']:
                    gateway_id = 12
                    gateway_vmac = self.dpid_to_vmac[gateway_id]
                elif src_vmac in ['21:00:02:00:05:01']:
                    gateway_id = 14
                    gateway_vmac = self.dpid_to_vmac[gateway_id]
                elif src_vmac in ['22:00:01:00:04:01']:
                    gateway_id = 13
                    gateway_vmac = self.dpid_to_vmac[gateway_id]
                else:
                    return

                # install flow entry
                src_dpid = MacManager.get_dpid_with_vmac(src_vmac)
                print(src_dpid)
                print('++++++++++++++++++++++++++++++++++++++++++++++')
                dp = self.datapathes[src_dpid]
                ofproto = dp.ofproto
                parser = datapath.ofproto_parser

                out_port = self.switch_gateway_connection[(src_dpid, gateway_id)][0]

                match = parser.OFPMatch(eth_src=src_vmac)
                actions = [parser.OFPActionOutput(out_port)]
                instructions = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

                FlowManager.add_flow(dp, 1, match, instructions, table_id=8, buffer_id=None)
                self.host_gateway[src_vmac] = gateway_id


        # fake a arp pkt and answer
        pkt = self._create_arp_pkt(pkt, dst_vmac)
        actions = [parser.OFPActionOutput(port=in_port)]
        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, in_port=datapath.ofproto.OFPP_CONTROLLER,
            buffer_id=datapath.ofproto.OFP_NO_BUFFER, actions=actions,
            data=pkt
        )

        datapath.send_msg(out)

    def init_arp(self):
        return