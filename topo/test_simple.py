from mininet.cli import CLI
from mininet.log import setLogLevel, info,error
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink

if __name__ == "__main__":
    default_hs_bw = 10
    default_ss_bw = 10
    default_gs_bw = 10
    default_ng_bw = 10

    setLogLevel("info")
    net = Mininet(switch=OVSSwitch, listenPort = 6633, ipBase='191.0.0.1/4')

    mycontroller = RemoteController("RemoteController")
    net.controllers = [mycontroller]
    net.nameToNode["RemoteController"] = mycontroller

    # host
    # tenant 1
    host1 = net.addHost('h1', ip="191.168.1.1", mac='00:00:00:00:00:01')
    host2 = net.addHost('h2', ip="191.168.1.4", mac='00:00:00:00:00:04')

    # switch
    switch1 = net.addSwitch('s1', ip="191.168.2.1", datapath='user')

    # host - switch
    net.addLink(host1, switch1, 1, 1, cls=TCLink, bw=default_hs_bw)
    net.addLink(host2, switch1, 1, 2, cls=TCLink, bw=default_hs_bw)

    net.start()
    CLI(net)
    net.stop()
