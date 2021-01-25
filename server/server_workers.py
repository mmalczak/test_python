import numpy as np


class worker_class:
    def fft(self, data):
        data = np.fft.fft(data)
        return b"Success"

    def empty_loop(self, length):
        for i in range(0, length):
            pass
        return b"Success"

    def random_gen(self, length):
        r = np.random.rand(length)
        return b"Success"

    def receive_array(self, array):
        return b"Success"
