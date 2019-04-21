# -*- coding:utf-8 -*-
import cPickle as pickle

from Errors import Errors

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

    def get_with_index(self, index):
        assert index < len(self.pool)
        return self.pool[index]


class Util(object):

    @staticmethod
    def generate_MACs(max_mac_num):
        mac = []
        for i in range(1, max_mac_num + 1):
            mac.append(i)

        mac = [Util.generate_mac_format(hex(i)) for i in mac]
        return mac

    @staticmethod
    def generate_mac_format(hex_string):
        assert len(hex_string) >= 3
        hex_string = hex_string[2:]
        assert len(hex_string) <= 12
        zero_digit = 12 - len(hex_string)
        hex_string = '0' * zero_digit + hex_string
        res = ''
        digit_insert = [0, 2, 4, 6, 8]
        for i in digit_insert:
            res += hex_string[i] + hex_string[i + 1] + ':'
        res += hex_string[10] + hex_string[11]
        return res

    @staticmethod
    def generate_IPs(base, max_mac_num):
        ip = []
        _ = base.split('/')
        front = _[0]
        back = int(_[1])
        _ = front.split('.')

        def ip_format(_1, _2, _3, _4):
            return str(_1) + '.' + str(_2) + '.' + str(_3) + '.' + str(_4)

        _1, _2, _3, _4 = int(_[0]), int(_[1]), int(_[2]), int(_[3])
        for i in xrange(1, max_mac_num + 1):
            if _4 != 255:
                ip.append(ip_format(_1, _2, _3, _4 + 1))
                _4 += 1
            else:
                if back <= 8:
                    raise Errors.ip_overflow
                _4 = 0
                if _3 != 255:
                    ip.append(ip_format(_1, _2, _3 + 1, _4))
                    _3 += 1
                else:
                    if back <= 16:
                        raise Errors.ip_overflow
                    _3 = 0
                    if _2 != 255:
                        ip.append(ip_format(_1, _2 + 1, _3, _4))
                        _2 += 1
                    else:
                        raise Errors.ip_overflow
        return ip

    @staticmethod
    def generate_device_name(tenant_id, device_id, pre_name):
        tenant_id = str(tenant_id)
        assert len(tenant_id) <= 3
        t_zero_digit = 3 - len(tenant_id)
        device_id = str(device_id)
        assert len(device_id) <= 5
        h_zero_digit = 5 - len(device_id)
        res = pre_name + t_zero_digit * '0' + tenant_id + h_zero_digit * '0' + device_id
        return res

    @staticmethod
    def generate_host_name(tenant_id, host_id, pre_name='h'):
        return Util.generate_device_name(tenant_id, host_id, pre_name)

    @staticmethod
    def generate_switch_name(dc_id, switch_id, pre_name='s'):
        return Util.generate_device_name(dc_id, switch_id, pre_name)

    @staticmethod
    def generate_gateway_name(dc_id, gateway_id, pre_name='g'):
        return Util.generate_device_name(dc_id, gateway_id, pre_name)

