import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
from ast import literal_eval
from matplotlib.animation import FuncAnimation

adaptive_param = sys.argv[1]

project_location = os.path.realpath(os.getcwd()+'/../')
data_location = project_location + '/data/' + adaptive_param + '/'
plot_location = project_location + '/plots/' + adaptive_param + '/'

def plot_common(decorated_function):
    def wrapper(self, *args):
        plt.cla()
        decorated_function(self, *args)
        x_d = self.max_x - self.min_x
        y_d = self.max_y - self.min_y
        plt.ylim((self.min_y - 0.1 * y_d, self.max_y + 0.1 * y_d))
        plt.xlim((self.min_x - 0.1 * x_d, self.max_x + 0.1 * x_d))
        plt.xlabel('energy')
        plt.ylabel('time')
    return wrapper

class Container:
    def __init__(self):
        self.data = None
        self.l = 0
        self.max_x = 0
        self.min_x = 10e9
        self.max_y = 0
        self.min_y = 10e9

        sns.set()
        self.fig, self.ax_kwargs = plt.subplots()
        self.fig.set_size_inches(16, 12)

    def get_data(self, path):
        self.data = None
        self.l = 0
        self.max_x = 0
        self.min_x = 10e9
        self.max_y = 0
        self.min_y = 10e9

        self.data = pd.read_csv(path)
        self.data['adaptive_param_list'] = self.data['adaptive_param_list'].apply(literal_eval)
        self.data['energy_list'] = self.data['energy_list'].apply(literal_eval)
        self.data['time_list'] = self.data['time_list'].apply(literal_eval)

        ## adaptive_param_list could be empty for performance, powersave or
        ## ondemand governors
        i = 0
        while self.l == 0:
            self.l = len(self.data['adaptive_param_list'].loc[i])
            i = i + 1
        if(self.l == 0):
            print("Error")

        ## all adaptive params should be the same
        self.adaptive_param_list_common = self.data['adaptive_param_list'][i]

        for gov in self.data.iterrows():
            for value in gov[1]['energy_list']:
                if value > self.max_x:
                    self.max_x = value
                if value < self.min_x:
                    self.min_x = value
            for value in gov[1]['time_list']:
                if value > self.max_y:
                    self.max_y = value
                if value < self.min_y:
                    self.min_y = value


    def plot_single_param_value(self, i):
        energy_line = []
        time_line = []
        color = next(self.ax_kwargs._get_lines.prop_cycler)['color']
        for gov in self.data.iterrows():
            energy_list = gov[1]['energy_list']
            time_list = gov[1]['time_list']
            if gov[1]['governor'] == 'adaptive':
                energy_line.append(energy_list[i])
                time_line.append(time_list[i])
                if gov[1]['uc'] == 0 or gov[1]['uc'] == 100:
                    self.ax_kwargs.annotate(gov[1]['uc'],
                                            (energy_list[i],time_list[i]))
            if gov[1]['governor'] != 'adaptive':
                j = i
                if j >= len(energy_list):
                    j = 0
                if len(energy_list) == 1:
                    plt.scatter(energy_list[j], time_list[j], color='black')
                else:
                    plt.scatter(energy_list[j], time_list[j], color=color)
                self.ax_kwargs.annotate(gov[1]['governor'],
                                        (energy_list[j],time_list[j]))
        plt.plot(energy_line, time_line,
                    label=str(self.adaptive_param_list_common[i]), color=color)

    @plot_common
    def animate(self, i):
        self.plot_single_param_value(i)
        plt.text(self.min_x + 0.9 * (self.max_x - self.min_x),
                self.min_y + 0.9 * (self.max_y - self.min_y),
                    adaptive_param + '= ' + str(self.adaptive_param_list_common[i]))

    @plot_common
    def plot_gov_line(self):
        for gov in self.data.iterrows():
            energy_list = gov[1]['energy_list']
            time_list = gov[1]['time_list']
            plt.plot(energy_list, time_list,
                    color=gov[1]['color'], marker=gov[1]['marker'],
                    label=gov[1]['governor'] + ", uc=" + str(gov[1]['uc']))
            for i, txt in enumerate(gov[1]['adaptive_param_list']):
                self.ax_kwargs.annotate(txt, (energy_list[i], time_list[i]))
        plt.legend()

    @plot_common
    def plot_adapt_param_line(self):
        for i in range(self.l):
            self.plot_single_param_value(i)
        plt.legend()

    def produce_figures(self, *args):
        for csv_name in os.listdir(data_location):
            png_name = csv_name.replace('.csv', '.png')
            gif_name = csv_name.replace('.csv', '.gif')
            self.get_data(data_location + csv_name)
            if 'gov_line' in args:
                self.plot_gov_line()
                plt.savefig(plot_location + png_name.replace('.png',
                                                            '_gov_line.png'))
            if 'adapt_param_line' in args:
                self.plot_adapt_param_line()
                suffix = '_' + adaptive_param + '.png'
                plt.savefig(plot_location + png_name.replace('.png', suffix))
            if 'animation' in args:
                anim = FuncAnimation(self.fig, self.animate, frames=self.l,
                                     interval=1000)
                anim.save(plot_location + gif_name, writer='imagemagick')

cont = Container()
cont.produce_figures('animation', 'gov_line', 'adapt_param_line')
