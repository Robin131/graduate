# -*- coding:utf-8 -*-

class BaseError(Exception):
    ERROR_CODE = 0

    def __init__(self, code=ERROR_CODE, message='Error'):
        self.code = code
        self.message = message


class Errors(object):

    no_tenant_error = BaseError(1, '租户数量为0')
    no_datacenter_error = BaseError(2, '数据中心数量为0')
    ip_overflow = BaseError(3, 'host数量超过子网限制')
