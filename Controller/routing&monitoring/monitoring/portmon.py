import matplotlib.pyplot as plt
import matplotlib.animation as animation
#from matplotlib import style
import redis, sys

rd = redis.Redis(host='localhost', port=6379, db=0)
#style.use('fivethirtyeight')

def getData(_argval, _prmval, _size):
	data = {}
	argval = _argval
	prmval = _prmval
	dtsize = _size
	maxlist = rd.llen(argval)
	if dtsize >= maxlist:
		dtsize = maxlist -1
	yval = []
	yval2 = []
	xval = []
	yerr = []
	xerr= []
	if maxlist >= dtsize+1:
		j = 0
		for i in range(maxlist-(dtsize+1),maxlist):
			strval = rd.lindex(argval,i)
			#print strval
			datastr = strval.split(",")
			#print datastr
			data[j] = int( datastr[prmval] )
			if j > 0:
				yval.append(data[j])
				yval2.append(data[j] - data[j-1])
				xval.append((5*j)-dtsize*5)
			j+=1
	prmval +=1
	for i in range(maxlist-(dtsize+1),maxlist):
		strval = rd.lindex(argval,i)
		#print strval
		datastr = strval.split(",")
		data[j] = int( datastr[prmval] )
		if j > 0:
			yerr.append(data[j])
			xerr.append((5*j)-dtsize*5)
	return xval, yval, yval2, xerr, yerr

swinfo = sys.argv[1].split("-")
fig = plt.figure(num="switch "+swinfo[0]+" port:"+swinfo[1])

ax1 = fig.add_subplot(2,3,1)
ax2 = fig.add_subplot(2,3,2)
ax3 = fig.add_subplot(2,3,3)
ax4 = fig.add_subplot(2,3,4)
ax5 = fig.add_subplot(2,3,5)
ax6 = fig.add_subplot(2,3,6)

def animate(i):
	xval = []
	yval = []
	yval2 = []
	x1val, y1agg, y1cur, x1err, y1err = getData( sys.argv[1], 2, int(sys.argv[2]) )
	x2val, y2agg, y2cur, x2err, y2err = getData( sys.argv[1], 5, int(sys.argv[2]) )
	ax1.clear()
	ax2.clear()
	ax3.clear()
	ax4.clear()
	ax5.clear()
	ax6.clear()
	ax1.title.set_text('Aggreated Tx-bytes')
	ax2.title.set_text('Current Tx-bytes')
	ax3.title.set_text('Error Tx')
	ax4.title.set_text('Aggregated Rx-bytes')
	ax5.title.set_text('Current Rx-bytes')
	ax6.title.set_text('error Rx')
	ax1.plot(x1val, y1agg)
	ax2.plot(x1val, y1cur)
	ax3.plot(x1err, y1err)
	ax4.plot(x2val, y2agg)
	ax5.plot(x2val, y2cur)
	ax6.plot(x2err, y2err)

ani = animation.FuncAnimation(fig, animate, interval=1000)
plt.show()
