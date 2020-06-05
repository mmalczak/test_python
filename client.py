import zmq
import pickle
import time
import numpy as np

class Client():

    def __init__(self, task):
        self.context = zmq.Context()
        self.num_conn = 4
        self.task = task 
        self.sockets = []
        
        for i in range(0, self.num_conn):
            port = 5550 + i
            self.sockets.append(self.context.socket(zmq.DEALER))
            self.sockets[i].connect("tcp://10.10.10.1:"+str(port))

        self.control_socket = self.context.socket(zmq.DEALER)
        self.control_socket.connect("tcp://10.10.10.1:"+str(5540))

    def init_arrays(self, num_tasks):
        t = np.array(range(0, num_tasks))/num_tasks
        
        #delay modulation
        self.dm_sig_sin = (np.sin(2 * np.pi * delay_mod_freq * t + np.pi / 2) + 1) / 2 / 50
        c = 10
        #self.dm_sig_square = [1/5 if (el%(num_tasks/delay_mod_freq)<(num_tasks/(c*2*delay_mod_freq))) else 0 for el in range(num_tasks)]
        self.dm_sig_square = [0 if (el%(num_tasks/delay_mod_freq)<((2*c-1)/c)*(num_tasks/(2*delay_mod_freq))) else 1/5 for el in range(num_tasks)]
        
        #problem length modulation
        self.plm_sig_fft = (np.sin(2 * np.pi * prob_l_mod_freq * t - np.pi / 2) + 1) / 2 * 512
        self.plm_sig_empty_loop = (np.sin(2 * np.pi * prob_l_mod_freq * t - np.pi / 2) + 1) / 2 * 50000
        self.plm_sig_random_gen = (np.sin(2 * np.pi * prob_l_mod_freq * t - np.pi / 2) + 1) / 2 * 500

    def start(self, num_task, delay_mod_freq, prob_l_freq):
        self.init_arrays(num_tasks)

        ### Energy measurement start ###
        control_message = pickle.dumps({'task':'energy_measure_start', 'args':None})
        self.control_socket.send(control_message)
        data = self.control_socket.recv()
        ### Energy measurement start ###

        ### Time measurement start ###
        total_time_start = time.time()
        ### Time measurement start ###
        
        time_diff=0
        for j in range(0, num_tasks):
            args = [1]+[0]*int(self.plm_sig_fft[j])
        #    args = int(self.plm_sig_empty_loop[j])
        #    args = int(self.plm_sig_random_gen[j])
            message = pickle.dumps({'task':self.task, 'args':args})
            start = time.time()
            for i in range(0, self.num_conn):
                self.sockets[i].send(message)
            for i in range(0, self.num_conn):
                data = self.sockets[i].recv()
        #        print(data)
        
            time_diff = time.time() - start
            sleep_time = self.dm_sig_square[j] - time_diff
            if sleep_time > 0:
                time.sleep(sleep_time)
        #    print(time.time()-start)

        ### Time measurement stop ###
        total_time = time.time() - total_time_start
        ### Time measurement stop ###
        
        ### Energy measurement stop ###
        control_message = pickle.dumps({'task':'energy_measure_stop', 'args':None})
        self.control_socket.send(control_message)
        energy = self.control_socket.recv()
        energy = float(energy)
        ### Energy measurement stop ###
        return {'energy':energy, 'time':total_time}

# Available tasks with example arguments
# "fft" [1]+[0]*31
# "empty_loop" 500000
# "random_gen" 10
# "receive_array" [1, 2, 3, 4, 5]

task = "fft"
client = Client(task)
num_tasks = 10
delay_mod_freq = 6
prob_l_mod_freq = 3
ret = client.start(num_tasks, delay_mod_freq, prob_l_mod_freq)
print("Energy = {}".format(ret['energy']))
print("Total time = {}".format(ret['time']))


