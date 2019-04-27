import cPickle as pickle

from main import conf_file

if __name__ == '__main__':
    this_dc = 1
    with open(conf_file, "rb") as f:
        f1 = f.read()
        network = pickle.load(f1)
        f.close()
    network.set_up_mininet(this_dc)

