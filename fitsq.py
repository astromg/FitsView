#!/usr/bin/env python3

import numpy as np
from scipy.signal import convolve2d
from scipy.ndimage.filters import maximum_filter

__version__ = "0.1.0"
__author__ = "mgorski"
__email__ = ""


class FQS:
    def __init__(self):
        self.image = None
        self.gain = None
        self.rn_noise = None
        self.stats = {}
    def basic_stats(self):
        self.stats["min"] = np.min(self.image)
        self.stats["max"] = np.max(self.image)
        self.stats["mean"] = np.mean(self.image)
        self.stats["median"] = np.median(self.image)
        self.stats["std"] = np.std(self.image)
        self.stats["q_sigma_lower"] = self.stats["median"] - np.quantile(self.image, 0.159)
        self.stats["q_sigma_upper"] = np.quantile(self.image, 0.841) - self.stats["median"]
        self.stats["q_sigma"] = (np.quantile(self.image, 0.841) - np.quantile(self.image, 0.159))/2.
        self.stats["sigma/q"] = self.stats["std"] / self.stats["q_sigma"]


    def find_stars(self, threshold=5., kernel_size=30, fwhm=10):

        coo = []
        adu = []
        threshold = float(threshold)

        fwhm= float(fwhm)
        kernel_size = int(kernel_size)
        kernel_sigma = float(fwhm) / 2.355
        kernel = gauss_kernel(kernel_size, kernel_sigma)


        maska1 = self.image > self.stats["median"] + threshold * self.stats["q_sigma"]
        data2 = convolve2d(self.image, kernel, mode='same')
        maska2 = (data2 == maximum_filter(data2, 3))
        maska = np.logical_and(maska1, maska2)
        coo = np.argwhere(maska)
        if len(coo) > 1:
            coo = coo
            x, y = zip(*coo)
            val = self.image[x, y]
            sorted_i = np.argsort(val.astype(float))[::-1]
            sorted_coo = coo[sorted_i]
            sorted_val = val[sorted_i]
            coo = sorted_coo
            adu = sorted_val

        self.stats["stars"] = {"coo":coo, "adu":adu}


def gauss_kernel(size, sigma):
    kernel = np.fromfunction(lambda x, y: (1 / (2 * np.pi * sigma ** 2)) * np.exp(
        -((x - (size - 1) / 2) ** 2 + (y - (size - 1) / 2) ** 2) / (2 * sigma ** 2)), (size, size))
    return kernel / np.sum(kernel)






    #
    # def fwhm(self, saturation=65000, radius=10, all_stars=True):
    #     radius = int(radius)
    #     self.fwhm_xarr = []
    #     self.fwhm_yarr = []
    #     self.fwhm_x = None
    #     self.fwhm_y = None
    #     for i, tmp in enumerate(self.coo):
    #         if all_stars:
    #             i_max = len(self.adu)
    #         else:
    #             i_max = 100
    #         d1 = d2 = d3 = d4 = None
    #         if self.adu[i] < int(saturation) and i < i_max:
    #             x, y = self.coo[i]
    #             max_adu = self.adu[i]
    #             half_adu = (max_adu - self.median) / 2.
    #
    #             if True:
    #                 line = self.image[x - radius:x + radius, y] - self.median - half_adu
    #                 line = self.image[x - radius + 1:x + 1, y] - self.median - half_adu
    #                 maska1, maska2 = line > 0, line < 0
    #                 pos, neg = line[maska1], line[maska2]
    #                 if len(pos) > 0 and len(neg) > 0:
    #                     lower, upper = max(neg), min(pos)
    #                     line = list(line)
    #                     lower_i, upper_i = line.index(lower), line.index(upper)
    #                     lower_adu, upper_adu = line[lower_i], line[upper_i]
    #                     d1 = radius - upper_i - numpy.abs(lower_adu) / (numpy.abs(lower_adu) + numpy.abs(upper_adu))
    #
    #                 line = self.image[x:x + radius, y] - self.median - half_adu
    #                 maska1, maska2 = line > 0, line < 0
    #                 pos, neg = line[maska1], line[maska2]
    #                 if len(pos) > 0 and len(neg) > 0:
    #                     lower, upper = max(neg), min(pos)
    #                     line = list(line)
    #                     lower_i, upper_i = line.index(lower), line.index(upper)
    #                     lower_adu, upper_adu = line[lower_i], line[upper_i]
    #                     d2 = upper_i + 1 - numpy.abs(lower_adu) / (numpy.abs(lower_adu) + numpy.abs(upper_adu))
    #
    #                 line = self.image[x, y - radius + 1:y + 1] - self.median - half_adu
    #                 maska1, maska2 = line > 0, line < 0
    #                 pos, neg = line[maska1], line[maska2]
    #                 if len(pos) > 0 and len(neg) > 0:
    #                     lower, upper = max(neg), min(pos)
    #                     line = list(line)
    #                     lower_i, upper_i = line.index(lower), line.index(upper)
    #                     lower_adu, upper_adu = line[lower_i], line[upper_i]
    #                     d3 = radius - upper_i - numpy.abs(lower_adu) / (numpy.abs(lower_adu) + numpy.abs(upper_adu))
    #
    #                 line = self.image[x, y:y + radius] - self.median - half_adu
    #                 maska1, maska2 = line > 0, line < 0
    #                 pos, neg = line[maska1], line[maska2]
    #                 if len(pos) > 0 and len(neg) > 0:
    #                     lower, upper = max(neg), min(pos)
    #                     line = list(line)
    #                     lower_i, upper_i = line.index(lower), line.index(upper)
    #                     lower_adu, upper_adu = line[lower_i], line[upper_i]
    #                     d4 = upper_i + 1 - numpy.abs(lower_adu) / (numpy.abs(lower_adu) + numpy.abs(upper_adu))
    #
    #         if d1 != None and d2 != None:
    #             dx = (d1 + d2)
    #         else:
    #             dx = 0
    #
    #         if d3 != None and d4 != None:
    #             dy = (d3 + d4)
    #         else:
    #             dy = 0
    #         self.fwhm_xarr.append(dx)
    #         self.fwhm_yarr.append(dy)
    #
    #     self.fwhm_xarr, self.fwhm_yarr = numpy.array(self.fwhm_xarr), numpy.array(self.fwhm_yarr)
    #
    #     maska = self.fwhm_xarr == 0
    #     fwhm_xarr = self.fwhm_xarr[~maska]
    #
    #     maska = self.fwhm_yarr == 0
    #     fwhm_yarr = self.fwhm_yarr[~maska]
    #
    #     if len(fwhm_xarr) > 2:
    #         self.fwhm_x = numpy.median(fwhm_xarr)
    #     if len(fwhm_yarr) > 2:
    #         self.fwhm_y = numpy.median(fwhm_yarr)
    #
    #     return self.fwhm_x, self.fwhm_y