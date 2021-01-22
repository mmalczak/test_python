import pickle
import sys
from multiprocessing import Process

import numpy as np
import zmq


class worker_class:
    def fft(self, data):
        data = np.fft.fft(data)

    def empty_loop(self, length):
        for i in range(0, length):
            pass

    def random_gen(self, length):
        r = np.random.rand(length)

    def receive_array(self, array):
        pass


def socket_process(process_num):
    context = zmq.Context()
    socket = context.socket(zmq.ROUTER)
    port = 5550 + process_num
    ip = sys.argv[1]
    socket.bind("tcp://" + ip + ":" + str(port))
    while True:
        [identity, message] = socket.recv_multipart()
        message = pickle.loads(message)
        getattr(worker_class(), message["task"])(message["args"])
        socket.send_multipart([identity, b"Success"])


num_cores = 8
processes = []
for i in range(0, num_cores):
    processes.append(Process(target=socket_process, args=(i,)))
for i in range(0, num_cores):
    processes[i].start()
for i in range(0, num_cores):
    processes[i].join()
