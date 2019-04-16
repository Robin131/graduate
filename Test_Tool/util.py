import cPickle as pickle

# generate a mac address list with len of MAX_MAC_NUM
def generate_MACs(max_mac_num):
    mac = []
    for i in range(1, max_mac_num + 1):
        mac.append(i)

    mac = [generate_mac_format(hex(i)) for i in mac]
    return mac

def generate_mac_format(hex_string):
    assert len(hex_string) >= 3
    hex_string = hex_string[2:]
    assert len(hex_string) <= 12
    zero_digit = 12 - len(hex_string)
    hex_string = '0' * zero_digit + hex_string
    res = ''
    digit_insert = [0, 2, 4, 6, 8]
    for i in digit_insert:
        res += hex_string[i] + hex_string[i+1] + ':'
    res += hex_string[10] + hex_string[11]
    return res

def generate_device_name(tenant_id, device_id, pre_name):
    tenant_id = str(tenant_id)
    assert len(tenant_id) <= 3
    t_zero_digit = 3 - len(tenant_id)
    device_id = str(device_id)
    assert len(device_id) <= 5
    h_zero_digit = 5 - len(device_id)
    res = pre_name + t_zero_digit * '0' + tenant_id + h_zero_digit * '0' + device_id
    return res

def generate_host_name(tenant_id, host_id, pre_name='h'):
    return generate_device_name(tenant_id, host_id, pre_name)

def generate_switch_name(dc_id, switch_id, pre_name='s'):
    return generate_device_name(dc_id, switch_id, pre_name)

def generate_gateway_name(dc_id, gateway_id, pre_name='g'):
    return generate_device_name(dc_id, gateway_id, pre_name)

# TODO build an ip pool
def generate_ip_4_gateway(dc_id, gateway_id):
    return '110.111.' + str(dc_id) + '.' + str(gateway_id)

def save_dict(dict, file_path):
    with open(file_path, "wb") as f:
        pickle.dump(dict, f)
        f.close()