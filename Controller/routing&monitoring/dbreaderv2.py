import redis,sys
#name = sys.argv[1]
looping = True
rd = redis.Redis(host='localhost', port=6379, db=0)
while looping:
	print "#type exit to close the program"
	md = raw_input("read or delete <arg>:")
	param = md.split(" ")
	mode = param[0]
	if mode == "read":
		argval = param[1]#raw_input("type the record:")
		if rd.llen(argval) == 0:
			print "record "+argval+" is empty"
		else:			
			for i in range(rd.llen(argval)):
				print rd.lindex(argval,i)
	
	elif mode == "delete":
		#print "type exit to return to main menu"
		argval = param[1] #raw_input("delete all fields in:")
		if argval != "exit":
			rd.delete(argval)
	elif mode == "latest":
		argval = param[1]
		maxlist = rd.llen(argval)
		for i in range(maxlist-10,maxlist):
			print rd.lindex(argval,i)
	elif mode =="member":
		argval = param[1]
		print rd.smembers(argval)
	elif mode == "exit":
		looping = False
print "Bye..."
