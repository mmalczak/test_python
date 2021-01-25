# Client-server test application

This application allows to compare the performance of adaptive CPU controller
with other available governors:
* performance
* powersave
* ondemand

Overmore, it allows to compare the performance of adaptive CPU controller for
various parameters of the controller.

The application consists of 3 components:
* server - it runs on the machine the controller is installed on.
	It consists of two elements:
	* server control – it controls the behaviour of cpufreq module, reads
		data from the controller and measures the energy usage of the
		CPU
	* server workers – it is used to stress the machine
* client - it sends tasks to the server in order to stress the machine, control
	its behaviour and read measured data
* figures generator - it produces plots out of the data collected by the client

Data and plots folders are created in the top level directory when starting
the client application.

Server and client applications could run on the same machine, but in order to
collect more representative data, the server application should be the only
application that runs on the machine.

In order to start the server application, go to server directory and type:
```
python3 server.py IP
```
where IP is the IP of the machine the server runs on.

In order to start the client application, go to client directory and type:
```
python3 client_demo.py IP
```
where IP is the previously provided IP.

In order to generate figures, after collecting data by the client, go to
figures_generators directory and type:
```
python3 all_figures.py
```

# Configuration
client_demo.py script serves as an example how to configure the client.
The script is to be modified in order to fit the requirements.

Following parameters of the client are configurable:
* task
* num_tasks
* dm_freq
* plm_freq
* dm_scale
* plm_scale
* num_measurements
* increasing_freq
* square
They will be described in more detail in the section.

All the collected data serves to compare the energy usage of the processor and
the time taken to carry out the tasks.

There are 3 types of tasks used to stress the server (in parenthesis value
to be passed as "task" argument):
* fft calculation ("fft")
* random numbers generation ("random_gen")
* empty loop ("empty_loop")

For single measurement, the task is calculated multiple number of times,
configured by "num_tasks".

The length of the task varies and can be configured with the following parameters:
* plm_freq – problem length modulation frequency
* plm_scale – problem length modulation scale

The time delay with which the tasks are sent varies and can be configured
with the following parameters:
* dm_freq – delay modulation frequency
* dm_scale – delay modulation scale

If the time taken to execute a task is bigger then the delay, the following
task is sent straightaway. Otherwise the task is sent after the difference
between the delay and the time taken to execute the task.

"increasing_frequency" argument allows to modulate the signals with the square of the
sample instead of linearly.

"square" argument allows to modulate the signal as square instead of sinus.

Parameters *plm_freq*, *plm_scale*, *dm_freq*, *dm_scale*, *increasing_frequency*
and *square* are used to create signals of the length *num_tasks*.
Then, each of the tasks is configured to have the length and the delay based
on the value of the corresponding sample.

"num_measurements" sets the number of taken samples


There are 3 auxiliary methods that allow to perform tests:
* governors_compare – it is used to collect time-energy samples for all the
	available governors as well as for different values of setpoint(uc)
	of adaptive controller. Overmore, it outputs the data of signals for
	problem length modulation and delay modulation as well as the data
	collected from the kernel. Data from the kernel is read just for
	the adaptive controller, for the set-point equal to 60. This value
	is selected becasue it seems to maintain the CPU occupied all the time,
	giving enough space for sudden peaks in load of the CPU. Therefore, it
	seems to keep low power usage, without sacrifising quality of service.
* governors_compare_adaptive_param – it collects the same time-energy data as
	*governors_compare*, but calculates the mean value and iterates over
	selected parameter of the adaptive controller. The parameters of
	adaptive controller are the following:
	Am, Ao, lambda, Rd, sampling_rate, Sd, theta_limit_down, theta_limit_up, uc.
	Current values of all adaptive parameters could be checked by sysfs
	interface in: /sys/devices/system/cpu/cpufreq/adaptive. They can also
	be configured manually.
* sweep_param – in order to simplify performing measurements, this methods
	sweeps all the provided parameters and calls *governor_compare* and
	*governors_compare_adaptive_param* method.
