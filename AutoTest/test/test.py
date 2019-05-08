import re
from AutoTest.Model.const import FilePath
import os


if __name__ == '__main__':

    pkt_loss_arg = r'([0-9]+)\ *\/\ *([0-9]+)'
    pkt_received = 0
    pkt_sent = 0

    serv_path = FilePath.server_res_path
    ls = os.listdir(serv_path)

    for file in ls:
        if os.path.isdir(file):
            continue
        file = serv_path + '/' + file
        with open(file, 'r') as f:
            raw = f.readlines()
            for line in raw:
                result = re.search(pkt_loss_arg, line)
                if result:
                    pkt_received += int(result.group(1))
                    pkt_sent += int(result.group(2))
                else:
                    continue
    pkt_loss = (pkt_sent - pkt_received) / float(pkt_sent)
    print(pkt_loss)