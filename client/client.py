import zmq
import pickle
import time
import numpy as np
import pandas as pd
import sys
import os

# plm - problem length modulation
# dm - delay modulation

passive_governors=[{'governor':'performance', 'uc':'NA', 'color':'silver', 'marker':'o'},
                   {'governor':'powersave', 'uc':'NA', 'color':'dimgray', 'marker':'o'}]
ondemand_governors=[{'governor':'ondemand', 'uc':'NA', 'color':'black', 'marker':'s'}]
adaptive_governors=[{'governor':'adaptive', 'uc':0, 'color':'darkblue', 'marker':'x'},
                    {'governor':'adaptive', 'uc':10, 'color':'brown', 'marker':'x'},
                    {'governor':'adaptive', 'uc':20, 'color':'peru', 'marker':'x'},
                    {'governor':'adaptive', 'uc':30, 'color':'gold', 'marker':'x'},
                    {'governor':'adaptive', 'uc':40, 'color':'lime', 'marker':'x'},
                    {'governor':'adaptive', 'uc':50, 'color':'aqua', 'marker':'x'},
                    {'governor':'adaptive', 'uc':60, 'color':'dodgerblue', 'marker':'x'},
                    {'governor':'adaptive', 'uc':70, 'color':'yellow', 'marker':'x'},
                    {'governor':'adaptive', 'uc':80, 'color':'darkviolet', 'marker':'x'},
                    {'governor':'adaptive', 'uc':90, 'color':'pink', 'marker':'x'},
                    {'governor':'adaptive', 'uc':100, 'color':'crimson', 'marker':'x'}]

sampling_rate_values = [10000, 20000, 40000, 80000, 160000, 320000, 640000];
default_sampling_rate = 10000

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

        self.project_location = os.path.realpath(os.getcwd()+'/../')
        self.create_folders()

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

    def create_folders(self):
        data_types = ['/plots/', '/data/']
        data_folders = ['mod_vs_tlm', 'adaptive_params', 'scatter']
        for d_type in data_types:
            path = self.project_location + d_type
            if not os.path.exists(path):
                os.mkdir(path)
            for folder in data_folders:
                path = self.project_location + d_type + folder
                if not os.path.exists(path):
                    os.mkdir(path)

    def init_arrays(self, export_modulation_data):
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

        if export_modulation_data:
            data = {'dm_sig':self.dm_sig, 'plm_sig':self.plm_sig}
            data = pd.DataFrame(data)
            path = self.project_location + '/data/mod_vs_tlm/'
            path = path + str(self) + ', modulation_signals.csv'
            data.to_csv(path, index=False)

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

    def time_energy_measurement(self, export_modulation_data):
        self.init_arrays(export_modulation_data)

        ### telemetry reset ###
        if export_modulation_data:
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
        if export_modulation_data:
            control_message = pickle.dumps({'task':'read_tlm',
                                            'args':None})
            self.control_socket.send(control_message)
            data = self.control_socket.recv()
            data = data.decode('utf-8')
            path = self.project_location + '/data/mod_vs_tlm/'
            path = path + str(self) + '.txt'
            f = open(path, 'w')
            f.write(data)
            f.close()
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
        control_message = pickle.dumps({'task':'set_adaptive_param',
                                        'args':[param_name, value]})
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

    def set_governor(self, governor, uc):
        print(governor)
        print("uc = " + str(uc))
        self.set_scaling_governor(governor)
        if uc is not 'NA':
            self.set_uc(uc)

    def inner_decorator(self, governor):
        if governor == 'adaptive' or governor == 'ondemand':
            self.set_sampling_rate(160000)
        if governor == 'adaptive':
            pass
            #self.set_adaptive_param('Sd', '1 0.5')
            #self.set_adaptive_param('Ao', '1 0.5 0')

    def get_governor_data(self, governor, uc):
        self.set_governor(governor, uc)
        self.inner_decorator(governor)

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

        gov_data = []
        for gov in passive_governors:
            gov_data.append(gov)
            temp = self.get_governor_data(gov['governor'], gov['uc'])
            gov_data[-1].update(temp)
        for gov in ondemand_governors:
            gov_data.append(gov)
            temp = self.get_governor_data(gov['governor'], gov['uc'])
            gov_data[-1].update(temp)
        for gov in adaptive_governors:
            gov_data.append(gov)
            temp = self.get_governor_data(gov['governor'], gov['uc'])
            gov_data[-1].update(temp)

        gov_data = pd.DataFrame(gov_data)

        path = self.project_location + '/data/scatter/'
        path = path + str(self)
        path = path + '.csv'
        gov_data.to_csv(path, index=False)

    def append_mean_data(self, energy_list, time_list):
        data_gov = self.time_energy_stats()
        energy = np.mean(data_gov['energy_list'])
        time = np.mean(data_gov['time_list'])
        energy_list.append(energy)
        time_list.append(time)

    def adaptive_param_line(self, governor, uc, adaptive_param,
                                adaptive_param_values):
        energy_list = []
        time_list = []

        self.set_governor(governor, uc)
        self.inner_decorator(governor)

        for adaptive_param_value in adaptive_param_values:
            if adaptive_param == 'sampling_rate':
                self.set_sampling_rate(adaptive_param_value)
            else:
                self.set_adaptive_param(adaptive_param, adaptive_param_value)
            self.append_mean_data(energy_list, time_list)
        return {'energy_list':energy_list, 'time_list':time_list,
                                    'adaptive_param_list':adaptive_param_values}

    def adaptive_param_point(self, governor, uc):
        energy_list = []
        time_list = []

        self.set_governor(governor, uc)
        self.inner_decorator(governor)

        self.append_mean_data(energy_list, time_list)
        return {'energy_list':energy_list, 'time_list':time_list,
                                    'adaptive_param_list':[]}


    def governors_compare_adaptive_param(self, adaptive_param,
                                        adaptive_param_values, default_value):
        data_types = ['/plots/', '/data/']
        for d_type in data_types:
            path = self.project_location + d_type + 'adaptive_params/' + adaptive_param
            if not os.path.exists(path):
                os.mkdir(path)

        ## warmup ##
        self.set_scaling_governor('ondemand')
        self.time_energy_stats()
        ## warmup ##

        gov_data = []
        for gov in passive_governors:
            gov_data.append(gov)
            temp = self.adaptive_param_point(gov['governor'], gov['uc'])
            gov_data[-1].update(temp)
        for gov in ondemand_governors:
            if adaptive_param == 'sampling_rate':
                gov_data.append(gov)
                temp = self.adaptive_param_line(gov['governor'], gov['uc'],
                                            adaptive_param, adaptive_param_values)
                gov_data[-1].update(temp)
            else:
                gov_data.append(gov)
                temp = self.adaptive_param_point(gov['governor'], gov['uc'])
                gov_data[-1].update(temp)
        for gov in adaptive_governors:
            gov_data.append(gov)
            temp = self.adaptive_param_line(gov['governor'], gov['uc'],
                                        adaptive_param, adaptive_param_values)
            gov_data[-1].update(temp)
        self.set_adaptive_param(adaptive_param, default_value)
        gov_data = pd.DataFrame(gov_data)
        path = self.project_location + '/data/adaptive_params/' + adaptive_param + '/'
        path = path + str(self)
        path = path + '.csv'
        gov_data.to_csv(path, index=False)

    def sweep_param(self, params, params_names_list, adaptive_params):
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
                for adaptive_param in adaptive_params:
                    self.governors_compare_adaptive_param(adaptive_param['name'],
                            adaptive_param['values'], adaptive_param['default'])
            else:
                self.sweep_param(params_copy, params_names_list, adaptive_params)


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

