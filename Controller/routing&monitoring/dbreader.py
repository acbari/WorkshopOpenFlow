import redis,sys
name = sys.argv[1]

rd = redis.Redis(host='localhost', port=6379, db=0)
print "Time","Pkt rcv","Pkt trx","Byte rcv","Byte trx"
for i in range(rd.llen(name)):
	print rd.lindex(name,i)
