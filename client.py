import zmq
import pickle
import time
import numpy as np

context = zmq.Context()

num_conn = 4

task = "fft"
args = [1]+[0]*31
#args = [1]
#task = "empty_loop"
#args = 100000000
#task = "random_gen"
#args = 10
#task = "receive_array"
#args = [1, 2, 3, 4, 5]

message = pickle.dumps({'task':task, 'args':args})

sockets = []
for i in range(0, num_conn):
    port = 5550 + i
    sockets.append(context.socket(zmq.DEALER))
    sockets[i].connect("tcp://127.0.0.1:"+str(port))

length = 1000
f = 6
t = np.array(range(0, length))/length
sig = (np.sin(2 * np.pi * f * t - np.pi / 2) + 1) / 2 / 50
#sig = np.ones(length)/10000

time_diff=0
for j in range(0, length):
    start = time.time()
    for i in range(0, num_conn):
        sockets[i].send(message)
    for i in range(0, num_conn):
        data = sockets[i].recv()
#        print(data)
    time.sleep(sig[j])
    #time_diff = time.time() - start
    #sleep_time = sig[j] - time_diff
    #if sleep_time > 0:
    #    time.sleep(sleep_time)
#    print("sig")
#    print(sig[j])
#    print("time")
#    print(time.time()-start)

