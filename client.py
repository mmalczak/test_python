import zmq
import pickle
import time
import numpy as np

class Client():

    def __init__(self):
        self.context = zmq.Context()
        
        self.num_conn = 4
        
        self.task = "fft"
        self.args = [1]+[0]*31
        #self.args = [1]
        #self.task = "empty_loop"
        #self.args = 500000
        #self.task = "random_gen"
        #self.args = 10
        #self.task = "receive_array"
        #self.args = [1, 2, 3, 4, 5]

        self.sockets = []
        for i in range(0, self.num_conn):
            port = 5550 + i
            self.sockets.append(self.context.socket(zmq.DEALER))
            self.sockets[i].connect("tcp://10.10.10.1:"+str(port))

        self.control_socket = self.context.socket(zmq.DEALER)
        self.control_socket.connect("tcp://10.10.10.1:"+str(5540))

    def start(self):
        ### Energy measurement start ###
        control_message = pickle.dumps({'task':'energy_measure_start', 'args':None})
        self.control_socket.send(control_message)
        data = self.control_socket.recv()
        ### Energy measurement start ###


        num_tasks = 10
        f = 6
        t = np.array(range(0, num_tasks))/num_tasks

        #delay modulation
        dm_sig_sin = (np.sin(2 * np.pi * f * t + np.pi / 2) + 1) / 2 / 50
        c = 10
        #dm_sig_square = [1/5 if (el%(num_tasks/f)<(num_tasks/(c*2*f))) else 0 for el in range(num_tasks)]
        dm_sig_square = [0 if (el%(num_tasks/f)<((2*c-1)/c)*(num_tasks/(2*f))) else 1/5 for el in range(num_tasks)]
        
        f = 3
        #problem length modulation
        plm_sig_fft = (np.sin(2 * np.pi * f * t - np.pi / 2) + 1) / 2 * 512
        plm_sig_empty_loop = (np.sin(2 * np.pi * f * t - np.pi / 2) + 1) / 2 * 50000
        plm_sig_random_gen = (np.sin(2 * np.pi * f * t - np.pi / 2) + 1) / 2 * 500
        
        #sig = np.ones(num_tasks)/10000
        
        total_time_start = time.time()
        
        time_diff=0
        for j in range(0, num_tasks):
            args = [1]+[0]*int(plm_sig_fft[j])
        #    args = int(plm_sig_empty_loop[j])
        #    args = int(plm_sig_random_gen[j])
            message = pickle.dumps({'task':self.task, 'args':args})
            start = time.time()
            for i in range(0, self.num_conn):
                self.sockets[i].send(message)
            for i in range(0, self.num_conn):
                data = self.sockets[i].recv()
        #        print(data)
            #time.sleep(dm_sig_sin[j])
        #    time.sleep(dm_sig_square[j])
        #    time.sleep(0.02)
        
            time_diff = time.time() - start
            sleep_time = dm_sig_square[j] - time_diff
            if sleep_time > 0:
                time.sleep(sleep_time)
        #    print("sig")
        #    print(sig[j])
        #    print("time")
        #    print(time.time()-start)

        total_time = time.time() - total_time_start
        
        ### Energy measurement stop ###
        control_message = pickle.dumps({'task':'energy_measure_stop', 'args':None})
        self.control_socket.send(control_message)
        energy = self.control_socket.recv()
        energy = float(energy)
        print("Energy = {}".format(energy))
        print("Total time = {}".format(total_time))
        ### Energy measurement stop ###

client = Client()
client.start()
