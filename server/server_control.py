import zmq
import pickle
import numpy as np
from subprocess import run
from subprocess import PIPE

class controller_class():

    def energy_measure_start(self, args):
#        print("Energy measure start")
        run(["/bin/bash", "energy_measure_start.sh"])
        return b"Success"

    def energy_measure_stop(self, args):
#        print("Energy measure stop")
        out = run(["/bin/bash", "energy_measure_stop.sh"], stdout=PIPE,
                                                                stderr=PIPE)
        energy = out.stdout
        return energy

    def set_scaling_governor(self, args):
        out = run(["echo " + args +
            " > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor"],
            shell=True)
        if out.returncode is 0:
            return b"Success"
        else:
            return b"Error"

    def set_uc(self, args):
        out = run(["echo " + str(args) +
            " > /sys/devices/system/cpu/cpufreq/adaptive/uc"],
            shell=True)
        if out.returncode is 0:
            return b"Success"
        else:
            return b"Error"



context = zmq.Context()
socket = context.socket(zmq.ROUTER)
port = 5540
socket.bind("tcp://10.10.10.1:"+str(port))
while True:
    [identity, message] = socket.recv_multipart()
    message = pickle.loads(message)
    ret = getattr(controller_class(), message['task'])(message['args'])
    socket.send_multipart([identity, ret])


