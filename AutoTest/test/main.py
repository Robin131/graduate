import sys
sys.path.append('../..')

from AutoTest.Model.Network import Network


conf_file = '../config/net.json'

if __name__ == '__main__':
    network = Network(conf_file)
    network.save(minute=1)
