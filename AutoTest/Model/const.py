
class TenantPriority(object):
    priority = {
        "LOW": 1,
        "HIGH": 2
    }
    LOW = 1,
    HIGH = 2

class LinkBandWidth(object):
    host_switch_bw = 10
    switch_switch_bw = 10
    gateway_switch_bw = 10
    nat_gateway_bw = 10
    gateway_gateway_bw = 10

class LinkType(object):
    hs_link = 1
    ss_link = 2
    gs_link = 3
    ng_link = 4
    gg_link = 5
