import matplotlib.pyplot as plt
import numpy as np

# use ggplot style for more sophisticated visuals
#plt.style.use('ggplot')
dt1min = 0
dt1max = 0
dt2min = 0
dt2max = 0
ax1 = None
ax2 = None
isinit = False

def live_plotter(x_vec,y1_data,y2_data,line1,line2,identifier='',pause_time=0.1): 
	global isinit
	global ax1
	global ax2
	if line1==[]:
		# this is the call to matplotlib that allows dynamic plotting
		plt.ion()
		fig = plt.figure(figsize=(13,6))
		ax1 = fig.add_subplot(121)
		ax2 = fig.add_subplot(122)
		ax1.title.set_text('Aggregated data')
		ax2.title.set_text('Real time data')
		
		# create a variable for the line so we can later update it
		line1, = ax1.plot(x_vec,y1_data,'-o',alpha=0.8)        
		line2, = ax2.plot(x_vec,y2_data,'-o',alpha=0.8)    
		dt1min = np.min(y1_data)
		dt1max = np.max(y1_data)
		dt2min = np.min(y2_data)
		dt2max = np.max(y2_data)
		line2.set_ydata(y2_data)    
		#if np.min(y1_data)<=line1.axes.get_ylim()[0] or np.max(y1_data)>=line1.axes.get_ylim()[1]:
		ax1.set_ylim(dt1min-10,dt1max+10)
		#if np.min(y2_data)<=line2.axes.get_ylim()[0] or np.max(y2_data)>=line2.axes.get_ylim()[1]:
		ax2.set_ylim(dt2min-1,dt2max+1)
		
		#update plot label/title
		plt.ylabel('Numbers')
		#plt.title('Title: {}'.format(identifier))
        	plt.show()
		isinit = True
    	if isinit:
		dt1min = np.min(y1_data)
		dt1max = np.max(y1_data)
		dt2min = np.min(y2_data)
		dt2max = np.max(y2_data)
		line2.set_ydata(y2_data) 
		ax1.set_ylim(dt1min-10,dt1max+10)
		ax2.set_ylim(dt2min-1,dt2max+1)

	# after the figure, axis, and line are created, we only need to update the y-data
	line1.set_ydata(y1_data)
	line2.set_ydata(y2_data)
	# adjust limits if new data goes beyond bounds
	
	# this pauses the data so the figure/axis can catch up - the amount of pause can be altered above
	plt.pause(pause_time)
	
	# return line so we can update it again in the next iteration
    	return line1,line2
