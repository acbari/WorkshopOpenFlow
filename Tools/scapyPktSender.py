import sys,datetime
from scapy.all import *

#example: python scapyPktSender.py 10.0.100.100 45

ipsrc = "10.0.0.1"
ipdst = sys.argv[1] 
dest_iface = '01:01:01:00:00:'+sys.argv[2]
pkt = Ether(type=0x800, dst=dest_iface)/IP(src=ipsrc, dst=ipdst)/UDP(sport=9999,dport=9999)	
sendp(pkt, iface='h1-eth0')
time.sleep(0.5)
