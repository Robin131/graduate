import re
from AutoTest.Model.const import FilePath, IperfArg
import os


if __name__ == '__main__':

    sev_path = FilePath.server_res_path

    pkt_loss_arg = r'([0-9]+)\ *\/\ *([0-9]+)'
    pkt_received = 0
    pkt_sent = 0

    # iperf bug for too many pkts
    max_pkt = IperfArg.max_pkt

    ls = os.listdir(sev_path)
    for file in ls:
        if os.path.isdir(file):
            continue
        file = sev_path + '/' + file
        with open(file, 'r') as f:
            raw = f.readlines()
            for line in raw:
                result = re.search(pkt_loss_arg, line)
                if result:
                    received = int(result.group(1))
                    sent = int(result.group(2))
                    if sent >= max_pkt:
                        continue
                    pkt_sent += sent
                    pkt_received += received
                else:
                    continue
    pkt_loss = (pkt_sent - pkt_received) / float(pkt_sent)
    print(pkt_loss)