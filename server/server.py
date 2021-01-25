import pickle
import sys
from multiprocessing import Process

import zmq

from server_control import controller_class
from server_workers import worker_class


def socket_process(ip, port, class_object):
    context = zmq.Context()
    socket = context.socket(zmq.ROUTER)
    socket.bind("tcp://" + ip + ":" + str(port))
    while True:
        [identity, message] = socket.recv_multipart()
        message = pickle.loads(message)
        ret = getattr(class_object, message["task"])(message["args"])
        socket.send_multipart([identity, ret])


ip = sys.argv[1]
base_port = 5550


num_conn = 8
processes = []
processes.append(
    Process(
        target=socket_process,
        args=(
            ip,
            base_port,
            controller_class(),
        ),
    )
)
for i in range(1, num_conn + 1):
    processes.append(
        Process(
            target=socket_process,
            args=(
                ip,
                base_port + i,
                worker_class(),
            ),
        )
    )
for i in range(0, num_conn + 1):
    processes[i].start()
for i in range(0, num_conn + 1):
    processes[i].join()
