import zmq
import pickle
import time
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from confidence_ellipse import confidence_ellipse
from plot_kernel_data import plot_kernel_data
import sys


# plm - problem length modulation
# dm - delay modulation

def scatter_with_confidence_ellipse(data, ax_kwargs, color, marker, label):
    plt.scatter(data['energy_list'], data['time_list'], color=color,
                marker=marker, label=label)
    confidence_ellipse(data['energy_list'], data['time_list'], ax_kwargs,
                n_std=1, edgecolor=color)
    plt.xlabel('energy')
    plt.ylabel('time')

project_location = sys.argv[2]

class Client():

    def __init__(self, task, num_tasks, dm_freq, plm_freq, dm_scale, plm_scale,
                    num_measurements, increasing_freq, square):
        self.task = task
        self.num_tasks = num_tasks
        self.dm_freq = dm_freq
        self.plm_freq = plm_freq
        self.dm_scale = dm_scale
        self.plm_scale = plm_scale
        self.num_measurements = num_measurements
        self.increasing_freq = increasing_freq
        self.square = square

        self.context = zmq.Context()
        self.num_conn = 8
        self.sockets = []

        for i in range(0, self.num_conn):
            port = 5550 + i
            self.sockets.append(self.context.socket(zmq.DEALER))
            ip = sys.argv[1]
            self.sockets[i].connect("tcp://" + ip + ":"+str(port))

        self.control_socket = self.context.socket(zmq.DEALER)
        ip = sys.argv[1]
        self.control_socket.connect("tcp://" + ip + ":"+str(5540))

    def __str__(self):
        string = ""
        string = string + "task_{}".format(self.task)
        string = string + ",num_tasks_{}".format(self.num_tasks)
        string = string + ",dm_freq_{}".format(self.dm_freq)
        string = string + ",plm_freq_{}".format(self.plm_freq)
        string = string + ",dm_scale_{:.3f}".format(self.dm_scale)
        string = string + ",plm_scale_{}".format(self.plm_scale).zfill(8)
        string = string + ",num_measurements_{}".format(self.num_measurements)
        string = string + ",increasing_freq_{}".format(self.increasing_freq)
        string = string + ",square_{}".format(self.square)
        return string

    def init_arrays(self, modulation_plots):
        t = np.array(range(0, self.num_tasks))/self.num_tasks

        #delay modulation
        if self.dm_freq == 0:
            self.dm_sig = [self.dm_scale] * self.num_tasks
        else:
            if self.increasing_freq:
                phase = 2 * np.pi * self.dm_freq * t * t + np.pi / 2
            else:
                phase = 2 * np.pi * self.dm_freq * t + np.pi / 2
            self.dm_sig = (np.sin(phase) + 1) / 2 * self.dm_scale
        if self.square:
            self.dm_sig = [self.dm_scale if i > self.dm_scale / 2 else 0
                                                        for i in self.dm_sig]

        #problem length modulation
        if self.plm_freq == 0:
            self.plm_sig = [self.plm_scale] * self.num_tasks
        else:
            if self.increasing_freq:
                phase = 2 * np.pi * self.plm_freq * t * t - np.pi / 2
            else:
                phase = 2 * np.pi * self.plm_freq * t - np.pi / 2
            self.plm_sig = (np.sin(phase) + 1) / 2 * self.plm_scale
        if self.square:
            self.plm_sig = [self.plm_scale if i > self.plm_scale / 2 else 0
                                                        for i in self.plm_sig]

        if modulation_plots:
            #plt.ion()
            #plt.show()
            plt.subplot(2, 1, 1, title="Delay modulation signal")
            plt.plot(self.dm_sig)
            #plt.pause(0.1)
            plt.subplot(2, 1, 2, title="Problem length modulation signal")
            plt.plot(self.plm_sig)
            #plt.pause(0.1)
            #plt.show()
            figure = plt.gcf()
            figure.set_size_inches(16, 12)
            plt.savefig(project_location + 'test_python/plots/mod_vs_tlm/' +
                                str(self) + ', modulation_signals.png')
            plt.close()

    def stress_server(self):
        time_diff=0
        for j in range(0, self.num_tasks):
            args = [1]+[0]*int(self.plm_sig[j])
            message = pickle.dumps({'task':self.task, 'args':args})
            start = time.time()
            for i in range(0, self.num_conn):
                self.sockets[i].send(message)
            for i in range(0, self.num_conn):
                data = self.sockets[i].recv()

            time_diff = time.time() - start
            sleep_time = self.dm_sig[j] - time_diff
            if sleep_time > 0:
                time.sleep(sleep_time)

    def time_energy_measurement(self, modulation_plots):
        self.init_arrays(modulation_plots)

        ### telemetry reset ###
        if modulation_plots:
            control_message = pickle.dumps({'task':'reset_tlm',
                                            'args':None})
            self.control_socket.send(control_message)
            data = self.control_socket.recv()
        ### telemetry reset ###

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
        if energy < 0:
            return -1
        ### Energy measurement stop ###

        ### telemetry read ###
        if modulation_plots:
            control_message = pickle.dumps({'task':'read_tlm',
                                            'args':None})
            self.control_socket.send(control_message)
            data = self.control_socket.recv()
            plot_kernel_data(data, project_location, str(self))
        ### telemetry read ###

        return {'energy':energy, 'time':total_time}

    def time_energy_stats(self):
        energy_list = []
        time_list = []
        for i in range(self.num_measurements):
            print("sample idx = " + str(i))
            ret = self.time_energy_measurement(False)
            if ret == -1:
                continue
            energy_list.append(ret['energy'])
            time_list.append(ret['time'])

        return {'energy_list':energy_list, 'time_list':time_list}

    def set_scaling_governor(self, governor):
        control_message = pickle.dumps({'task':'set_scaling_governor',
                                        'args':governor})
        self.control_socket.send(control_message)
        status = self.control_socket.recv()

    def set_adaptive_param(self, param_name, value):
        control_message = pickle.dumps({'task':'set_adaptive_param', 'args':[param_name, value]})
        self.control_socket.send(control_message)
        status = self.control_socket.recv()

    def set_uc(self, uc):
        control_message = pickle.dumps({'task':'set_uc', 'args':uc})
        self.control_socket.send(control_message)
        status = self.control_socket.recv()

    def set_sampling_rate(self, sampling_rate):
        control_message = pickle.dumps({'task':'set_sampling_rate',
                                                        'args':sampling_rate})
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
        print("Problem length modulation scale = " + str(self.plm_scale))
        print("Number of tasks = " + str(self.num_tasks))
        self.set_scaling_governor('adaptive')
        self.set_uc(60)
        self.time_energy_measurement(True)
        ## warmup ##
        self.set_scaling_governor('ondemand')
        self.time_energy_stats()
        ## warmup ##

        sns.set()
        plt.figure(1)
        fig, ax_kwargs = plt.subplots()

        data_gov = self.get_governor_data('performance', 'NA')
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, (0.7, 0.7, 0.7), 'o', 'performance')
        data_gov = self.get_governor_data('powersave', 'NA')
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, (0.3, 0.3, 0.3), 'o', 'powersave')
        data_gov = self.get_governor_data('ondemand', 'NA')
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, (0, 0, 0), 's', 'ondemand')
        data_gov = self.get_governor_data('adaptive', 0)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'darkblue', 'x', 'adaptive, uc = 0')
        data_gov = self.get_governor_data('adaptive', 10)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'brown', 'x', 'adaptive, uc = 10')
        data_gov = self.get_governor_data('adaptive', 20)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'peru', 'x', 'adaptive, uc = 20')
        data_gov = self.get_governor_data('adaptive', 30)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'gold', 'x', 'adaptive, uc = 30')
        data_gov = self.get_governor_data('adaptive', 40)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'lime', 'x', 'adaptive, uc = 40')
        data_gov = self.get_governor_data('adaptive', 50)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'aqua', 'x', 'adaptive, uc = 50')
        data_gov = self.get_governor_data('adaptive', 60)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'dodgerblue', 'x', 'adaptive, uc = 60')
        data_gov = self.get_governor_data('adaptive', 70)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'yellow', 'x', 'adaptive, uc = 70')
        data_gov = self.get_governor_data('adaptive', 80)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'darkviolet', 'x', 'adaptive, uc = 80')
        data_gov = self.get_governor_data('adaptive', 90)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'pink', 'x', 'adaptive, uc = 90')
        data_gov = self.get_governor_data('adaptive', 100)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'crimson', 'x', 'adaptive, uc = 100')

        plt.legend()

#        plt.show()
        figure = plt.gcf()
        figure.set_size_inches(16, 12)
        path = project_location + 'test_python/plots/scatter/'

        path = path + str(self)

        path = path + '.png'
        plt.savefig(path)
        plt.close()

    def sampling_rate_compare(self, governor, uc):
        print("Problem length modulation scale = " + str(self.plm_scale))
        print("Number of tasks = " + str(self.num_tasks))
        ## warmup ##
        self.set_scaling_governor('ondemand')
        self.time_energy_stats()
        ## warmup ##

        sns.set()
        fig, ax_kwargs = plt.subplots()

        self.set_sampling_rate(10000)
        data_gov = self.get_governor_data(governor, uc)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'b', 'x', 'sampling_rate = 10000')
        self.set_sampling_rate(20000)
        data_gov = self.get_governor_data(governor, uc)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'g', 'x', 'sampling_rate = 20000')
        self.set_sampling_rate(40000)
        data_gov = self.get_governor_data(governor, uc)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'r', 'x', 'sampling_rate = 40000')
        self.set_sampling_rate(80000)
        data_gov = self.get_governor_data(governor, uc)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'c', 'x', 'sampling_rate = 80000')
        self.set_sampling_rate(160000)
        data_gov = self.get_governor_data(governor, uc)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'm', 'x', 'sampling_rate = 160000')
        self.set_sampling_rate(320000)
        data_gov = self.get_governor_data(governor, uc)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'lime', 'x', 'sampling_rate = 320000')
        self.set_sampling_rate(640000)
        data_gov = self.get_governor_data(governor, uc)
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'pink', 'x', 'sampling_rate = 640000')


        plt.legend()

#        plt.show()
        figure = plt.gcf()
        figure.set_size_inches(16, 12)
        path = project_location + 'test_python/plots/sampling_rate/'
        path = path + str(self)
        path = path + ',' + governor
        path = path + ',' + str(uc)
        path = path + '.png'
        plt.savefig(path)
        plt.close()

    def append_mean_data(self, governor, uc, energy_list, time_list):
        data_gov = self.get_governor_data(governor, uc)
        energy = np.mean(data_gov['energy_list'])
        time = np.mean(data_gov['time_list'])
        energy_list.append(energy)
        time_list.append(time)

    def sampling_rate_line(self, governor, uc, sampling_rate_values):
        energy_list = []
        time_list = []

        for sampling_rate in sampling_rate_values:
            self.set_sampling_rate(sampling_rate)
            self.append_mean_data(governor, uc, energy_list, time_list)
        return {'energy_list':energy_list, 'time_list':time_list}

    def sampling_rate_plot_line(self, governor, uc, color, marker,
                                ax_kwargs, sampling_rate_values):
        data_gov = self.sampling_rate_line(governor, uc, sampling_rate_values)
        plt.plot(data_gov['energy_list'], data_gov['time_list'],
                    color=color, marker=marker, label=governor + ", uc=" + str(uc))
        for i, txt in enumerate(sampling_rate_values):
            ax_kwargs.annotate(txt, (data_gov['energy_list'][i], data_gov['time_list'][i]))

    def governors_compare_sampling_rate(self, sampling_rate_values):
        ## warmup ##
        self.set_scaling_governor('ondemand')
        self.time_energy_stats()
        ## warmup ##

        sns.set()
        plt.figure(1)
        fig, ax_kwargs = plt.subplots()

        self.sampling_rate_plot_line('ondemand', 'NA', (0, 0, 0), 's', ax_kwargs, sampling_rate_values)
        self.sampling_rate_plot_line('adaptive', 0, 'darkblue', 'x', ax_kwargs, sampling_rate_values)
        self.sampling_rate_plot_line('adaptive', 10, 'brown', 'x', ax_kwargs, sampling_rate_values)
        self.sampling_rate_plot_line('adaptive', 20, 'peru', 'x', ax_kwargs, sampling_rate_values)
        self.sampling_rate_plot_line('adaptive', 30, 'gold', 'x', ax_kwargs, sampling_rate_values)
        self.sampling_rate_plot_line('adaptive', 40, 'lime', 'x', ax_kwargs, sampling_rate_values)
        self.sampling_rate_plot_line('adaptive', 50, 'aqua', 'x', ax_kwargs, sampling_rate_values)
        self.sampling_rate_plot_line('adaptive', 60, 'dodgerblue', 'x', ax_kwargs, sampling_rate_values)
        self.sampling_rate_plot_line('adaptive', 70, 'yellow', 'x', ax_kwargs, sampling_rate_values)
        self.sampling_rate_plot_line('adaptive', 80, 'darkviolet', 'x', ax_kwargs, sampling_rate_values)
        self.sampling_rate_plot_line('adaptive', 90, 'pink', 'x', ax_kwargs, sampling_rate_values)
        self.sampling_rate_plot_line('adaptive', 100, 'crimson', 'x', ax_kwargs, sampling_rate_values)

        plt.xlabel('energy')
        plt.ylabel('time')
        plt.legend()
        figure = plt.gcf()
        figure.set_size_inches(16, 12)
        path = project_location + 'test_python/plots/sampling_rate/'
        path = path + str(self)
        path = path + '.png'
        plt.savefig(path)
        plt.close()

    def sweep_param(self, params, params_names_list):
        if params_names_list is None:
            params_names_list = [*params]
            for params_name in params:
                params_values = params[params_name]
                setattr(self, params_name, params_values[0])
        params_copy = params.copy()
        params_name = next(iter(params_copy))
        params_values = params_copy[params_name]
        params_copy.pop(params_name)
        for params_value in params_values:
            setattr(self, params_name, params_value)
            if len(params_copy) == 0:
                self.governors_compare()
            else:
                self.sweep_param(params_copy, params_names_list)


# Available tasks with example arguments
# "fft" [1]+[0]*31
# "empty_loop" 500000
# "random_gen" 10
# "receive_array" [1, 2, 3, 4, 5]

task = "fft"
num_tasks = 128
dm_freq = 3
plm_freq = 0
dm_scale = 8 / 50
plm_scale = 512
num_measurements = 1
sampling_rate = 10000
increasing_freq = False
square = False

client = Client(task, num_tasks, dm_freq, plm_freq, dm_scale, plm_scale,
                num_measurements, increasing_freq, square)

#client.sweep_prob_l_and_num_tasks()
client.time_energy_measurement(True)
#client.sweep_param({'num_tasks':[32], 'dm_freq':[2, 3], 'plm_scale': [1, 2]}, None)
#client.sweep_param({'num_tasks':[1, 2], 'dm_freq':[1, 2, 3]}, None)

