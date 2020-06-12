import zmq
from multiprocessing import Process
import pickle
import numpy as np


class worker_class():

    def fft(self, data):
        data = np.fft.fft(data)
        print("fft")
        print(data)

    def empty_loop(self, length):
        for i in range(0, length):
            pass
        print("empty_loop")

    def random_gen(self, length):
        r = np.random.rand(length)
        print(r)

    def receive_array(self, array):
        print(array)



def socket_process(process_num):
    context = zmq.Context()
    socket = context.socket(zmq.ROUTER)
    port = 5550 + process_num
    socket.bind("tcp://127.0.0.1:"+str(port))
    while True:
        [identity, message] = socket.recv_multipart()
        message = pickle.loads(message)
        getattr(worker_class(), message['task'])(message['args'])
        socket.send_multipart([identity, b"Success"])


num_cores = 4
processes = []
for i in range(0, num_cores):
    processes.append(Process(target=socket_process, args=(i,)))
for i in range(0, num_cores):
    processes[i].start()
for i in range(0, num_cores):
    processes[i].join()



