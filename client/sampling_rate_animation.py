import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os
from ast import literal_eval

project_location = os.path.realpath(os.getcwd()+'/../')
data_location = project_location + '/data/sampling_rate/'
plot_location = project_location + '/plots/sampling_rate/'


name = 'task_fft,num_tasks_2,dm_freq_1,plm_freq_1,dm_scale_0.000,plm_scale_65536,num_measurements_2,increasing_freq_False,square_False'
data = pd.read_csv(data_location + name + '.csv')
data['sampling_rate_list'] = data['sampling_rate_list'].apply(literal_eval)
data['energy_list'] = data['energy_list'].apply(literal_eval)
data['time_list'] = data['time_list'].apply(literal_eval)

sns.set()
plt.figure(1)
fig, ax_kwargs = plt.subplots()

for gov in data.iterrows():
    plt.plot(gov[1]['energy_list'], gov[1]['time_list'],
            color=gov[1]['color'], marker=gov[1]['marker'],
            label=gov[1]['governor'] + ", uc=" + str(gov[1]['uc']))
    for i, txt in enumerate(gov[1]['sampling_rate_list']):
        ax_kwargs.annotate(txt, (gov[1]['energy_list'][i], gov[1]['time_list'][i]))


plt.xlabel('energy')
plt.ylabel('time')
plt.legend()
#figure = plt.gcf()
#figure.set_size_inches(16, 12)
#path = plot_location
#path = path + name
#path = path + '.png'
#plt.savefig(path)
#plt.close()
plt.show()

