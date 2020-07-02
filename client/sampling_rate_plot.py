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

sns.set()
fig, ax_kwargs = plt.subplots()
fig.set_size_inches(16, 12)


for gov in data.iterrows():
    plt.plot(gov[1]['energy_list'], gov[1]['time_list'],
            color=gov[1]['color'], marker=gov[1]['marker'],
            label=gov[1]['governor'] + ", uc=" + str(gov[1]['uc']))
    for i, txt in enumerate(gov[1]['sampling_rate_list']):
        ax_kwargs.annotate(txt, (gov[1]['energy_list'][i], gov[1]['time_list'][i]))
plt.xlabel('energy')
plt.ylabel('time')
plt.legend()


#l = len(data['sampling_rate_list'].loc[0])
#for i in range(l):
#    energy_line = []
#    time_line = []
#    for gov in data.iterrows():
#        if gov[1]['governor'] == 'adaptive':
#            energy_line.append(gov[1]['energy_list'][i])
#            time_line.append(gov[1]['time_list'][i])
#        if gov[1]['uc'] == 0 or gov[1]['uc'] == 100:
#            ax_kwargs.annotate(gov[1]['uc'], (gov[1]['energy_list'][i],gov[1]['time_list'][i]))
#
#        if gov[1]['governor'] == 'ondemand':
#            plt.scatter(gov[1]['energy_list'][i], gov[1]['time_list'][i])
#            ax_kwargs.annotate('ondemand', (gov[1]['energy_list'][i],gov[1]['time_list'][i]))
#    plt.plot(energy_line, time_line, label=str(gov[1]['sampling_rate_list'][i]))



plt.xlabel('energy')
plt.ylabel('time')
plt.legend()

path = plot_location
path = path + name
path = path + '.png'
plt.savefig(path)
plt.close()
