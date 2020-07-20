import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from ast import literal_eval
from confidence_ellipse import confidence_ellipse

project_location = os.path.realpath(os.getcwd()+'/../')
data_location = project_location + '/data/scatter/'
plot_location = project_location + '/plots/scatter/'

def plot_common(decorated_function):
    def wrapper(self, *args):
        #plt.cla()
        decorated_function(self, *args)
        plt.legend()
        plt.xlabel('energy')
        plt.ylabel('time')
    return wrapper

class Container:
    def __init__(self):
        self.data = None

        sns.set()
        self.fig, self.ax_kwargs = plt.subplots()
        self.fig.set_size_inches(16, 12)

    def get_data(self, path):
        self.data = None

        self.data = pd.read_csv(path)
        self.data['energy_list'] = self.data['energy_list'].apply(literal_eval)
        self.data['time_list'] = self.data['time_list'].apply(literal_eval)

    def scatter_with_confidence_ellipse(self, energy_list, time_list, color, marker, label):
        plt.scatter(energy_list, time_list, color=color, marker=marker, label=label)
        confidence_ellipse(energy_list, time_list, self.ax_kwargs, n_std=1, edgecolor=color)
        plt.xlabel('energy')
        plt.ylabel('time')


    @plot_common
    def scatter(self):
        for gov in self.data.iterrows():
            energy_list = gov[1]['energy_list']
            time_list = gov[1]['time_list']
            self.scatter_with_confidence_ellipse(energy_list, time_list,
                    gov[1]['color'], gov[1]['marker'], gov[1]['governor'])

    def produce_figures(self, *args):
        for csv_name in os.listdir(data_location):
            png_name = csv_name.replace('.csv', '.png')
            gif_name = csv_name.replace('.csv', '.gif')
            self.get_data(data_location + csv_name)
            self.scatter()
            plt.savefig(plot_location + png_name)

cont = Container()
cont.produce_figures()