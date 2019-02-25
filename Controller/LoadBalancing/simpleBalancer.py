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


class MyBalancerSwitch(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	### OFP_VERSIONS: menentukan versi OpenFlow yang dipakai, disini memakai versi OF 1.3
	
	def __init__(self, *args, **kwargs):
		super(MyBalancerSwitch, self).__init__(*args, **kwargs)
		self.hostDB = {}	#berisi pairing antara host.ID - port number

	def add_flow(self, datapath, match, actions, priority):
		ofproto = datapath.ofproto
		
		#instruksi dasar untuk mengeksekusi semua perintah di daftar actions
		inst = [datapath.ofproto_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
		mod = datapath.ofproto_parser.OFPFlowMod(
			datapath=datapath,								#switch id
			cookie=0, cookie_mask=0,
			table_id=0,												#nomor Flow table dimana flow rule di install 
			command=ofproto.OFPFC_ADD,
			idle_timeout=0, hard_timeout=0,			#timeout = 0 -> tidak memiliki timeout
			priority=priority,												#menentukan urutan matching
			buffer_id=ofproto.OFP_NO_BUFFER,
			out_port=ofproto.OFPP_ANY,
			out_group=ofproto.OFPG_ANY,
			flags=0,
			match=match,										#perintah match
			instructions=inst)									#perintah actions
		datapath.send_msg(mod)
	
	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)	
	def switch_features_handler(self, ev):
		msg = ev.msg
		dp = msg.datapath
		ofproto = dp.ofproto
		ofparser = dp.ofproto_parser
		
		if (dp.id ==1):
			#50-50 balancing
			buckets = []
			weight = 50
			actions = [dp.ofproto_parser.OFPActionOutput(2, 0)]
			buckets.append(ofparser.OFPBucket(weight=weight,actions=actions))
			weight = 50
			actions = [dp.ofproto_parser.OFPActionOutput(3, 0)]
			buckets.append(ofparser.OFPBucket(weight=weight,actions=actions))
			req = ofparser.OFPGroupMod(datapath=dp, command=ofproto.OFPGC_ADD, type_=ofproto.OFPGT_SELECT, group_id=1, buckets=buckets)
			dp.send_msg(req)
			
			match = ofparser.OFPMatch(in_port = 1, eth_type=0x800)
			actions = [dp.ofproto_parser.OFPActionGroup(1)]
			inst = [ofparser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
			mod = ofparser.OFPFlowMod(datapath=dp, table_id=0,priority=10, match=match, instructions=inst)
			dp.send_msg(mod)	
			
		elif (dp.id == 4):
			#from s2 and s3 forward to host 2 (port 1)
			match = dp.ofproto_parser.OFPMatch(in_port=2, eth_type=0x800)
			actions = [dp.ofproto_parser.OFPActionOutput(1, 0)]
			self.add_flow(dp, match, actions,1)
			match = dp.ofproto_parser.OFPMatch(in_port=3, eth_type=0x800)
			actions = [dp.ofproto_parser.OFPActionOutput(1, 0)]
			self.add_flow(dp, match, actions,1)
		else:
			#from in_port=1 (s1) forward to port 2 (s4)
			match = dp.ofproto_parser.OFPMatch(in_port=1, eth_type=0x800)
			actions = [dp.ofproto_parser.OFPActionOutput(2, 0)]
			self.add_flow(dp, match, actions,1)	

	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
		msg = ev.msg
		in_port = msg.match['in_port']
		dp = msg.datapath
		ofproto = dp.ofproto
		dpid = dp.id
		pkt = packet.Packet(msg.data)
