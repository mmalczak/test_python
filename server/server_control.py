from subprocess import PIPE
from subprocess import run


class controller_class:
    def energy_measure_start(self, args):
        #        print("Energy measure start")
        run(["/bin/bash", "energy_measure_start.sh"])
        return b"Success"

    def energy_measure_stop(self, args):
        #        print("Energy measure stop")
        out = run(
            ["/bin/bash", "energy_measure_stop.sh"], stdout=PIPE, stderr=PIPE
        )
        energy = out.stdout
        return energy

    def set_scaling_governor(self, args):
        out = run(
            [
                "echo "
                + args
                + " > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor"
            ],
            shell=True,
        )
        if out.returncode == 0:
            return b"Success"
        else:
            return b"Error"

    def set_adaptive_param(self, args):
        out = run(
            [
                "echo "
                + str(args[1])
                + " > /sys/devices/system/cpu/cpufreq/adaptive/"
                + str(args[0])
            ],
            shell=True,
        )
        if out.returncode == 0:
            return b"Success"
        else:
            return b"Error"

    def set_uc(self, args):
        out = run(
            [
                "echo "
                + str(args)
                + " > /sys/devices/system/cpu/cpufreq/adaptive/uc"
            ],
            shell=True,
        )
        if out.returncode == 0:
            return b"Success"
        else:
            return b"Error"

    def set_sampling_rate(self, args):
        out = run(
            ["cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor"],
            shell=True,
            stdout=PIPE,
        )
        governor = out.stdout.decode("utf-8").rstrip()
        if governor == "adaptive" or governor == "ondemand":
            out = run(
                [
                    "echo "
                    + str(args)
                    + " > /sys/devices/system/cpu/cpufreq/"
                    + governor
                    + "/sampling_rate"
                ],
                shell=True,
                stdout=PIPE,
            )
            if out.returncode == 0:
                return b"Success"
            else:
                return b"Error"
        else:
            ret = (
                "Parameter sampling_rate is not available for "
                + governor
                + " governor"
            )
            return ret.encode("utf-8")

    def reset_tlm(self, args):
        out = run(
            ["sudo ../../telemetry/./tlm"],
            shell=True,
            stdout=PIPE,
            stderr=PIPE,
        )
        if out.returncode == 0:
            return b"Success"
        else:
            return b"Error"

    def read_tlm(self, args):
        out = run(
            ["sudo ../../telemetry/./tlm -f csv"],
            shell=True,
            stdout=PIPE,
            stderr=PIPE,
        )
        tlm_data = out.stdout
        return tlm_data
