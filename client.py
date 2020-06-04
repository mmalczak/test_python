import zmq
import pickle
import time
import numpy as np

context = zmq.Context()

num_conn = 4

#task = "fft"
#args = [1]+[0]*255
#args = [1]
#task = "empty_loop"
#args = 500000
task = "random_gen"
args = 10
#task = "receive_array"
#args = [1, 2, 3, 4, 5]

message = pickle.dumps({'task':task, 'args':args})

sockets = []
for i in range(0, num_conn):
    port = 5550 + i
    sockets.append(context.socket(zmq.DEALER))
    sockets[i].connect("tcp://127.0.0.1:"+str(port))

length = 1000
f = 16
t = np.array(range(0, length))/length
#sig = (np.sin(2 * np.pi * f * t + np.pi / 2) + 1) / 2 / 50
c = 10
#sig = [1/5 if (el%(length/f)<(length/(c*2*f))) else 0 for el in range(length)]

#problem length modulation
#sig = (np.sin(2 * np.pi * f * t - np.pi / 2) + 1) / 2 * 50000
sig = (np.sin(2 * np.pi * f * t - np.pi / 2) + 1) / 2 * 500

#sig = np.ones(length)/10000

time_diff=0
for j in range(0, length):
#    args = [1]+[0]*int(sig[j])
    args = int(sig[j])
    message = pickle.dumps({'task':task, 'args':args})
    print(args)
    start = time.time()
    for i in range(0, num_conn):
        sockets[i].send(message)
    for i in range(0, num_conn):
        data = sockets[i].recv()
#        print(data)
    time.sleep(0.02)
    #time_diff = time.time() - start
    #sleep_time = sig[j] - time_diff
    #if sleep_time > 0:
    #    time.sleep(sleep_time)
#    print("sig")
#    print(sig[j])
#    print("time")
#    print(time.time()-start)

