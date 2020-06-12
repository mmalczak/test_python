import zmq
import pickle
import time
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from confidence_ellipse import confidence_ellipse


def scatter_with_confidence_ellipse(data, ax_kwargs, color, marker, label):
    plt.scatter(data['energy_list'], data['time_list'], color=color,
                marker=marker, label=label)
    confidence_ellipse(data['energy_list'], data['time_list'], ax_kwargs,
                n_std=1, edgecolor=color)
    plt.xlabel('energy')
    plt.ylabel('time')

class Client():

    def __init__(self, task, num_tasks, delay_mod_freq, prob_l_mod_freq,
                    prob_l_mod_scale, num_measurements):
        self.task = task
        self.num_tasks = num_tasks
        self.delay_mod_freq = delay_mod_freq
        self.prob_l_mod_freq = prob_l_mod_freq
        self.prob_l_mod_scale = prob_l_mod_scale
        self.num_measurements = num_measurements

        self.context = zmq.Context()
        self.num_conn = 4
        self.sockets = []

        for i in range(0, self.num_conn):
            port = 5550 + i
            self.sockets.append(self.context.socket(zmq.DEALER))
            self.sockets[i].connect("tcp://127.0.0.1:"+str(port))

        self.control_socket = self.context.socket(zmq.DEALER)
        self.control_socket.connect("tcp://127.0.0.1:"+str(5540))

    def init_arrays(self):
        t = np.array(range(0, self.num_tasks))/self.num_tasks

        #delay modulation
        c = 10
        if self.delay_mod_freq == 0:
            self.dm_sig_square = [1 / 5] * self.num_tasks
        else:
            tasks_per_period = self.num_tasks/self.delay_mod_freq
            self.dm_sig_square = [0 if el % tasks_per_period <
                                        (2 * c - 1) / c * tasks_per_period / 2
                                    else 1 / 5 for el in range(self.num_tasks)]

        #problem length modulation
        if self.prob_l_mod_freq == 0:
            self.plm_sig_fft = [512 * self.prob_l_mod_scale] * self.num_tasks
        else:
            phase = 2 * np.pi * self.prob_l_mod_freq * t - np.pi / 2
            self.plm_sig_fft = (np.sin(phase) + 1) / 2 * 512 * self.prob_l_mod_scale

    def stress_server(self):
        time_diff=0
        for j in range(0, self.num_tasks):
            args = [1]+[0]*int(self.plm_sig_fft[j])
            message = pickle.dumps({'task':self.task, 'args':args})
            start = time.time()
            for i in range(0, self.num_conn):
                self.sockets[i].send(message)
            for i in range(0, self.num_conn):
                data = self.sockets[i].recv()

            time_diff = time.time() - start
            sleep_time = self.dm_sig_square[j] - time_diff
            if sleep_time > 0:
                time.sleep(sleep_time)

    def time_energy_measurement(self):
        self.init_arrays()

        ### Energy measurement start ###
        control_message = pickle.dumps({'task':'energy_measure_start',
                                        'args':None})
        self.control_socket.send(control_message)
        data = self.control_socket.recv()
        ### Energy measurement start ###

        ### Time measurement start ###
        total_time_start = time.time()
        ### Time measurement start ###

        self.stress_server()

        ### Time measurement stop ###
        total_time = time.time() - total_time_start
        ### Time measurement stop ###

        ### Energy measurement stop ###
        control_message = pickle.dumps({'task':'energy_measure_stop',
                                        'args':None})
        self.control_socket.send(control_message)
        energy = self.control_socket.recv()
        energy = float(energy)
        ### Energy measurement stop ###

        return {'energy':energy, 'time':total_time}

    def time_energy_stats(self):
        energy_list = []
        time_list = []
        for i in range(self.num_measurements):
            print("sample idx = " + str(i))
            ret = self.time_energy_measurement()
            energy_list.append(ret['energy'])
            time_list.append(ret['time'])

        return {'energy_list':energy_list, 'time_list':time_list}

    def set_scaling_governor(self, governor):
        control_message = pickle.dumps({'task':'set_scaling_governor',
                                        'args':governor})
        self.control_socket.send(control_message)
        status = self.control_socket.recv()

    def set_uc(self, uc):
        control_message = pickle.dumps({'task':'set_uc', 'args':uc})
        self.control_socket.send(control_message)
        status = self.control_socket.recv()

    def get_governor_data(self, governor, uc):
        print(governor)
        print("uc = " + str(uc))
        self.set_scaling_governor(governor)
        if uc is not 'NA':
            self.set_uc(uc)
        ret = self.time_energy_stats()
        return ret

    def governors_compare(self):
        print("Problem length modulation scale = " + str(self.prob_l_mod_scale))
        print("Number of tasks = " + str(self.num_tasks))
        ## warmup ##
        self.set_scaling_governor('ondemand')
        self.time_energy_stats()
        ## warmup ##

        sns.set()
        fig, ax_kwargs = plt.subplots()

        data_gov = self.get_governor_data('performance', 'NA')
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, (0.7, 0.7, 0.7), 'o', 'performance')
        data_gov = self.get_governor_data('powersave', 'NA')
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, (0.3, 0.3, 0.3), 'o', 'powersave')
        data_gov = self.get_governor_data('ondemand', 'NA')
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, (0, 0, 0), 's', 'ondemand')
        data_gov = self.get_governor_data('adaptive', 0)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'b', 'x', 'adaptive, uc = 0')
        data_gov = self.get_governor_data('adaptive', 20)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'g', 'x', 'adaptive, uc = 20')
        data_gov = self.get_governor_data('adaptive', 40)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'r', 'x', 'adaptive, uc = 50')
        data_gov = self.get_governor_data('adaptive', 50)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'c', 'x', 'adaptive, uc = 60')
        data_gov = self.get_governor_data('adaptive', 60)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'm', 'x', 'adaptive, uc = 80')
        data_gov = self.get_governor_data('adaptive', 80)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'y', 'x', 'adaptive, uc = 100')
        data_gov = self.get_governor_data('adaptive', 100)

        plt.legend()

#        plt.show()
        figure = plt.gcf()
        figure.set_size_inches(16, 12)
        plt.savefig('/home/milosz/work/test_python/plots/' +
                'num_tasks_' + str(self.num_tasks) +
                ' plm_scale_' + str(self.prob_l_mod_scale) + '.png')

    def sweep_num_tasks(self):
        num_tasks_list = [2, 4, 8]#, 16, 32, 64, 128, 256, 512, 1024]
        for num_tasks in num_tasks_list:
            self.num_tasks = num_tasks
            self.governors_compare()

# Available tasks with example arguments
# "fft" [1]+[0]*31
# "empty_loop" 500000
# "random_gen" 10
# "receive_array" [1, 2, 3, 4, 5]

task = "fft"
num_tasks = 6
delay_mod_freq = 6
prob_l_mod_freq = 3
prob_l_mod_scale = 1
num_measurements = 5
client = Client(task, num_tasks, delay_mod_freq, prob_l_mod_freq,
                prob_l_mod_scale, num_measurements)
prob_l_mod_scale_list = [1, 2, 4]#, 8, 16, 32, 64, 128, 256, 512, 1024]
for prob_l_mod_scale in prob_l_mod_scale_list:
    client.prob_l_mod_scale = prob_l_mod_scale
    client.sweep_num_tasks()

