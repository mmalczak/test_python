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

def plot_common(decorated_function):
    def wrapper(self, *args):
        plt.cla()
        decorated_function(self, *args)
        plt.ylim((0.9*self.min_y,1.1*self.max_y))
        plt.xlim((0.9*self.min_x,1.1*self.max_x))
        plt.xlabel('energy')
        plt.ylabel('time')
    return wrapper

class Container:
    def __init__(self):
        self.data = None
        self.l = None
        self.max_x = 0
        self.min_x = 10e9
        self.max_y = 0
        self.min_y = 10e9

        sns.set()
        self.fig, self.ax_kwargs = plt.subplots()
        self.fig.set_size_inches(16, 12)

    def get_data(self, path):
        self.max_x = 0
        self.min_x = 10e9
        self.max_y = 0
        self.min_y = 10e9

        self.data = pd.read_csv(path)
        self.data['sampling_rate_list'] = self.data['sampling_rate_list'].apply(literal_eval)
        self.data['energy_list'] = self.data['energy_list'].apply(literal_eval)
        self.data['time_list'] = self.data['time_list'].apply(literal_eval)

        self.l = len(self.data['sampling_rate_list'].loc[0])

        for i in range(self.l):
            for gov in self.data.iterrows():
                if gov[1]['energy_list'][i] > self.max_x:
                    self.max_x = gov[1]['energy_list'][i]
                if gov[1]['energy_list'][i] < self.min_x:
                    self.min_x = gov[1]['energy_list'][i]
                if gov[1]['time_list'][i] > self.max_y:
                    self.max_y = gov[1]['time_list'][i]
                if gov[1]['time_list'][i] < self.min_y:
                    self.min_y = gov[1]['time_list'][i]

    @plot_common
    def animate(self, i):
        energy_line = []
        time_line = []
        for gov in self.data.iterrows():
            if gov[1]['governor'] == 'adaptive':
                energy_line.append(gov[1]['energy_list'][i])
                time_line.append(gov[1]['time_list'][i])
            if gov[1]['uc'] == 0 or gov[1]['uc'] == 100:
                self.ax_kwargs.annotate(gov[1]['uc'],
                                (gov[1]['energy_list'][i],gov[1]['time_list'][i]))
            if gov[1]['governor'] == 'ondemand':
                plt.scatter(gov[1]['energy_list'][i], gov[1]['time_list'][i])
                self.ax_kwargs.annotate('ondemand',
                                (gov[1]['energy_list'][i],gov[1]['time_list'][i]))

        plt.plot(energy_line, time_line, label=str(gov[1]['sampling_rate_list'][i]))
        plt.text(0.9*self.max_x, self.max_y,
                    'sampling rate = ' + str(gov[1]['sampling_rate_list'][i]))

    @plot_common
    def plot_gov_line(self):
        for gov in self.data.iterrows():
            plt.plot(gov[1]['energy_list'], gov[1]['time_list'],
                    color=gov[1]['color'], marker=gov[1]['marker'],
                    label=gov[1]['governor'] + ", uc=" + str(gov[1]['uc']))
            for i, txt in enumerate(gov[1]['sampling_rate_list']):
                self.ax_kwargs.annotate(txt, (gov[1]['energy_list'][i], gov[1]['time_list'][i]))
        plt.legend()

    @plot_common
    def plot_samp_rate_line(self):
        for i in range(self.l):
            energy_line = []
            time_line = []
            for gov in self.data.iterrows():
                if gov[1]['governor'] == 'adaptive':
                    energy_line.append(gov[1]['energy_list'][i])
                    time_line.append(gov[1]['time_list'][i])
                if gov[1]['uc'] == 0 or gov[1]['uc'] == 100:
                    self.ax_kwargs.annotate(gov[1]['uc'], (gov[1]['energy_list'][i],gov[1]['time_list'][i]))

                if gov[1]['governor'] == 'ondemand':
                    plt.scatter(gov[1]['energy_list'][i], gov[1]['time_list'][i])
                    self.ax_kwargs.annotate('ondemand', (gov[1]['energy_list'][i],gov[1]['time_list'][i]))
            plt.plot(energy_line, time_line, label=str(gov[1]['sampling_rate_list'][i]))
        plt.legend()

    def produce_figures(self, *args):
        for csv_name in os.listdir(data_location):
            png_name = csv_name.replace('.csv', '.png')
            gif_name = csv_name.replace('.csv', '.gif')
            cont.get_data(data_location + csv_name)
            if 'gov_line' in args:
                self.plot_gov_line()
                plt.savefig(plot_location + png_name.replace('.png', '_gov_line.png'))
            if 'samp_rate_line' in args:
                self.plot_samp_rate_line()
                plt.savefig(plot_location + png_name.replace('.png', '_samp_rate_line.png'))
            if 'animation' in args:
                anim = FuncAnimation(cont.fig, cont.animate, frames=cont.l, interval=1000)
                anim.save(plot_location + gif_name, writer='imagemagick')

cont = Container()
cont.produce_figures('animation', 'gov_line', 'samp_rate_line')
