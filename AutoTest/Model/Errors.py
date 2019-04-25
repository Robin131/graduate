# -*- coding:utf-8 -*-

class BaseError(Exception):
    ERROR_CODE = 0

    def __init__(self, code=ERROR_CODE, message='Error'):
        self.code = code
        self.message = message


class Errors(object):

    no_tenant_error =                                   BaseError(1, '租户数量为0')
    no_datacenter_error =                               BaseError(2, '数据中心数量为0')
    ip_overflow =                                       BaseError(3, 'host数量超过子网限制')
    no_conf =                                           BaseError(4, '无配置信息')
    conf_no_mac_num =                                   BaseError(5, '缺少最大mac地址配置信息')
    conf_no_datacenters =                               BaseError(6, '缺少数据中心配置信息')
    conf_no_alter_ip =                                  BaseError(7, '缺少子网配置信息')
    conf_no_tenant =                                    BaseError(8, '缺少租户配置信息')
    conf_no_topo_type =                                 BaseError(9, '缺少topo类型配置信息')
    conf_no_switch_ip =                                 BaseError(10, '缺少交换机ip信息')
    conf_no_hosts_per_switch =                          BaseError(11, '缺少交换机 - 主机密度配置信息')
    unknown_topo_type =                                 BaseError(12, '未知的topo类型')
    conf_no_hosts_per_gateway =                         BaseError(13, '缺少网关 - 主机密度配置信息')
    conf_no_gateway_ip =                                BaseError(14, '缺少网关ip配置信息')
    host_switch_conflict =                              BaseError(15, '拓扑中设置的密度与外层配置冲突')