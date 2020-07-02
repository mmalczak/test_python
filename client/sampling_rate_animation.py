import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os
from ast import literal_eval
from matplotlib.animation import FuncAnimation

project_location = os.path.realpath(os.getcwd()+'/../')
data_location = project_location + '/data/sampling_rate/'
plot_location = project_location + '/plots/sampling_rate/'


name = 'task_fft,num_tasks_2,dm_freq_1,plm_freq_1,dm_scale_0.000,plm_scale_65536,num_measurements_2,increasing_freq_False,square_False_governors_compare'
data = pd.read_csv(data_location + name + '.csv')
data['sampling_rate_list'] = data['sampling_rate_list'].apply(literal_eval)
data['energy_list'] = data['energy_list'].apply(literal_eval)
data['time_list'] = data['time_list'].apply(literal_eval)


l = len(data['sampling_rate_list'].loc[0])

max_x = 0
min_x = 10e9
max_y = 0
min_y = 10e9
for i in range(l):
    for gov in data.iterrows():
        if gov[1]['energy_list'][i] > max_x:
            max_x = gov[1]['energy_list'][i]
        if gov[1]['energy_list'][i] < min_x:
            min_x = gov[1]['energy_list'][i]
        if gov[1]['time_list'][i] > max_y:
            max_y = gov[1]['time_list'][i]
        if gov[1]['time_list'][i] < min_y:
            min_y = gov[1]['time_list'][i]

def animate(i):
    plt.cla()
    energy_line = []
    time_line = []
    for gov in data.iterrows():
        if gov[1]['governor'] == 'adaptive':
            energy_line.append(gov[1]['energy_list'][i])
            time_line.append(gov[1]['time_list'][i])
        if gov[1]['uc'] == 0 or gov[1]['uc'] == 100:
            ax_kwargs.annotate(gov[1]['uc'],
                            (gov[1]['energy_list'][i],gov[1]['time_list'][i]))
        if gov[1]['governor'] == 'ondemand':
            plt.scatter(gov[1]['energy_list'][i], gov[1]['time_list'][i])
            ax_kwargs.annotate('ondemand',
                            (gov[1]['energy_list'][i],gov[1]['time_list'][i]))

    plt.plot(energy_line, time_line, label=str(gov[1]['sampling_rate_list'][i]))
    plt.ylim((0.9*min_y,1.1*max_y))
    plt.xlim((0.9*min_x,1.1*max_x))
    plt.xlabel('energy')
    plt.ylabel('time')
    plt.text(0.9*max_x, max_y,
                'sampling rate = ' + str(gov[1]['sampling_rate_list'][i]))


sns.set()
fig, ax_kwargs = plt.subplots()
fig.set_size_inches(16, 12)

anim = FuncAnimation(fig, animate, frames=l, interval=1000)

path = plot_location
path = path + name
anim.save(path + '.gif', writer='imagemagick')
