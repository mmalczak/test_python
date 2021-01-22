import logging
import sys

from client import Client

logging.basicConfig(level=logging.INFO)
ip = sys.argv[1]

sampling_rate_values = [10000, 20000, 40000, 80000, 160000, 320000, 640000]
default_sampling_rate = 10000

task = "fft"
num_tasks = 1024
dm_freq = 0
plm_freq = 3
dm_scale = 1 / 50
plm_scale = 4096
num_measurements = 2
sampling_rate = 10000
increasing_freq = False
square = False

client = Client(
    ip,
    task,
    num_tasks,
    dm_freq,
    plm_freq,
    dm_scale,
    plm_scale,
    num_measurements,
    increasing_freq,
    square,
    default_sampling_rate,
)

client.governors_compare()
client.governors_compare_adaptive_param(
    "sampling_rate",
    sampling_rate_values,
    default_sampling_rate,
)

# client.sweep_param(
#  {"num_tasks": [4], "dm_freq": [2, 3], "plm_scale": [1, 2]},
#  [
#      {
#          "name": "sampling_rate",
#          "values": sampling_rate_values,
#          "default": default_sampling_rate,
#      }
#  ],
# )
