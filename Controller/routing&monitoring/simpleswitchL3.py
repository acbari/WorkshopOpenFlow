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
import networkx as nx
import matplotlib.pyplot as plt
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link

class MyL3Switch(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	### OFP_VERSIONS: menentukan versi OpenFlow yang dipakai, disini memakai versi OF 1.3
	

	def computeSP(self,src,dst):
		

	@set_ev_cls(event.EventSwitchEnter)
	def get_topology_data(self, ev):
		def drawGraph():
			pos = nx.spring_layout(self.G)
			nx.draw_networkx_nodes(self.G, pos, node_size = 500)
			nx.draw_networkx_labels(self.G, pos)
			black_edges = [edge for edge in self.G.edges()]
			nx.draw_networkx_edges(self.G, pos, edgelist=black_edges, arrows=False)		
			#plt.show() #it will halt the program, close the window to continue
			plt.savefig('topology.png')
			plt.clf()		

		def convertToGraph():
			#self.G = nx.Graph()
			self.G.clear()
			for lk in self.lkListInfo:
				self.G.add_edge(str(lk[0]), str(lk[1]))
			#print self.G.nodes()
			#print self.G.edges()
			#drawGraph()

		#  ryu-manager <path/this_file> --observe-links
		self.swList = get_switch(self.topology_api_app, None)
		self.swListID =[switch.dp.id for switch in self.swList]
		self.lkList = get_link(self.topology_api_app, None)
		self.lkListInfo =[(link.src.dpid,link.dst.dpid,{'port':link.src.port_no}) for link in self.lkList]
		
		#print self.swList
		#print self.swListID
		#print self.lkList		
		#print self.lkListInfo
		
		convertToGraph()
	
	def __init__(self, *args, **kwargs):
		super(MyL3Switch, self).__init__(*args, **kwargs)
		self.swList = []		#daftar switch
		self.swListDB = {}		#switch DB
		self.hostDB = {}	#berisi pairing antara host.ID - port number
		self.swAcsList = []		#daftar access switch
		self.SP = {}			#ker:value => (srcid, dstid) = [list of path (sw.id)]

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
	
	def delflowintable(self,dp):
		ofp = dp.ofproto
		parser = dp.ofproto_parser
		del_flows = parser.OFPFlowMod(dp, table_id=ofp.OFPTT_ALL, out_port=ofp.OFPP_ANY, out_group=ofp.OFPG_ANY, command=ofp.OFPFC_DELETE) 
		dp.send_msg(del_flows)
		print "deleting all flow entries in all table of sw-",dp.id

	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)	
	def switch_features_handler(self, ev):
		msg = ev.msg
		dp = msg.datapath
		ofproto = dp.ofproto

		print "config sw:",dp.id
		self.delflowintable(dp)

		self.swList.append(dp)	#daftar switch		
		for sw in self.swList:
			self.swListDB[sw.id] = sw
			if sw.id < 5 and not(sw in self.swAcsList):
				self.swAcsList.append(sw)
		print "Access sw:",len(self.swAcsList), self.swAcsList
		if dp.id < 5:	
			match = dp.ofproto_parser.OFPMatch(eth_type=0x806)  #0x806 -> ARP ethertype
			actions = [dp.ofproto_parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,ofproto.OFPCML_NO_BUFFER)]
			self.add_flow(dp, match, actions)
			
			match = dp.ofproto_parser.OFPMatch(eth_type=0x800,ip_proto=0x01)  #0x800, proto 0x01 -> ICMP
			actions = [dp.ofproto_parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,ofproto.OFPCML_NO_BUFFER)]
			self.add_flow(dp, match, actions)		
	
	def sendPacketArp(self, datapath, msg, pkt):		
		for dp in self.swAcsList:
			ofproto = dp.ofproto
			if dp.id != datapath.id:#bukan switch penerima arp dari host		
				actions = [dp.ofproto_parser.OFPActionOutput(1 , 0)]
				data =msg.data
				out = dp.ofproto_parser.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
				  						in_port=ofproto.OFPP_CONTROLLER, actions=actions, data=data)
				dp.send_msg(out)
				print "sent to: S-", dp.id, " port:1"

	def sendPacketICMP(self, datapath, msg, pkt, dstIP):
		dstTpl = self.hostDB[dstIP]
		val  = int(dstTpl[0])
		print val
		dp = self.swListDB[val]	
		portdst = 1#int(dstTpl[1])
		ofproto = dp.ofproto
		actions = [dp.ofproto_parser.OFPActionOutput(portdst , 0)]
		data =msg.data
		out = dp.ofproto_parser.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
		  						in_port=ofproto.OFPP_CONTROLLER, actions=actions, data=data)
		dp.send_msg(out)
		print "sent to: S-", dp.id, " port:", portdst
	
	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
		msg = ev.msg
		in_port = msg.match['in_port']
		dp = msg.datapath
		ofproto = dp.ofproto
		dpid = dp.id
		pkt = packet.Packet(msg.data)
		
		print pkt
		pkt_ethernet = pkt.get_protocols(ethernet.ethernet)[0]
		#print pkt_ethernet.ethertype
		pkt_arp = pkt.get_protocols(arp.arp)		

		if pkt_arp:
			pkt_arp = pkt.get_protocols(arp.arp)[0]
			print ("receiving arp packet")
			#ambil IP pengirim dan asosiasikan dengan switch dan input port.
			pkt_arp = pkt.get_protocol(arp.arp)
			sipv4 =  pkt_arp.src_ip
			self.hostDB[sipv4] = (dp.id, in_port)

			#kirim ke semua access switch yg lain
			self.sendPacketArp(dp, msg, pkt)
		
		pkt_ipv4 = pkt.get_protocols(ipv4.ipv4)
		if pkt_ipv4:
			pkt_ipv4 = pkt.get_protocols(ipv4.ipv4)[0]
		pkt_icmp = pkt.get_protocols(icmp.icmp)	
		if pkt_icmp:
			pkt_icmp = pkt.get_protocols(icmp.icmp)[0]
			#kirim ke access switch yg sesuai
			if pkt_icmp.type == 0:#reply
				dst_ip = pkt_ipv4.dst
				print "DB:",self.hostDB[dst_ip]
				self.sendPacketICMP(dp, msg, pkt, dst_ip)
			if pkt_icmp.type == 8:#request
				dst_ip = pkt_ipv4.dst
				print "DB:",self.hostDB[dst_ip]
				self.sendPacketICMP(dp, msg, pkt, dst_ip)
		
