#!/usr/bin/env python3

import numpy as np
from scipy.signal import convolve2d
from scipy.ndimage.filters import maximum_filter

from scipy.ndimage import convolve
from scipy.ndimage import generate_binary_structure, label
from scipy.ndimage import sum as ndimage_sum

from astropy.stats import sigma_clipped_stats
from astropy.stats import mad_std

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


    def fwhm(self, stats, saturation=65000, radius=10, all_stars=True):
        radius = int(radius)

        self.stats = stats
        coo = np.array(self.stats["stars"]["coo"])
        adu = np.array(self.stats["stars"]["adu"])
        fwhm_xarr = []
        fwhm_yarr = []
        fwhm_x = None
        fwhm_y = None
        for i, tmp in enumerate(coo):
            if all_stars:
                i_max = len(adu)
            else:
                i_max = 100
            d1 = d2 = d3 = d4 = None
            if adu[i] < int(saturation) and i < i_max:
                x, y = coo[i]
                max_adu = adu[i]
                half_adu = (max_adu - self.stats["median"]) / 2.

                if True:
                    line = self.image[x - radius + 1:x + 1, y] - self.stats["median"] - half_adu
                    maska1, maska2 = line > 0, line < 0
                    pos, neg = line[maska1], line[maska2]
                    if len(pos) > 0 and len(neg) > 0:
                        lower, upper = max(neg), min(pos)
                        line = list(line)
                        lower_i, upper_i = line.index(lower), line.index(upper)
                        lower_adu, upper_adu = line[lower_i], line[upper_i]
                        d1 = radius - upper_i - np.abs(lower_adu) / (np.abs(lower_adu) + np.abs(upper_adu))

                    line = self.image[x:x + radius, y] - self.stats["median"] - half_adu
                    maska1, maska2 = line > 0, line < 0
                    pos, neg = line[maska1], line[maska2]
                    if len(pos) > 0 and len(neg) > 0:
                        lower, upper = max(neg), min(pos)
                        line = list(line)
                        lower_i, upper_i = line.index(lower), line.index(upper)
                        lower_adu, upper_adu = line[lower_i], line[upper_i]
                        d2 = upper_i + 1 - np.abs(lower_adu) / (np.abs(lower_adu) + np.abs(upper_adu))

                    line = self.image[x, y - radius + 1:y + 1] - self.stats["median"] - half_adu
                    maska1, maska2 = line > 0, line < 0
                    pos, neg = line[maska1], line[maska2]
                    if len(pos) > 0 and len(neg) > 0:
                        lower, upper = max(neg), min(pos)
                        line = list(line)
                        lower_i, upper_i = line.index(lower), line.index(upper)
                        lower_adu, upper_adu = line[lower_i], line[upper_i]
                        d3 = radius - upper_i - np.abs(lower_adu) / (np.abs(lower_adu) + np.abs(upper_adu))

                    line = self.image[x, y:y + radius] - self.stats["median"] - half_adu
                    maska1, maska2 = line > 0, line < 0
                    pos, neg = line[maska1], line[maska2]
                    if len(pos) > 0 and len(neg) > 0:
                        lower, upper = max(neg), min(pos)
                        line = list(line)
                        lower_i, upper_i = line.index(lower), line.index(upper)
                        lower_adu, upper_adu = line[lower_i], line[upper_i]
                        d4 = upper_i + 1 - np.abs(lower_adu) / (np.abs(lower_adu) + np.abs(upper_adu))

            if d1 != None and d2 != None:
                dx = (d1 + d2)
            else:
                dx = 0

            if d3 != None and d4 != None:
                dy = (d3 + d4)
            else:
                dy = 0
            fwhm_xarr.append(dx)
            fwhm_yarr.append(dy)

        fwhm_xarr =  np.array(fwhm_xarr)
        fwhm_yarr =  np.array(fwhm_yarr)
        self.stats["stars"]["fwhm_xarr"] = fwhm_yarr
        self.stats["stars"]["fwhm_yarr"] = fwhm_yarr

        maska = fwhm_xarr == 0
        fwhm_xarr = fwhm_xarr[~maska]


        maska = fwhm_yarr == 0
        fwhm_yarr = fwhm_yarr[~maska]

        if len(fwhm_xarr) > 2:
            fwhm_x = np.median(fwhm_xarr)
        if len(fwhm_yarr) > 2:
            fwhm_y = np.median(fwhm_yarr)

        self.stats["fwhm_x"] = fwhm_x
        self.stats["fwhm_y"] = fwhm_y



    def sky_gradient(self,image,n_segments=10):
        image = image
        segments = make_segments(image, n_segments=n_segments)

        x = []
        y = []
        back = []
        back_mad = []
        for s in segments:
            x_tmp = (s["x"][0] + s["x"][1]) // 2
            y_tmp = (s["y"][0] + s["y"][1]) // 2
            x.append(x_tmp)
            y.append(y_tmp)
            back.append(np.median(s["subframe"]))
            back_mad.append(mad_std(s["subframe"]))

        x = np.array(x)
        y = np.array(y)
        back = np.array(back)

        A = np.vstack([np.ones_like(x), x, y, x ** 2, x * y, y ** 2]).T
        coeff, *_ = np.linalg.lstsq(A, back, rcond=None)

        x0 = min(x)
        y0 = min(y)
        xk = max(x)
        yk = max(y)

        le = []
        re = []
        ue = []
        de = []

        bk = []

        for xi, yi in zip(x, y):
            bk.append(polysurf(xi, yi, coeff))
            le.append(polysurf(x0, yi, coeff))
            re.append(polysurf(xk, yi, coeff))
            ue.append(polysurf(xi, yk, coeff))
            de.append(polysurf(xi, y0, coeff))

        max_amplitude = max(bk) - min(bk)
        max(le) - min(re)
        frame_gradient = max(max((max(le) - min(re)), (max(re) - min(le))),
                             max((max(ue) - min(de)), (max(de) - min(ue))))

        self.max_amplitude = max_amplitude
        self.frame_gradient = frame_gradient
        self.sky_surface_coeff = coeff
        self.sky_surface_bk = bk
        self.sky_surface_x = x
        self.sky_surface_y = y



    def line_detection(self,image,k1=3,k2=7,th1=3,th2=3):
        image = image


        kernel_l, kernel_r = line_detection_kernel(k1)  # tu sie zmienia
        result_l = convolve(image, kernel_l)
        maska_1l = result_l > np.median(result_l) + th1 * mad_std(result_l)
        result_r = convolve(image, kernel_r)
        maska_1r = result_r > np.median(result_r) + th1 * mad_std(result_r)
        #maska1 = maska_l ^ maska_r

        kernel_l, kernel_r = line_detection_kernel(k2)  # tu sie zmienia
        result_l = convolve(image, kernel_l)
        maska_2l = result_l > np.median(result_l) + th2 * mad_std(result_r)
        result_r = convolve(image, kernel_r)
        maska_2r = result_r > np.median(result_r) + th2 * mad_std(result_r)
        #maska2 = maska_l ^ maska_r

        #maska = maska1 & maska2
        maska = (maska_1l & maska_2l) ^ (maska_1r & maska_2r)

        return maska



        # znajdowanie grup

        # conection_kernel = generate_binary_structure(2, 2)  # kernel grupowania
        # labeled_array, num_features = label(maska, structure=conection_kernel)
        # sizes = ndimage_sum(maska, labeled_array, range(1, num_features + 1))
        #
        # maska0 = np.zeros_like(image, dtype=bool)
        #
        # for i in range(1, num_features + 1):
        #     tmp = np.argwhere(labeled_array == i)
        #     pixels = []
        #     values = []
        #     if len(tmp) > 10:
        #         for pk in tmp:
        #             pixels.append(pk)
        #             values.append(image[pk[1], pk[0]])
        #         pixels = np.array(pixels)
        #         values = np.array(values)
        #         mask = values > 0
        #         pixels = pixels[mask]
        #         values = values[mask]
        #         if len(values) > 1:
        #             y_cen = np.average(pixels[:, 0], weights=values)
        #             x_cen = np.average(pixels[:, 1], weights=values)
        #             centered = pixels - [y_cen, x_cen]
        #             cov = np.cov(centered.T, aweights=values)
        #             eigvals, eigvecs = np.linalg.eigh(cov)  # [minor, major]
        #             major_axis = eigvecs[:, 1]
        #             minor_axis = eigvecs[:, 0]
        #             if eigvals[0] != 0:
        #                 ellipticity = eigvals[1] / eigvals[0]  # >1 = wydłużony, ~1 = okrągły
        #
        #                 if ellipticity > 2:
        #                     for ay, ax in tmp:
        #                         maska0[ay, ax] = True
        return maska0






    def cosmic_ray_detection(self,image):
        image = image

        kernel1 = [[-1, 0, 1],
                [-2, 0, 2],
                [-1, 0, 1]]

        kernel2 = [[-1, -2, -1],
                [0, 0, 0],
                [1, 2, -1]]

        result1 = convolve(image, kernel1)
        result2 = convolve(image, kernel2)

        maska1 = result1 > np.median(result1) + 5 * mad_std(result1)
        maska2 = result2 > np.median(result2) + 5 * mad_std(result2)

        maska = maska1 | maska2

        # znajdowanie grup

        conection_kernel = generate_binary_structure(2, 2)  # kernel grupowania
        labeled_array, num_features = label(maska, structure=conection_kernel)
        sizes = ndimage_sum(maska, labeled_array, range(1, num_features + 1))

        crays_x = []
        crays_y = []

        hot_x = []
        hot_y = []

        maska0 = np.zeros_like(image, dtype=bool)
        for i in range(1, num_features + 1):
            tmp = np.argwhere(labeled_array == i)

            if len(tmp) > 5:
                gx = []
                gy = []
                for ay, ax in tmp:
                    gx.append(ax)
                    gy.append(ay)

                gx0 = int(np.mean(gx))
                gy0 = int(np.mean(gy))
                dx = int(max(gx) - min(gx))
                dy = int(max(gy) - min(gy))
                crays_x.append(gx0)
                crays_y.append(gy0)

                image_cut = image[gx0 - 2 * dx:gx0 + 2 * dx, gy0 - 2 * dy:gy0 + 2 * dy]

                # Współrzędne pikseli
                y_ind, x_ind = np.indices(image_cut.shape)

                # Spłaszczone dane
                pixels = np.column_stack((y_ind.ravel(), x_ind.ravel()))
                values = image_cut.ravel()

                # Opcjonalna maska, np. tylko jasne piksele
                mask = values > 0
                pixels = pixels[mask]
                values = values[mask]

                mask = values > np.median(values) + mad_std(values)
                pixels = pixels[mask]
                values = values[mask]

                if len(values) > 0:

                    # Środek ciężkości (ważony jasnością)
                    y_cen = np.average(pixels[:, 0], weights=values)
                    x_cen = np.average(pixels[:, 1], weights=values)

                    # Centrowanie danych względem środka
                    centered = pixels - [y_cen, x_cen]

                    # Macierz kowariancji
                    cov = np.cov(centered.T, aweights=values)
                    eigvals, eigvecs = np.linalg.eigh(cov)  # [minor, major]

                    # PCA: główna oś i kąt orientacji
                    major_axis = eigvecs[:, 1]
                    minor_axis = eigvecs[:, 0]
                    ellipticity = eigvals[1] / eigvals[0]  # >1 = wydłużony, ~1 = okrągły

                    #print(f"Eliptyczność (major/minor): {ellipticity:.2f}")

                    #print(i, len(tmp))

                    if ellipticity > 1.5:
                        for ay, ax in tmp:
                            maska0[ay, ax] = True

        return maska0, crays_x, crays_y


    def hot_pixel_detection(self,image):

        image = image

        kernel1 = [[0, -1, 0],
                   [-1, 4, -1],
                   [0, -1, 0]]

        kernel2 = [[0, -1, 0],
                   [-1, 0, 1],
                   [0, 1, 0]]

        result = convolve(image, kernel1)

        return result

    def mask_generator(self,result,th=3):
        th = th

        maska = result > np.median(result) + th * mad_std(result)

        # znajdowanie grup
        conection_kernel = generate_binary_structure(2, 2)  # kernel grupowania
        labeled_array, num_features = label(maska, structure=conection_kernel)
        sizes = ndimage_sum(maska, labeled_array, range(1, num_features + 1))

        hot_x = []
        hot_y = []

        for i in range(1, num_features + 1):
            tmp = np.argwhere(labeled_array == i)
            if len(tmp) == 1:
                ax, ay = tmp[0]
                d = 5
                image_cut = image[ax - d:ax + d, ay - d:ay + d]
                mk = image_cut > np.median(image_cut) + 1000  # + 100 * mad_std(image_cut)
                if len(image_cut[mk]) == 1:
                    hot_x.append(ay)
                    hot_y.append(ax)

        return hot_x, hot_y


def gauss_kernel(size, sigma):
    kernel = np.fromfunction(lambda x, y: (1 / (2 * np.pi * sigma ** 2)) * np.exp(
        -((x - (size - 1) / 2) ** 2 + (y - (size - 1) / 2) ** 2) / (2 * sigma ** 2)), (size, size))
    return kernel / np.sum(kernel)


def line_detection_kernel(R):
    size = 2 * R + 1
    center = R
    y, x = np.ogrid[:size, :size]
    distance = np.sqrt((x - center) ** 2 + (y - center) ** 2)
    inner = R - 1 / 2
    outer = R + 1 / 2

    left = ((x <= center) & (y <= center)) | ((x >= center) & (y >= center))
    right = ((x < center) & (y > center)) | ((x > center) & (y < center))

    # left
    mk = ((distance >= inner) & (distance <= outer))
    kernel_l = mk.astype(float)
    tmp_mk = ((distance >= inner) & (distance <= outer) & right)
    kernel_l[tmp_mk] = -1

    # right
    mk = ((distance >= inner) & (distance <= outer))
    kernel_r = mk.astype(float)
    tmp_mk = ((distance >= inner) & (distance <= outer) & left)
    kernel_r[tmp_mk] = -1

    return kernel_l, kernel_r





def make_segments(image, n_segments=10, overlap=0):
    height, width = image.shape
    seg_h = height // n_segments
    seg_w = width // n_segments

    segments = []

    for i in range(n_segments):
        for j in range(n_segments):
            result = {}

            y_start = (i * seg_h) - overlap
            if y_start < 0: y_start = 0
            x_start = (j * seg_w) - overlap
            if x_start < 0: x_start = 0
            y_end = ((i + 1) * seg_h) + overlap if i < n_segments - 1 else height
            x_end = ((j + 1) * seg_w) + overlap if j < n_segments - 1 else width

            subframe = image[y_start:y_end, x_start:x_end]

            result = {}
            result["x"] = [x_start, x_end]
            result["y"] = [y_start, y_end]
            result["subframe"] = subframe
            segments.append(result)

    return segments


def polysurf(x, y, coeff):
    a0, a1, a2, a3, a4, a5 = coeff
    return a0 + a1 * x + a2 * y + a3 * x ** 2 + a4 * x * y + a5 * y ** 2