from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink

if '__main__' == __name__:
	net = Mininet(controller=RemoteController, switch=OVSSwitch,
				link=TCLink, autoSetMacs = True)
	#OVSSwitch
	c0 = net.addController('c0', controller=RemoteController, port=6633)
	h1 = net.addHost('h1', ip = '10.0.0.1', MAC = '01:01:01:00:00:01')
	h2 = net.addHost('h2', ip = '10.0.0.2', MAC = '01:01:01:00:00:02')
	
	s = {}
	s[1] = net.addSwitch('s1')
	s[2] = net.addSwitch('s2')
	s[3] = net.addSwitch('s3')
	s[4] = net.addSwitch('s4')

	#add link
	net.addLink( h1, s[1], delay = '1ms')
	net.addLink( h2, s[4], delay = '1ms')
	                                           
	net.addLink( s[1], s[2], delay = '1ms')
	net.addLink( s[1], s[3], delay = '1ms')
	net.addLink( s[4], s[2], delay = '1ms')
	net.addLink( s[4], s[3], delay = '1ms')
	
	net.build()
	c0.start()
	for i in range(1,5):
		s[i].start([c0])
		s[i].cmd( 'ovs-vsctl set Bridge s'+str(i)+' protocols=OpenFlow13')
	CLI(net)
	net.stop()

#Run:
#sudo python simpleTree.py
