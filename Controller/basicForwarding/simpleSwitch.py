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


class MyL2Switch(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	### OFP_VERSIONS: menentukan versi OpenFlow yang dipakai, disini memakai versi OF 1.3
	
	def __init__(self, *args, **kwargs):
		super(MyL2Switch, self).__init__(*args, **kwargs)
		self.swList = []		#daftar switch
		self.hostDB = {}	#berisi pairing antara host.ID - port number

	def add_flow(self, datapath, match, actions,priority=0):
		ofproto = datapath.ofproto
		
		#instruksi dasar untuk mengeksekusi semua perintah di daftar actions
		inst = [datapath.ofproto_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
		mod = datapath.ofproto_parser.OFPFlowMod(
			datapath=datapath,		#switch id
			cookie=0, cookie_mask=0,
			table_id=0,			#nomor Flow table dimana flow rule di install 
			command=ofproto.OFPFC_ADD,
			idle_timeout=0, hard_timeout=0,	#timeout = 0 -> tidak memiliki timeout
			priority=priority,		#menentukan urutan matching
			buffer_id=ofproto.OFP_NO_BUFFER,
			out_port=ofproto.OFPP_ANY,
			out_group=ofproto.OFPG_ANY,
			flags=0,
			match=match,			#perintah match
			instructions=inst)		#perintah actions
		datapath.send_msg(mod)
	
	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)	
	def switch_features_handler(self, ev):
		msg = ev.msg
		dp = msg.datapath
		ofproto = dp.ofproto
		
		self.swList.append(dp)			#daftar switch yang terkoneksi	
		
		match = dp.ofproto_parser.OFPMatch(eth_type=0x806)  #0x806 -> ARP ethertype
		actions = [dp.ofproto_parser.OFPActionOutput(ofproto.OFPP_FLOOD, 0), 
					dp.ofproto_parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
					ofproto.OFPCML_NO_BUFFER)]
		#FLOOD --> khusus topologi acyclic.
		#Pada topologi cyclic --> endless flooding --> overhead
		
		#install flow rule, pada switch dp, dengan skema match-actions
		self.add_flow(dp, match, actions)				

	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
		msg = ev.msg
		in_port = msg.match['in_port']
		dp = msg.datapath
		ofproto = dp.ofproto
		dpid = dp.id
		pkt = packet.Packet(msg.data)
		pkt_arp = pkt.get_protocols(arp.arp)[0]
		
		if pkt_arp:
			print ("receiving arp packet")
			#ambil IP pengirim dan asosiasikan dengan input port.
			pkt_arp = pkt.get_protocol(arp.arp)
			sipv4 =  pkt_arp.src_ip
			self.hostDB[sipv4] = in_port
			
			#pasang flow rule, jika menerima paket ICMP dengan tujuan IP pengirim, kirim ke input_port 
			match = dp.ofproto_parser.OFPMatch(eth_type=0x800,ip_proto=0x01,ipv4_dst=sipv4)
			actions = [dp.ofproto_parser.OFPActionOutput(self.hostDB[sipv4] , 0)]
			self.add_flow(dp, match, actions, 1)
			print ("install flow rule: match: ICMP to "+sipv4+" output:"+str(in_port))



