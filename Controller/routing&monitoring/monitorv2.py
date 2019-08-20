from operator import attrgetter
import redis, time
from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub


class SimpleMonitor13(simple_switch_13.SimpleSwitch13):

    def __init__(self, *args, **kwargs):
        super(SimpleMonitor13, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
	self.Portinfo = []
	self.timex = str(time.time())
	print self.timex
	self.rd = redis.Redis(host='localhost', port=6379, db=0)
	

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
		self.timex = str(time.time())
		for dp in self.datapaths.values():
			self._request_stats(dp)
		hub.sleep(5)

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body
	for stat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match['in_port'],
                                             flow.match['eth_dst'])):
		portIn = stat.match['in_port']
		portOut = stat.instructions[0].actions[0].port
		matchval = stat.match['eth_dst']
		bytecount = str(stat.byte_count)
		pktcount = str(stat.packet_count)
		recordname = "sw"+str(ev.msg.datapath.id*1)+"-"+str(portIn)+"-"+str(matchval)
		self.rd.rpush(recordname, self.timex+","+pktcount+","+bytecount)
		if not(self.rd.sismember("recordname", recordname)):
			self.rd.sadd("recordname", recordname)
		print "insert:",recordname, pktcount+","+bytecount

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        for stat in sorted(body, key=attrgetter('port_no')):
		portIn = str(stat.port_no)
		if stat.port_no < 100:
			recordname = "sw"+str(ev.msg.datapath.id*1)+"-"+portIn
			self.rd.rpush(recordname, self.timex+","+str(stat.tx_packets)+","+str(stat.tx_bytes)+","+str(stat.tx_errors)+","+str(stat.rx_packets)+","+str(stat.rx_bytes)+","+str(stat.rx_errors))
			if not(self.rd.sismember("recordname", recordname)):
				self.rd.sadd("recordname", recordname)
			print "insertTx:",recordname, self.timex+","+str(stat.tx_packets)+","+str(stat.tx_bytes)+","+str(stat.tx_errors)+","+str(stat.rx_packets)+","+str(stat.rx_bytes)+","+str(stat.rx_errors)
			
