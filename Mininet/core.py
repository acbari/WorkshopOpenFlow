from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink

if '__main__' == __name__:
	
	net = Mininet(controller=RemoteController, switch=OVSSwitch, link=TCLink, autoSetMacs = True)
	#OVSSwitch
	c0 = net.addController('c0', controller=RemoteController, port=6633)
	h1 = net.addHost('h1', ip='10.0.0.1', MAC='01:01:01:00:00:01')
	h2 = net.addHost('h2', ip='10.0.0.2', MAC='01:01:01:00:00:02')	
	h3 = net.addHost('h3', ip='10.0.0.3', MAC='01:01:01:00:00:03')
	h4 = net.addHost('h4', ip='10.0.0.4', MAC='01:01:01:00:00:04')
	
	s = {}
	s[1 ] = net.addSwitch('s1')
	s[2 ] = net.addSwitch('s2')
	s[3 ] = net.addSwitch('s3')
	s[4 ] = net.addSwitch('s4')
	s[5 ] = net.addSwitch('s5')
	s[6 ] = net.addSwitch('s6')
	s[7 ] = net.addSwitch('s7')
	s[8 ] = net.addSwitch('s8')
	
	#host-access links
	net.addLink( h1, s[1], delay='1ms')
	net.addLink( h2, s[2], delay='1ms')
	net.addLink( h3, s[3], delay='1ms')
	net.addLink( h4, s[4], delay='1ms')
	
	#access-core links
	net.addLink( s[1], s[5], delay='1ms')
	net.addLink( s[1], s[6], delay='1ms')
	net.addLink( s[2], s[5], delay='1ms')
	net.addLink( s[2], s[6], delay='1ms')
	net.addLink( s[3], s[7], delay='1ms')
	net.addLink( s[3], s[8], delay='1ms')
	net.addLink( s[4], s[7], delay='1ms')
	net.addLink( s[4], s[8], delay='1ms')
	
	#core-core links
	net.addLink( s[5], s[7], delay='1ms')
	net.addLink( s[5], s[8], delay='1ms')
	net.addLink( s[6], s[7], delay='1ms')
	net.addLink( s[6], s[8], delay='1ms')
	
	net.build()
	c0.start()
	for i in range(1,9):
		s[i].start([c0])
		s[i].cmd( 'ovs-vsctl set Bridge s'+str(i)+' protocols=OpenFlow13')
	
	CLI(net)
	net.stop()

#Run:
#sudo python simpleTree.py
