from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink

if '__main__' == __name__:
	
	net = Mininet(controller=RemoteController, switch=OVSSwitch, 
				link=TCLink, autoSetMacs = True)
	#OVSSwitch
	c0 = net.addController('c0', controller=RemoteController, port=6633)
	h1 = net.addHost('h1', ip='10.0.0.1', MAC='01:01:01:00:00:01')
	h2 = net.addHost('h2', ip='10.0.0.2', MAC='01:01:01:00:00:02')	
	h3 = net.addHost('h3', ip='10.0.0.3', MAC='01:01:01:00:00:03')
	
	s1 = net.addSwitch('s1')		

	#add link
	net.addLink( h1, s1, delay='1ms')
	net.addLink( h2, s1, delay='1ms')
	net.addLink( h3, s1, delay='1ms')

	net.build()
	c0.start()
	s1.start([c0])
	s1.cmd( 'ovs-vsctl set Bridge s1 protocols=OpenFlow13')
	CLI(net)
	net.stop()

#Run:
#sudo python simpleTree.py
