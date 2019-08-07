import redis,sys
name = sys.argv[1]

rd = redis.Redis(host='localhost', port=6379, db=0)
print "Time","Pkt_rcv","Pkt_trx","Byte_rcv","Byte_trx"
for i in range(rd.llen(name)):
	print rd.lindex(name,i)
