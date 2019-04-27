# -*- coding: utf-8 -*-
import cPickle as pickle
import sys
import abc

sys.path.append('..')

config_dic = '../AutoTest/Data/config.pkl'

class Configuration(object):
    def __init__(self, file, dc_id):
        super(Configuration, self).__init__()

        self.config_file = file
        self.dc_id = dc_id
        self.arp_table = None
        self.host_pmac = None
        self.tenant_level = None
        self.subnets = None
        self.potential_gateway = None
        self.gateway_datacenter_port = None
        self.gateway_ip = None
        self.tenant_speed = None
        self.all_datacenter_id = None

    @abc.abstractmethod
    def get_configuration(self, dc_id):
        pass

class DictionaryConfiguration(Configuration):
    def __init__(self, dc_id, file=config_dic):
        super(DictionaryConfiguration, self).__init__(file, dc_id)
        with open(config_dic, "rb") as f:
            self.dic = pickle.load(f)
            f.close()
        self.get_configuration(self.dc_id)

    def get_configuration(self, dc_id):
        dic = self.dic[dc_id]
        self.arp_table = dic['arp_table']
        self.host_pmac = dic['host_mac']
        self.tenant_level = dic['tenant_level']
        self.subnets = dic['subnets']
        self.potential_gateway = dic['potential_gateway']
        self.gateway_datacenter_port = dic['gateway_datacenter_port']
        self.gateway_ip = dic['gateway_ip']
        self.tenant_speed = dic['tenant_speed']
        self.all_datacenter_id = dic['all_datacenter_id']
        return

    def logging_dic(self):
        print(self.dic)


