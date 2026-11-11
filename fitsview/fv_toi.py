#!/usr/bin/env python3

# FFS "jak w TOI" (przycisk "Run fast" w oknie FFS - calc_frame_fwhm jak TOI): te same wywolania co TOI fits_gui.FFS_Worker, opis jak panel
# TOI i gotowe ustawienia tabel. Oznaczenia na obrazie - zwyklymi tabelami FitsView (Catalog), nie osobnym
# mechanizmem: tabela linii (ffs.lines - odcinki, jak dotad) i tabela gwiazd pokazana dwa razy z zakresem kolumny
# (suwaki min / max w Catalog) i markerem jak w TOI. Stale z TOI fits_gui z 2026-11-11 - przy zmianach w TOI poprawic tez tutaj.
# TOI liczy FFS na image.T (x <-> y); FitsView na obrazie (x = kolumna), wiec katy bez zamiany.

import numpy

# --- jak TOI FFS_Worker.run
FWHM_PARAMS = dict(threshold=10, fwhm=5, box=15, N_stars=50)
SKY_SEGMENTS = 7

# --- progi jak TOI fits_gui
STAR_SHAPE_WINDOW = (0.55, 0.95)        # gwiazdy z shape poza oknem - odrzucone z FWHM klatki
ELLIP_WARN = 0.15
TRAILED_E_MIN = 0.4
PATTERN_MIN_STRENGTH = 0.15
FWHM_ARCSEC_WARN = 2.3


def saturation_for(header):
    # TOI calc_ffs: zb08 / wk06 45000 (koniec przetwornika ~64500, zapas na nieliniowosc), jk15 150000
    tel = str(header.get("TELESCOP", "")).strip().lower() if header is not None else ""
    return 150000. if tel == "jk15" else 45000.


def pixel_scale(header):
    # arcsec / px z naglowka (OCA: SCALE), None gdy brak - FWHM tylko w pikselach
    if header is None: return None
    for k in ("SCALE", "PIXSCALE", "SECPIX"):
        try:
            v = float(header.get(k))
            if v > 0: return v
        except (TypeError, ValueError):
            pass
    return None


def run(ffs):
    # na nowym obiekcie FFS(image, saturation=saturation_for(...), autobin=True), jak TOI
    ffs.calc_frame_fwhm(**FWHM_PARAMS)
    ffs.sky_gradient(n_segments=SKY_SEGMENTS)
    try:            # wzor katow gwiazd (psf_pattern); < 5 gwiazd -> ValueError, TOI tez ignoruje
        ffs.calc_star_field_stats()
    except Exception:
        pass


def views(saturation):
    # tabela gwiazd pokazana jak oznaczenia TOI: kolumna kolorowania ("color") + zakres suwakow w Catalog
    # (range: (min, max), None - koniec zakresu kolumny; outside - obiekty poza zakresem). Nazwa produktu -> ustawienia
    lo, hi = STAR_SHAPE_WINDOW
    return {
        "stars rejected": dict(valuecol="shape", range=(lo, hi), outside=True, marker="open square", mksize=9, color="red",
                               description="Stars measured but rejected from the frame FWHM: shape outside %g-%g (as TOI red squares)" % (lo, hi)),
        "stars saturated": dict(valuecol="max_adu", range=(saturation, None), outside=False, marker="open circle", mksize=7,
                                color="red", description="Saturated stars: max_adu >= %g (as TOI red circles)" % saturation),
    }


def pattern_strength(ffs):
    st = ffs.stats["frame"]
    pattern = st.get("psf_pattern")
    if pattern == "linear":
        return float(st.get("psf_e_mean", numpy.nan))
    if pattern in ("radial", "tangential") and ffs.stars is not None and "pattern" in ffs.stars.colnames:
        e = numpy.asarray(ffs.stars["ellipticity"], dtype=float)
        m = numpy.asarray(ffs.stars["pattern"], dtype=bool)
        return float(st["psf_pattern_s"] * numpy.mean(e[m])) if m.any() else numpy.nan
    return numpy.nan


def summary(ffs, scale=None, dx=0, dy=0, red="red", dim="gray"):
    # opis HTML jak panel TOI (ostrzezenia, FWHM, eliptycznosc, shape, gwiazdy, wzor PSF)
    warn = lambda what, v: f'<span style="color:{red};">WARNING</span>: {what}: <span style="color:{red};"><b>{v}</b></span><br>'
    num = lambda v: "--" if v is None or not numpy.isfinite(v) else f"{v:.2f}"
    st = ffs.stats["frame"]
    txt = ""
    med = st.get("median")
    for key, what in (("bkg_max_amplitude", "bkg amplitude"), ("bkg_frame_gradient", "frame gradient")):
        v = st.get(key)
        if med and v is not None and numpy.isfinite(v) and abs(v / med) > 0.1:
            txt += warn(what, "%.0f" % v)
    lines = ffs.lines
    if lines is not None and len(lines):
        other = numpy.zeros(len(lines), bool)
        for k in ("spike", "bleed"):
            if k in lines.colnames: other |= numpy.asarray(lines[k], dtype=bool)
        if (~other).sum():
            txt += warn("satellite trail(s)", int((~other).sum()))
    stars = ffs.stars
    if stars is not None and len(stars):
        e = numpy.asarray(stars["ellipticity"], dtype=float)
        t = numpy.asarray(stars["theta"], dtype=float)
        m = numpy.isfinite(e) & numpy.isfinite(t)
        if m.sum() >= 3 and numpy.median(e[m]) >= TRAILED_E_MIN:
            z = numpy.sum(e[m] * numpy.exp(2j * t[m])) / numpy.sum(e[m])
            s = f'<span style="color:{red};">WARNING</span>: trailed stars: e <span style="color:{red};"><b>{numpy.median(e[m]):.2f}</b></span>'
            if abs(z) >= 0.7: s += f' @ {numpy.degrees(0.5 * numpy.angle(z)) % 180:.0f}&deg;'
            txt += s + "<br>"
    fwhm = st.get("fwhm")
    if fwhm is None or not numpy.isfinite(fwhm):
        txt += f'FWHM: <span style="color:{red};"><b>--</b></span> (too few good stars)<br>'
    else:
        arc = fwhm * scale if scale else None
        bad = arc is not None and arc > FWHM_ARCSEC_WARN
        fmt = (lambda v: f'<span style="color:{red};"><b>{v:.1f}</b></span>') if bad else (lambda v: f'<b>{v:.1f}</b>')
        txt += f'FWHM: {fmt(fwhm)} px' + (f' ({fmt(arc)} arcsec)' if arc is not None else "") + "<br>"
    ell = st.get("ellipticity")
    bad = ell is not None and numpy.isfinite(ell) and ell > ELLIP_WARN
    txt += f'ellipse: <span style="color:{red};"><b>{ell:.2f}</b></span><br>' if bad else f'ellipse: <b>{num(ell)}</b><br>'
    txt += f'shape: <b>{num(st.get("shape"))}</b><br>'
    used = st.get("used_stars")
    if used is not None:
        nmax = FWHM_PARAMS["N_stars"]
        txt += (f'stars used: <span style="color:{red};"><b>{used}</b></span>/{nmax}<br>' if used < 5
                else f'stars used: <b>{used}</b>/{nmax}<br>')
    pattern = st.get("psf_pattern")
    if pattern is not None:
        if pattern == "linear":
            p = f'<b>linear</b> e {st["psf_e_mean"]:.2f} @ {numpy.degrees(st["psf_theta_mean"]) % 180:.0f}&deg;'
        elif pattern in ("radial", "tangential"):
            p = f'<b>{pattern}</b> e {pattern_strength(ffs):.2f} (centre {st["psf_centre_x"] + dx:.0f}, {st["psf_centre_y"] + dy:.0f})'
            if pattern == "tangential" and numpy.isfinite(st.get("psf_rot_deg", numpy.nan)):
                p += f' rot {st["psf_rot_deg"]:.3f}&deg;'
        else:
            p = "<i>none</i>"
        if pattern in ("linear", "radial", "tangential") and not pattern_strength(ffs) >= PATTERN_MIN_STRENGTH:
            p = f'<span style="color:{dim};">{p} (weak)</span>'
        txt += "PSF pattern: " + p + "<br>"
    return txt
