import random
from ryu.base import app_manager										
from ryu.controller import ofp_event									
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls							
from ryu.ofproto import ofproto_v1_3									
from ryu.lib.packet import packet										
from ryu.lib.packet import ethernet		
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import icmp								
from ryu.lib.packet import ether_types
from bloom_filter import BloomFilter

class MyFilterSwitch(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	### OFP_VERSIONS: menentukan versi OpenFlow yang dipakai, disini memakai versi OF 1.3
	'''
	def randomFilter(self, seed, maxcount):
		random.seed(seed)
		def randomIP(upperbound):
			return str(random.randint(1, upperbound))
		allIP = []
		for i in range(maxcount):
			newIP =  "10." + "0" + "." + randomIP(10) + "." + randomIP(250)
			print newIP
			allIP.append(newIP)
			self.bloom.add(newIP)
		print "IP address blocked: "+str(len(allIP))
	'''	
	def __init__(self, *args, **kwargs):
		super(MyFilterSwitch, self).__init__(*args, **kwargs)
		self.hostDB = {}	#berisi pairing antara host.ID - port number
		self.bloom = BloomFilter(max_elements=10000, error_rate=0.1)
		self.randomFilter(12345678, 1000)
	
	def add_flow(self, datapath, match, actions):
		ofproto = datapath.ofproto
		
		#instruksi dasar untuk mengeksekusi semua perintah di daftar actions
		inst = [datapath.ofproto_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
		mod = datapath.ofproto_parser.OFPFlowMod(
			datapath=datapath,				#switch id
			cookie=0, cookie_mask=0,
			table_id=0,					#nomor Flow table dimana flow rule di install 
			command=ofproto.OFPFC_ADD,
			idle_timeout=0, hard_timeout=0,			#timeout = 0 -> tidak memiliki timeout
			priority=0,					#menentukan urutan matching
			buffer_id=ofproto.OFP_NO_BUFFER,
			out_port=ofproto.OFPP_ANY,
			out_group=ofproto.OFPG_ANY,
			flags=0,
			match=match,					#perintah match
			instructions=inst)				#perintah actions
		datapath.send_msg(mod)
	
	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)	
	def switch_features_handler(self, ev):
		msg = ev.msg
		dp = msg.datapath
		ofproto = dp.ofproto
		
		#semua paket IP tanyakan ke controller
		match = dp.ofproto_parser.OFPMatch(eth_type=0x800) 
		actions = [dp.ofproto_parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,ofproto.OFPCML_NO_BUFFER)]
		
		self.add_flow(dp, match, actions)	

	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
		msg = ev.msg
		in_port = msg.match['in_port']
		dp = msg.datapath
		ofproto = dp.ofproto
		dpid = dp.id
		pkt = packet.Packet(msg.data)

		pkt_ipv4 = pkt.get_protocols(ipv4.ipv4)
		
		if pkt_ipv4:
			pkt_ipv4 = pkt.get_protocols(ipv4.ipv4)[0]
			dst_ip =  pkt_ipv4.dst
			print "new request: ",dst_ip
			if dst_ip in self.bloom:
				#pasang flow rule untuk mendrop paket
				match = dp.ofproto_parser.OFPMatch(in_port=1,eth_type=0x800,ip_proto=0x11,ipv4_dst=dst_ip)
				actions = []
				self.add_flow(dp, match, actions,2)
				print ("install flow rule, match: IP to "+dst_ip+" output:drop")
			else:
				#pasang flow rule untuk memforward paket ke host 2
				actions = [dp.ofproto_parser.OFPActionOutput(2 , 0)]
				data = msg.data
				out = dp.ofproto_parser.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
				dp.send_msg(out)
				
				#install flowrule untuk memforward paket ke host 2 tanpa menghubungi controller
				match = dp.ofproto_parser.OFPMatch(in_port=1,eth_type=0x800,ip_proto=0x11,ipv4_dst=dst_ip)
				actions = [dp.ofproto_parser.OFPActionOutput(2 , 0)]
				self.add_flow(dp, match, actions,2)
				print ("install flow rule, match: IP to "+dst_ip+" output:2")
		



