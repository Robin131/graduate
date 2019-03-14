from mininet.cli import CLI
from mininet.log import setLogLevel, info,error
from mininet.net import Mininet
from mininet.node import Node, RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.util import waitListening
from time import sleep


def connectToRootNS( network, switch, ip, routes ):
    root = Node( 'root', inNamespace=False )
    intf = network.addLink( root, switch).intf1
    root.setIP( ip, intf=intf )
    root.setMAC("10:00:00:00:00:00")

    network.start()
    sleep(10)
    for route in routes:
        root.cmd('route add -net ' + route + ' dev ' + str(intf))
        print("route add completed=================")
    for route in routes:
        root.cmd('route add -net ' + route + ' dev ' + str(intf))
        print("route add completed=================")

def sshd( network, cmd='/usr/sbin/sshd', opts='-D',
          ip='191.168.111.1/8', routes=None, switch=None ):
    if not switch:
        switch = network[ 's1' ]  # switch to use
    if not routes:
        routes = [ '191.0.0.0/8' ]
    connectToRootNS( network, switch, ip, routes )
    for host in network.hosts:
        print(host , "host==============")
        host.cmd( cmd + ' ' + opts + '&' ) # host.cmd('/usr/sbin/sshd -D &')
    info( "*** Waiting for ssh daemons to start\n" )
    for server in network.hosts:
        print(server)
        waitListening( server=server, port=22, timeout=5 )
    info( "\n*** Hosts are running sshd at the following addresses:\n" )
    for host in network.hosts:
        info( host.name, host.IP(), '\n' )
    info( "\n*** Type 'exit' or control-D to shut down network\n" )
    CLI( network )
    for host in network.hosts:
         host.cmd( 'kill %' + cmd )
    network.stop()


if __name__ == "__main__":
    default_hs_bw = 50
    default_ss_bw = 50
    default_gs_bw = 50
    default_ng_bw = 50
    default_tunnel_bw = 10

    setLogLevel("info")
    net = Mininet(switch=OVSSwitch, listenPort=6633, ipBase='191.0.0.1/8')

    mycontroller = RemoteController("RemoteController")
    net.controllers = [mycontroller]
    net.nameToNode["RemoteController"] = mycontroller

    # host
    # tenant 1, datacenter 1
    host1 = net.addHost('h1', ip="191.168.1.1", mac='00:00:00:00:00:01')
    host4 = net.addHost('h4', ip="191.168.1.4", mac='00:00:00:00:00:04')
    host6 = net.addHost('h6', ip="191.168.1.6", mac='00:00:00:00:00:06')

    # tenant 2, datacenter 1
    host2 = net.addHost('h2', ip="191.168.1.2", mac='00:00:00:00:00:02')
    host3 = net.addHost('h3', ip="191.168.1.3", mac='00:00:00:00:00:03')
    host5 = net.addHost('h5', ip="191.168.1.5", mac='00:00:00:00:00:05')
    host7 = net.addHost('h7', ip="191.168.1.7", mac='00:00:00:00:00:07')

    # tenant 1, datacenter 2
    host21 = net.addHost('h21', ip="191.168.2.1", mac='00:00:00:00:00:21')

    # tenant 2, datacenter 2
    host22 = net.addHost('h22', ip="191.168.2.2", mac='00:00:00:00:00:22')

    # switch
    # datacenter 1
    switch1 = net.addSwitch('s1', ip="191.2.1.1", dpid='1')
    switch2 = net.addSwitch('s2', ip="191.2.1.2", dpid='2')
    switch3 = net.addSwitch('s3', ip="191.2.1.3", dpid='3')

    # datacenter 2
    switch21 = net.addSwitch('s21', ip="191.2.2.1", dpid='4')
    switch22 = net.addSwitch('s22', ip="191.2.2.2", dpid='5')

    # gateway
    # datacenter 1
    gateway1 = net.addSwitch('g1', ip="191.1.1.1", dpid='A')
    gateway2 = net.addSwitch('g2', ip="191.1.1.1", dpid='B')
    gateway3 = net.addSwitch('g3', ip="191.1.1.1", dpid='C')

    # datacenter 2
    gateway21 = net.addSwitch('g21', ip="191.1.1.1", dpid='D')
    gateway22 = net.addSwitch('g22', ip="191.1.1.1", dpid='E')
    gateway23 = net.addSwitch('g23', ip="191.1.1.1", dpid='F')

    # host - switch
    # tenant 1, datacenter 1
    net.addLink(host1, switch1, 1, 1, cls=TCLink, bw=default_hs_bw)
    net.addLink(host4, switch2, 1, 1, cls=TCLink, bw=default_hs_bw)
    net.addLink(host6, switch3, 1, 1, cls=TCLink, bw=default_hs_bw)

    # tenant 2, datacenter 1
    net.addLink(host2, switch1, 1, 2, cls=TCLink, bw=default_hs_bw)
    net.addLink(host3, switch1, 1, 3, cls=TCLink, bw=default_hs_bw)
    net.addLink(host5, switch2, 1, 2, cls=TCLink, bw=default_hs_bw)
    net.addLink(host7, switch3, 1, 2, cls=TCLink, bw=default_hs_bw)

    # tenant 1, datacenter 2
    net.addLink(host21, switch21, 1, 1, cls=TCLink, bw=default_hs_bw)
    net.addLink(host22, switch22, 1, 1, cls=TCLink, bw=default_hs_bw)

    # switch - switch
    # datacenter 1
    net.addLink(switch1, switch2, 4, 4, cls=TCLink, bw=default_ss_bw)
    net.addLink(switch2, switch3, 3, 3, cls=TCLink, bw=default_ss_bw)

    # datacenter 2
    net.addLink(switch21, switch22, 2, 2, cls=TCLink, bw=default_ss_bw)

    # switch - gateway
    # datacenter 1
    net.addLink(switch1, gateway1, 5, 1, cls=TCLink, bw=default_gs_bw)
    net.addLink(switch1, gateway2, 6, 1, cls=TCLink, bw=default_gs_bw)
    net.addLink(switch1, gateway3, 7, 1, cls=TCLink, bw=default_gs_bw)

    net.addLink(switch2, gateway1, 5, 2, cls=TCLink, bw=default_gs_bw)
    net.addLink(switch2, gateway2, 6, 2, cls=TCLink, bw=default_gs_bw)
    net.addLink(switch2, gateway3, 7, 2, cls=TCLink, bw=default_gs_bw)

    net.addLink(switch3, gateway1, 4, 3, cls=TCLink, bw=default_gs_bw)
    net.addLink(switch3, gateway2, 5, 3, cls=TCLink, bw=default_gs_bw)
    net.addLink(switch3, gateway3, 6, 3, cls=TCLink, bw=default_gs_bw)

    # switch - gateway
    # datacenter 2
    net.addLink(switch21, gateway21, 3, 1, cls=TCLink, bw=default_gs_bw)
    net.addLink(switch21, gateway22, 4, 1, cls=TCLink, bw=default_gs_bw)
    net.addLink(switch21, gateway23, 5, 1, cls=TCLink, bw=default_gs_bw)

    net.addLink(switch22, gateway21, 3, 2, cls=TCLink, bw=default_gs_bw)
    net.addLink(switch22, gateway22, 4, 2, cls=TCLink, bw=default_gs_bw)
    net.addLink(switch22, gateway23, 5, 2, cls=TCLink, bw=default_gs_bw)

    # gateway - gateway
    # datacenter 1
    net.addLink(gateway1, gateway2, 4, 4)
    net.addLink(gateway2, gateway3, 5, 4)
    net.addLink(gateway3, gateway1, 5, 5)

    # datacenter 2
    net.addLink(gateway21, gateway22, 3, 3)
    net.addLink(gateway22, gateway23, 4, 3)
    net.addLink(gateway23, gateway21, 4, 4)

    # gre tunnel
    net.addLink(gateway1, gateway21, 6, 5, cls=TCLink, bw=default_tunnel_bw)
    net.addLink(gateway2, gateway22, 6, 5, cls=TCLink, bw=default_tunnel_bw)
    net.addLink(gateway3, gateway23, 6, 5, cls=TCLink, bw=default_tunnel_bw)

    sshd(net)
    # net.start()
    # CLI(net)
    # net.stop()











