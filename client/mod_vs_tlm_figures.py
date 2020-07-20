import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from plot_kernel_data import plot_kernel_data

project_location = os.path.realpath(os.getcwd()+'/../')
data_location = project_location + '/data/mod_vs_tlm/'
plot_location = project_location + '/plots/mod_vs_tlm/'

def plot_common(decorated_function):
    def wrapper(self, *args):
        decorated_function(self, *args)
        plt.legend()
    return wrapper

class Container:
    def __init__(self):
        self.mod_data = None
        self.tlm_data = None

        sns.set()
        self.fig, self.ax_kwargs = plt.subplots()
        self.fig.set_size_inches(16, 12)

    def get_data(self, path):
        if path.endswith('modulation_signals.csv'):
            self.mod_data = pd.read_csv(path)
        else:
            f = open(path, 'r')
            self.tlm_data = f.read()
            f.close()

    @plot_common
    def mod_plot(self):
        plt.subplot(2, 1, 1, title="Delay modulation signal")
        plt.plot(self.mod_data['dm_sig'])
        plt.subplot(2, 1, 2, title="Problem length modulation signal")
        plt.plot(self.mod_data['plm_sig'])

    def produce_figures(self, *args):
        for name in os.listdir(data_location):
            png_name = None
            self.get_data(data_location + name)
            if name.endswith('modulation_signals.csv'):
                png_name = name.replace('.csv', '.png')
                self.mod_plot()
                plt.savefig(plot_location + png_name)
            else:
                name = name.replace('.txt', '')
                plot_kernel_data(self.tlm_data, project_location, name)


cont = Container()
cont.produce_figures()
