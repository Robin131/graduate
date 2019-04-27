import cPickle as pickle
import sys
sys.path.append('..')

from Model.Network import pickle_file


if __name__ == '__main__':
    this_dc = 1
    with open(pickle_file, "rb") as f:
        network = pickle.load(f)
    network.set_up_mininet(this_dc)

