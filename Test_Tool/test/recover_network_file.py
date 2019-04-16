import cPickle as pickle

from Test_Tool.test.save_network_file import fileName

if __name__=='__main__':
    with open(fileName, "rb") as f:
        network = pickle.load(f)
        network.init_net(datacenter_id=1)


