#!/usr/bin/env python3

import os
import numpy as np

from astropy.io import fits
from pyaraucaria.ffs import FFS

import os


def main():
    fits_files = [f for f in os.listdir("/Users/mgorski/work/data/fits_examples") if f.lower().endswith(".fits")]

    for fitsfile in fits_files:
        hdul = fits.open(fitsfile)
        data = hdul[0].data
        hdr = hdul[0].header
        hdul.close()

        ffs = FFS(data)
        ffs.saturation = 50000
        ffs.calc_frame_fwhm(threshold=10, fwhm=10, box=10, N_stars=20)

        print(ffs["frame"]["fwhm"])



if __name__ == '__main__':
    main()