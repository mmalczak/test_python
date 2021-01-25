import matplotlib.pyplot as plt
import numpy as np
import scipy.signal as dsp


def get_array(x):
    x = x.replace("[", "")
    x = x.replace("]", "")
    x = x.split(",")
    x = [float(el) for el in x]
    return x


def plot_kernel_data(data, project_location, params_str):
    x_beg = 00
    x_end = 100

    time = []
    load_est = []
    load = []
    uc = []
    freq = []
    freq_next = []
    R = []
    S = []
    T = []
    D = []
    P = []
    phi_P_phi = []
    theta = []
    stop = 1
    for line in data.splitlines():
        line_split = line.split(";")
        time.append(float(line_split[0]) + float(line_split[1]) / 1000000000)
        load.append(float(line_split[3]))
        load_est.append(float(line_split[4]))
        uc.append(float(line_split[5]))
        freq.append(float(line_split[6]))
        freq_next.append(float(line_split[7]))
        theta.append(get_array(line_split[8]))
        R.append(get_array(line_split[9]))
        S.append(get_array(line_split[10]))
        T.append(get_array(line_split[11]))
        D.append(get_array(line_split[12]))
        P.append(get_array(line_split[13]))
        phi_P_phi.append(get_array(line_split[14]))

    a = np.array([1])
    l = 1
    b = np.ones(l, dtype=float) / l
    a.astype(float)
    load_est = dsp.lfilter(b, a, load_est)
    load = dsp.lfilter(b, a, load)

    N = len(time)
    x_beg = int(N * x_beg / 100)
    x_end = int(N * x_end / 100)

    N_subplot = 6

    # plt.figure(1)
    sp = plt.subplot(N_subplot, 1, 1)
    sp.set_title("Output")
    axes = plt.gca()
    axes.set_ylim([0, 200])
    plt.plot(time[x_beg:x_end], load[x_beg:x_end], label="y")
    # plt.plot(time[x_beg:x_end], load_est[x_beg:x_end], label='y_est');
    plt.plot(time[x_beg:x_end], uc[x_beg:x_end], label="uc")
    plt.grid()
    plt.legend(loc="upper left")

    sp = plt.subplot(N_subplot, 1, 2)
    sp.set_title("Input scaled")
    axes = plt.gca()
    axes.set_ylim([0, 5000000])
    plt.plot(time[x_beg:x_end], freq_next[x_beg:x_end], label="v")
    plt.plot(time[x_beg:x_end], freq[x_beg:x_end], label="u")
    plt.grid()
    plt.legend(loc="upper left")

    sp = plt.subplot(N_subplot, 1, 3)
    sp.set_title("Estimated parameters")
    plt.plot(time[x_beg:x_end], theta[x_beg:x_end])
    plt.grid()
    leg = []
    for i in range(len(theta[0])):
        leg.append("theta[" + str(i) + "]")
    plt.legend(leg, loc="upper left")

    sp = plt.subplot(N_subplot, 1, 4)
    sp.set_title("Controller")
    axes = plt.gca()
    axes.set_ylim([-10, 10])
    plt.plot(time[x_beg:x_end], R[x_beg:x_end])
    plt.plot(time[x_beg:x_end], S[x_beg:x_end])
    plt.plot(time[x_beg:x_end], T[x_beg:x_end])
    leg = []
    for i in range(len(R[0])):
        leg.append("R[" + str(i) + "]")
    for i in range(len(S[0])):
        leg.append("S[" + str(i) + "]")
    for i in range(len(T[0])):
        leg.append("T[" + str(i) + "]")
    plt.legend(leg, loc="upper left")

    sp = plt.subplot(N_subplot, 1, 5)
    sp.set_title("Controller")
    axes = plt.gca()
    axes.set_ylim([-10, 10])
    plt.plot(time[x_beg:x_end], D[x_beg:x_end])
    leg = []
    for i in range(len(D[0])):
        leg.append("D[" + str(i) + "]")
    plt.legend(leg, loc="upper left")

    sp = plt.subplot(N_subplot, 1, 6)
    sp.set_title("phi_P_phi")
    axes = plt.gca()
    plt.plot(time[x_beg:x_end], phi_P_phi[x_beg:x_end])
    plt.hlines(1000, time[x_beg], time[x_end - 1])

    plt.grid()
    plt.savefig(
        project_location
        + "/plots/mod_vs_tlm/"
        + params_str
        + ", tlm_data.png"
    )

    plt.cla()
    plt.clf()
    sp = plt.subplot()
    axes = plt.gca()
    axes.set_xlim([-5, 5])
    axes.set_ylim([-2.5, 2.5])
    sp.set_title("Model poles and zeros")
    zeros_re = []
    zeros_im = []
    poles_re = []
    poles_im = []
    # theta = theta[0:1]
    for idx, theta_el in enumerate(theta):
        A = [1] + theta_el[0:2]
        B = theta_el[2:]
        z = np.roots(B)
        p = np.roots(A)
        zeros_re.append(z.real)
        zeros_im.append(z.imag)
        poles_re.append(p.real)
        poles_im.append(p.imag)
    circle1 = plt.Circle((0, 0), 1, fill=False, color="black")
    axes.add_artist(circle1)
    plt.scatter(poles_re, poles_im, marker="x", color="r")
    plt.scatter(zeros_re, zeros_im, marker="o", color="none", edgecolor="b")
    plt.grid(True)
    plt.savefig(
        project_location
        + "/plots/mod_vs_tlm/"
        + params_str
        + ", poles_zeros.png"
    )
