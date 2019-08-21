#from pylive import live_plotter
from pylive2 import live_plotter
import numpy as np
import time, sys
import redis

rd = redis.Redis(host='localhost', port=6379, db=0)
argval = sys.argv[1]
prmval = int(sys.argv[2])
size = 100
x_vec = np.linspace(0,1,size+1)[0:-1]
y_vec = np.random.randn(len(x_vec))
line1 = []
line2 = []
data = {}
while True:
	yval = []
	yval2 = []
	xval = []
	maxlist = rd.llen(argval)
	if maxlist > 11:
		j = 0
		for i in range(maxlist-11,maxlist):
			strval = rd.lindex(argval,i)
			print strval
			datastr = strval.split(",")
			data[j] = int( datastr[prmval] )
			if j > 0:
				yval.append(data[j])
				yval2.append(data[j] - data[j-1])
				xval.append((5*j)-50)
			j+=1
	#rand_val = np.random.randn(1)
	#y_vec[-1] = rand_val
	x_vec = np.array(xval)
	y_vec = np.array(yval)
	y_vec2 = np.array(yval2)
	line1,line2 = live_plotter(x_vec,y_vec,y_vec2,line1,line2)
	y_vec = np.append(y_vec[1:],0.0)
	time.sleep(0.5)
