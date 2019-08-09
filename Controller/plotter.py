import random, time, sys
import matplotlib.pyplot as plt
import threading 


def randomval():
	sbx = []
	sby = []
	for i in range(10):
		sbx.append(i)
		sby.append(random.randint(1,20))
	return sbx, sby
	
def printchart(dtx, dty):
	plt.clf()
	plt.plot(dtx, dty, color='g')
	plt.xlabel('index')
	plt.ylabel('value')
	plt.title('Chart 1')
	plt.show()
	
	


def genchart(): 
	print("Generating chart:") 
	sbx, sby = randomval()
	printchart(sbx, sby) 
  
timer = threading.Timer(2.0, genchart) 
timer.start() 
print("Exit\n") 
