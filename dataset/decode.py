from scapy.all import *

file_name = './univ2_pt0'

if __name__ == '__main__':
    with PcapReader(file_name) as pcap_reader:
        print(repr(pcap_reader.read_packet()))
        print(repr(pcap_reader.read_packet()))