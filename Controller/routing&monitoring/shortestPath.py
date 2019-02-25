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
from ryu.lib import hub
import networkx as nx
import matplotlib.pyplot as plt
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link

#arp table selalu diperbaharui, meski telah diperoleh hasilnya akan direset
#1st option: access switch ==> a flow rule to send an arp reply
#2nd option: install shortest path not only for ip but also arp

class MyL3Switch(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	### OFP_VERSIONS: menentukan versi OpenFlow yang dipakai, disini memakai versi OF 1.3

	def computeSP(self,src=None,dst=None):
		aclist = []
		for sw in self.swAcsList:
			aclist.append(sw.id)
		
		for idsw in aclist:
			path = nx.single_source_shortest_path(self.G,idsw)
			#print path
			for idsw2 in aclist:
				if idsw != idsw2:
					self.SP[(idsw,idsw2)] = path[idsw2]
		print "self.SP:",self.SP			
		
	def updateSPRules(self, ipdst):
		#self.hostDB[sipv4] = (dp.id, in_port)
		srcSwID = self.hostDB[ipdst][0]
		for sw in self.swAcsList:
			if sw.id != srcSwID:
				key = (sw.id, srcSwID)
				path = self.SP[key]
				print "path:",path
				for index in range(len(path)-1):
					#print path[index],"-",path[index+1]	
					dp = self.swListDB[path[index]]
					dstPort = self.adjInfo[(path[index],path[index+1])]
					match = dp.ofproto_parser.OFPMatch(eth_type=0x800,ipv4_dst=ipdst)
					actions = [dp.ofproto_parser.OFPActionOutput(dstPort,0)]
					self.add_flow(dp, match, actions, 10)
					#match = dp.ofproto_parser.OFPMatch(eth_type=0x806,arp_tpa=ipdst)
					#actions = [dp.ofproto_parser.OFPActionOutput(dstPort,0)]
					#self.add_flow(dp, match, actions, 10)	
			else:				
				#send to host
				dp = sw
				dstPort = 1
				match = dp.ofproto_parser.OFPMatch(eth_type=0x800,ipv4_dst=ipdst)
				actions = [dp.ofproto_parser.OFPActionOutput(dstPort,0)]
				self.add_flow(dp, match, actions, 10)
				#match = dp.ofproto_parser.OFPMatch(eth_type=0x806,arp_tpa=ipdst)
				#actions = [dp.ofproto_parser.OFPActionOutput(dstPort,0)]
				#self.add_flow(dp, match, actions, 10)
					
		'''core.py => self.SP: {
		(1, 2): [1, 5, 2],    (1, 3): [1, 5, 8, 3], (1, 4): [1, 5, 8, 4],
		(3, 2): [3, 8, 5, 2], (3, 4): [3, 8, 4],    (3, 1): [3, 8, 5, 1],
		(4, 1): [4, 8, 5, 1], (4, 3): [4, 8, 3],    (4, 2): [4, 8, 5, 2],
		(2, 3): [2, 5, 8, 3], (2, 1): [2, 5, 1],    (2, 4): [2, 5, 8, 4]
		}'''

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
			self.G = nx.Graph()
			self.G.clear()
			for lk in self.lkList:
				self.G.add_edge(lk.src.dpid,lk.dst.dpid)
			print "self.G:",self.G,"End"
			drawGraph()

		#ryu-manager <path/this_file> --observe-links
		self.swList = get_switch(self.topology_api_app, None)
		self.swListID =[switch.dp.id for switch in self.swList]
		self.lkList = get_link(self.topology_api_app, None)
		#self.lkListInfo =[(link.src.dpid,link.dst.dpid,{'port':link.src.port_no}) for link in self.lkList]
		for link in self.lkList:
			self.adjInfo[(link.src.dpid, link.dst.dpid)] = link.src.port_no
		print "Topology:"
		print self.swListID
		print self.adjInfo
		convertToGraph()
	
	def __init__(self, *args, **kwargs):
		super(MyL3Switch, self).__init__(*args, **kwargs)
		self.swList = []		#daftar switch
		self.swListDB = {}		#switch DB
		self.hostDB = {}		#berisi pairing antara host.ID - port number
		self.swAcsList = []		#daftar access switch
		self.SP = {}			#ker:value => (srcid, dstid) = [list of path (sw.id)]
		self.topology_api_app = self
		self.G = nx.Graph()
		self.adjInfo = {}
		self.topo_thread = hub.spawn(self._monitor)
	
	def _monitor(self):
		self.topolink = None
		self.toponode = None
		while True:
			topolink = self.G.edges()
			toponode = self.G.nodes()
			if self.topolink != topolink or self.toponode != toponode:
				self.topolink = topolink
				self.toponode = toponode
				self.computeSP()
			else:
				print self.topolink, self.toponode
				print topolink, toponode
			hub.sleep(5)

	def add_flow(self, datapath, match, actions, priority=0):
		ofproto = datapath.ofproto
		
		#instruksi dasar untuk mengeksekusi semua perintah di daftar actions
		inst = [datapath.ofproto_parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
		mod = datapath.ofproto_parser.OFPFlowMod(
			datapath=datapath,				#switch id
			cookie=0, cookie_mask=0,
			table_id=0,					#nomor Flow table dimana flow rule di install 
			command=ofproto.OFPFC_ADD,
			idle_timeout=0, hard_timeout=0,			#timeout = 0 -> tidak memiliki timeout
			priority=priority,					#menentukan urutan matching
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

			#install flow rule
			#if pkt_arp.opcode == 2:
			self.updateSPRules(sipv4)
		
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
		
