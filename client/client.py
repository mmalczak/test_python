import zmq
import pickle
import time
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms

def confidence_ellipse(x, y, ax, n_std=3.0, facecolor='none', **kwargs):
    """
    Create a plot of the covariance confidence ellipse of *x* and *y*.

    Parameters
    ----------
    x, y : array-like, shape (n, )
        Input data.

    ax : matplotlib.axes.Axes
        The axes object to draw the ellipse into.

    n_std : float
        The number of standard deviations to determine the ellipse's radiuses.

    **kwargs
        Forwarded to `~matplotlib.patches.Ellipse`

    Returns
    -------
    matplotlib.patches.Ellipse
    """
    if x.size != y.size:
        raise ValueError("x and y must be the same size")

    cov = np.cov(x, y)
    pearson = cov[0, 1]/np.sqrt(cov[0, 0] * cov[1, 1])
    # Using a special case to obtain the eigenvalues of this
    # two-dimensionl dataset.
    ell_radius_x = np.sqrt(1 + pearson)
    ell_radius_y = np.sqrt(1 - pearson)
    ellipse = Ellipse((0, 0), width=ell_radius_x * 2, height=ell_radius_y * 2,
                      facecolor=facecolor, **kwargs)

    # Calculating the stdandard deviation of x from
    # the squareroot of the variance and multiplying
    # with the given number of standard deviations.
    scale_x = np.sqrt(cov[0, 0]) * n_std
    mean_x = np.mean(x)

    # calculating the stdandard deviation of y ...
    scale_y = np.sqrt(cov[1, 1]) * n_std
    mean_y = np.mean(y)

    transf1 = transforms.Affine2D().rotate_deg(45)
    transf2 = transforms.Affine2D().scale(scale_x, scale_y)
    transf3 = transforms.Affine2D().translate(mean_x, mean_y)


    ellipse.set_transform(transf1 + transf2 + transf3 + ax.transData)
    return ax.add_patch(ellipse)

def scatter_with_confidence_ellipse(data, ax_kwargs, color, marker, label):
    plt.scatter(data['energy_list'], data['time_list'], color=color, marker=marker, label=label)
    confidence_ellipse(data['energy_list'], data['time_list'], ax_kwargs, n_std=1, edgecolor=color)
    plt.xlabel('energy')
    plt.ylabel('time')

class Client():

    def __init__(self):
        self.context = zmq.Context()
        self.num_conn = 4
        self.sockets = []

        for i in range(0, self.num_conn):
            port = 5550 + i
            self.sockets.append(self.context.socket(zmq.DEALER))
            self.sockets[i].connect("tcp://10.10.10.1:"+str(port))

        self.control_socket = self.context.socket(zmq.DEALER)
        self.control_socket.connect("tcp://10.10.10.1:"+str(5540))

    def init_arrays(self, num_tasks, delay_mod_freq, prob_l_freq):
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

    def stress_server(self, task, num_tasks):
        time_diff=0
        for j in range(0, num_tasks):
            args = [1]+[0]*int(self.plm_sig_fft[j])
        #    args = int(self.plm_sig_empty_loop[j])
        #    args = int(self.plm_sig_random_gen[j])
            message = pickle.dumps({'task':task, 'args':args})
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

    def time_energy_measurement(self, task, num_tasks, delay_mod_freq, prob_l_freq):
        self.init_arrays(num_tasks, delay_mod_freq, prob_l_freq)

        ### Energy measurement start ###
        control_message = pickle.dumps({'task':'energy_measure_start', 'args':None})
        self.control_socket.send(control_message)
        data = self.control_socket.recv()
        ### Energy measurement start ###

        ### Time measurement start ###
        total_time_start = time.time()
        ### Time measurement start ###

        self.stress_server(task, num_tasks)

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

    def time_energy_stats(self, num_measurements, task, num_tasks, delay_mod_freq, prob_l_mod_freq):
        energy_list = []
        time_list = []
        for i in range(num_measurements):
            print(i)
            ret = self.time_energy_measurement(task, num_tasks, delay_mod_freq, prob_l_mod_freq)
            #print("Energy = {}".format(ret['energy']))
            #print("Total time = {}".format(ret['time']))
            energy_list.append(ret['energy'])
            time_list.append(ret['time'])

        return {'energy_list':energy_list, 'time_list':time_list}

    def set_scaling_governor(self, governor):
        control_message = pickle.dumps({'task':'set_scaling_governor', 'args':governor})
        self.control_socket.send(control_message)
        status = self.control_socket.recv()
        #print(status)

    def set_uc(self, uc):
        control_message = pickle.dumps({'task':'set_uc', 'args':uc})
        self.control_socket.send(control_message)
        status = self.control_socket.recv()
        #print(status)

    def get_governor_data(self, num_measurements, task, num_tasks, delay_mod_freq, prob_l_mod_freq, governor, uc):
        self.set_scaling_governor(governor)
        if uc is not 'NA':
            self.set_uc(uc)
        ret = self.time_energy_stats(num_measurements, task, num_tasks, delay_mod_freq, prob_l_mod_freq)
        ret['governor'] = [governor] * num_measurements
        ret['uc'] = [str(uc)] * num_measurements
        ret_pd = pd.DataFrame(ret)
        return ret_pd

    def governors_compare(self, num_measurements, task, num_tasks, delay_mod_freq, prob_l_mod_freq):
        ## warmup ##
        self.set_scaling_governor('ondemand')
        self.time_energy_stats(5, task, num_tasks, delay_mod_freq, prob_l_mod_freq)
        ## warmup ##


        sns.set()
        fig, ax_kwargs = plt.subplots()

        data  = pd.DataFrame()


        data_gov = self.get_governor_data(num_measurements, task, num_tasks, delay_mod_freq, prob_l_mod_freq, 'performance', 'NA')
        data = pd.concat([data, data_gov])
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, (0.7, 0.7, 0.7), 'o', 'performance')

        data_gov = self.get_governor_data(num_measurements, task, num_tasks, delay_mod_freq, prob_l_mod_freq, 'powersave', 'NA')
        data = pd.concat([data, data_gov])
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, (0.3, 0.3, 0.3), 'o', 'powersave')


        data_gov = self.get_governor_data(num_measurements, task, num_tasks, delay_mod_freq, prob_l_mod_freq, 'ondemand', 'NA')
        data = pd.concat([data, data_gov])
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, (0, 0, 0), 's', 'ondemand')

        data_gov = self.get_governor_data(num_measurements, task, num_tasks, delay_mod_freq, prob_l_mod_freq, 'adaptive', 1)
        data = pd.concat([data, data_gov])
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'b', 'x', 'adaptive, uc = 1')
        data_gov = self.get_governor_data(num_measurements, task, num_tasks, delay_mod_freq, prob_l_mod_freq, 'adaptive', 20)
        data = pd.concat([data, data_gov])
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'g', 'x', 'adaptive, uc = 20')
        data_gov = self.get_governor_data(num_measurements, task, num_tasks, delay_mod_freq, prob_l_mod_freq, 'adaptive', 40)
        data = pd.concat([data, data_gov])
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'r', 'x', 'adaptive, uc = 50')
        data_gov = self.get_governor_data(num_measurements, task, num_tasks, delay_mod_freq, prob_l_mod_freq, 'adaptive', 50)
        data = pd.concat([data, data_gov])
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'c', 'x', 'adaptive, uc = 60')
        data_gov = self.get_governor_data(num_measurements, task, num_tasks, delay_mod_freq, prob_l_mod_freq, 'adaptive', 60)
        data = pd.concat([data, data_gov])
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'm', 'x', 'adaptive, uc = 80')
        data_gov = self.get_governor_data(num_measurements, task, num_tasks, delay_mod_freq, prob_l_mod_freq, 'adaptive', 80)
        data = pd.concat([data, data_gov])
        scatter_with_confidence_ellipse(data_gov, ax_kwargs, 'y', 'x', 'adaptive, uc = 99')
        data_gov = self.get_governor_data(num_measurements, task, num_tasks, delay_mod_freq, prob_l_mod_freq, 'adaptive', 99)
        data = pd.concat([data, data_gov])


        #a = sns.relplot(x='energy_list', y='time_list', hue='uc', style='governor', data=data);

        #plt.scatter(data['energy_list'], data['time_list'], color='blue')
        #confidence_ellipse(data['energy_list'], data['time_list'], ax_kwargs, n_std=1, edgecolor='blue')
        #plt.scatter(data_gov['energy_list'], data_gov['time_list'])
        #confidence_ellipse(data_gov['energy_list'], data_gov['time_list'], ax_kwargs, alpha=0.5)
        plt.legend()

        plt.show()



# Available tasks with example arguments
# "fft" [1]+[0]*31
# "empty_loop" 500000
# "random_gen" 10
# "receive_array" [1, 2, 3, 4, 5]

client = Client()
task = "fft"
num_tasks = 6
delay_mod_freq = 6
prob_l_mod_freq = 3
num_measurements = 5
client.governors_compare(num_measurements, task, num_tasks, delay_mod_freq, prob_l_mod_freq)

