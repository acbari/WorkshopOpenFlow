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
	if maxlist >= dtsize+1:
		j = 0
		for i in range(maxlist-(dtsize+1),maxlist):
			strval = rd.lindex(argval,i)
			print strval
			datastr = strval.split(",")
			data[j] = int( datastr[prmval] )
			if j > 0:
				yval.append(data[j])
				yval2.append(data[j] - data[j-1])
				xval.append((5*j)-dtsize*5)
			j+=1
	return xval, yval, yval2

fig = plt.figure()
ax1 = fig.add_subplot(2,2,1)
ax2 = fig.add_subplot(2,2,2)
ax3 = fig.add_subplot(2,2,3)
ax4 = fig.add_subplot(2,2,4)


def animate(i):
	xval = []
	yval = []
	yval2 = []
	x1val, y1agg, y1cur = getData( sys.argv[1], 1, int(sys.argv[2]) )
	x2val, y2agg, y2cur = getData( sys.argv[1], 2, int(sys.argv[2]) )
	ax1.clear()
	ax2.clear()
	ax3.clear()
	ax4.clear()
	ax1.title.set_text('Aggregated packets')
	ax2.title.set_text('Current packets')
	ax3.title.set_text('Aggregated bytes')
	ax4.title.set_text('Current bytes')
	ax1.plot(x1val, y1agg)
	ax2.plot(x1val, y1cur)
	ax3.plot(x2val, y2agg)
	ax4.plot(x2val, y2cur)

ani = animation.FuncAnimation(fig, animate, interval=1000)
plt.show()
