#!/usr/bin/env python3

# Pomiar jednej gwiazdy pod kursorem (klawisze e, r) - tym samym przepisem co FFS.star_info (pyaraucaria):
# wycinek +-box wokol najjasniejszego piksela, tlo = mediana brzegu wycinka, FWHM = (fwhm_x + fwhm_y) / 2
# z FFS.fwhm, eliptycznosc i theta z FFS.adaptive_moments (pca, gdy nie zbiegaja), CPE, shape = CPE x FWHM^2,
# CI z promieniami 1 i 2 FWHM. Dzieki temu liczby z "e" sa te same, co FFS / TOI / ofp liczy dla klatki.
# Uzywa tylko statycznych funkcji FFS - przy zmianach w FFS.star_info poprawic tez tutaj.

import numpy
from pyaraucaria.ffs import FFS

BOX = 10            # polowa boku wycinka pomiarowego, jak FFS.star_info(box=10) / calc_frame_fwhm


def find_peak(dane, x, y, search):
    # najjasniejszy skonczony piksel w kwadracie +-search wokol (x, y) -> (x, y) calkowite albo None
    ny, nx = dane.shape
    x0, x1 = max(0, int(round(x)) - search), min(nx, int(round(x)) + search + 1)
    y0, y1 = max(0, int(round(y)) - search), min(ny, int(round(y)) + search + 1)
    cut = dane[y0:y1, x0:x1]
    if cut.size == 0 or not numpy.isfinite(cut).any(): return None
    dy, dx = numpy.unravel_index(numpy.nanargmax(cut), cut.shape)
    return x0 + dx, y0 + dy


def measure_star(dane, x, y, search=5, box=BOX, saturation=None):
    # gwiazda przy (x, y) (wspolrzedne oryginalu, x = kolumna): dict z wynikami albo None (brak danych)
    p = find_peak(dane, x, y, search)
    if p is None: return None
    px, py = p
    ny, nx = dane.shape
    x0, x1 = max(0, px - box), min(nx, px + box)
    y0, y1 = max(0, py - box), min(ny, py + box)
    cut = numpy.asarray(dane[y0:y1, x0:x1], dtype=float)
    border = numpy.concatenate([cut[0], cut[-1], cut[:, 0], cut[:, -1]])
    border = border[numpy.isfinite(border)]
    bkg = numpy.median(border) if border.size else numpy.nan
    sigma = 1.4826 * numpy.median(numpy.abs(border - bkg)) if border.size else numpy.nan    # szum tla (MAD)
    cut = cut - bkg
    peak = float(dane[py, px])

    res = {"x_peak": px, "y_peak": py, "peak": peak, "bkg": bkg, "sigma": sigma, "flux": numpy.nansum(cut),
           "saturated": saturation is not None and peak >= float(saturation), "box": (x0, x1, y0, y1)}
    cx, cy = FFS.centroid(numpy.nan_to_num(cut))
    res["x"], res["y"] = (x0 + cx, y0 + cy) if cx is not None else (float(px), float(py))

    f_mom, e, t = FFS.adaptive_moments(cut)
    res["method"] = "adaptive moments"
    if not numpy.isfinite(e):
        f_mom, e, t = FFS.pca(cut)
        res["method"] = "pca"
    fx, fy = FFS.fwhm(cut)
    fwhm = (fx + fy) / 2 if numpy.isfinite(fx) and numpy.isfinite(fy) else numpy.nan
    cpe = FFS.cpe(cut)
    if numpy.isfinite(fwhm) and fwhm > 0: r1, r2 = 1.0 * fwhm, 2.0 * fwhm
    else: r1, r2 = 2.0, 4.0
    res.update(fwhm=fwhm, fwhm_x=fx, fwhm_y=fy, fwhm_moments=f_mom, ellipticity=e, theta=t, cpe=cpe,
               shape=cpe * fwhm ** 2, ci=FFS.concentration_index(cut, r1, r2))
    return res


def moment_axes(fwhm, e):
    # polosie elipsy FWHM (polowa wysokosci) z FWHM i eliptycznosci adaptive_moments:
    # fwhm = 2.355 (sa + sb) / 2, e = 1 - sb / sa  ->  polosie = 1.1774 sa, 1.1774 sb
    if not (numpy.isfinite(fwhm) and numpy.isfinite(e)): return numpy.nan, numpy.nan
    q = 1.0 - e
    sa = 2.0 * fwhm / 2.355 / (1.0 + q)
    return 1.1774 * sa, 1.1774 * q * sa
