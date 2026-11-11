#!/usr/bin/env python3
# PyQtX przed matplotlib: backend_qtagg bierze juz zaimportowane PyQt6 (inaczej moglby wziac PyQt5)
from fitsview.PyQtX.QtCore import Qt
from fitsview.PyQtX import QtCore
from fitsview.PyQtX.QtWidgets import QMainWindow, QWidget, QLabel, QTextEdit, QLineEdit, QPushButton, \
    QGridLayout, QHBoxLayout, QVBoxLayout, QComboBox, QCheckBox, QTableWidget, \
    QTableWidgetItem, QApplication, QTabWidget, QToolButton, QMenu, QFileDialog, QHeaderView, QScrollArea, QSizePolicy, \
    QAbstractItemView, QFrame
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

import numpy as np
import numpy
import inspect, re, html, traceback

from astropy.table import Table
from astropy.io import fits

from pyaraucaria.ffs import FFS

from fitsview.fv_windows import init_panel, show_panel, close_panel
from fitsview.fv_theme import theme
from fitsview import fv_toi

class HeaderTabLocal(QWidget):
   def __init__(self,parent,header): 
       QWidget.__init__(self)
       self.setWindowFlag(Qt.WindowType.Tool)
       self.parent=parent
       self.header=header
       self.setWindowTitle('HDR')
       self.filter_l= QLabel("Filter: ")

       self.filter_e= QLineEdit()
       self.filter_e.setText("") 
       self.filter_e.textChanged.connect(self.update)


       self.cl =  QPushButton('Close', self)
       self.cl.clicked.connect(self.close_window)
       
       self.heder_e= QTextEdit()
       self.heder_e.setReadOnly(True)
       
       grid= QGridLayout()   
       grid.addWidget(self.filter_l,0,0)
       grid.addWidget(self.filter_e,0,1)
       grid.addWidget(self.heder_e,1,0,3,2)
       grid.addWidget(self.cl,4,1)
       self.setLayout(grid)
       init_panel(self, self.parent, "header", "Header", 600, 600)
       self.update()

       

   def update(self):     
       hdr=repr(self.header)
       hdr=hdr.split("\n")
       text=self.filter_e.text()
       txt=""
       for x in hdr:
           if str(text).lower() in str(x).lower(): txt=txt+str(x)+"\n"
       self.heder_e.setText(txt) 
       show_panel(self)


   def close_window(self): 
       close_panel(self)

class TextWindow(QWidget):
  def __init__(self,parent):
      QWidget.__init__(self)
      self.setWindowFlag(Qt.WindowType.Tool)
      self.parent=parent
      self.setWindowTitle('Query')
      
      self.txt=""

      self.pole= QTextEdit()
      self.cl =  QPushButton('Close', self)
      self.cl.clicked.connect(self.close_window)
      
      hbox1 =  QHBoxLayout()
#      hbox1.addStretch(1)
      hbox1.addWidget(self.pole)
      hbox2 =  QHBoxLayout()
      hbox2.addStretch(1)
      hbox2.addWidget(self.cl)
      vbox =  QVBoxLayout()
#      vbox.addStretch(1)
      vbox.addLayout(hbox1)
      vbox.addLayout(hbox2)        
      self.setLayout(vbox) 
         
      self.pole.setReadOnly(True)
#      self.pole.setLineWrapMode(0)
      init_panel(self, self.parent, "query", "Query", 400, 300)
  def update(self):
      show_panel(self)
      self.pole.append(self.txt)
      self.parent.activateWindow()
      
  def close_window(self):     
      close_panel(self)

class PlotWindow(QWidget):
    def __init__(self,parent,kind="profile",title="Plot"):
        # kind/title: panel (dok) - profile (klawisze l, c), radial (r), isophotes (e)
        QWidget.__init__(self)
        self.setWindowFlag(Qt.WindowType.Tool)
        self.parent=parent
        self.setWindowTitle(title)
        self.txt=""
        self.fig = Figure(figsize=(2, 2), linewidth=-1, dpi=100,tight_layout=True, frameon=True)
        self.canvas = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.axes.set_xlabel('X label')

        self.pole= QLineEdit()
        self.cl =  QPushButton('Close', self)
        self.cl.clicked.connect(self.close_window)

        hbox1 =  QHBoxLayout()
        hbox1.addWidget(self.canvas)
        hbox1a =  QHBoxLayout()
        hbox1a.addWidget(self.toolbar)
        hbox2 =  QHBoxLayout()
        hbox2.addWidget(self.pole)
        hbox3 =  QHBoxLayout()
        hbox3.addStretch(1)
        hbox3.addWidget(self.cl)
        vbox =  QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox1a)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        self.setLayout(vbox)

        self.pole.setReadOnly(True)
        self.toolbar.hide()
        init_panel(self, self.parent, kind, title, 400, 400, dy=330)       # okno: pod oknem Query

    def update(self):
        self.style_theme()                      # po axes.clear() w Image osie wracaja do bieli
        show_panel(self)
        self.pole.setText(self.txt)
        self.parent.activateWindow()

    def style_theme(self):
        theme.style_figure(self.fig, [self.axes])
        self.canvas.draw_idle()

    def close_window(self):
        close_panel(self)
        self.parent.update()

    def resizeEvent(self, event):
        if float(self.frameGeometry().width()) > 700 and float(self.frameGeometry().height()) > 500:
            self.toolbar.show()
        else:
            self.toolbar.hide()
        QWidget.resizeEvent(self, event)


class FigureWindow(QWidget):
    def __init__(self,parent):
        QWidget.__init__(self)
        self.setWindowFlag(Qt.WindowType.Tool)
        self.parent=parent
        self.txt = ""
        self.mkUI()
        self.update()

        self.xcol_s.currentTextChanged.connect(self.update)
        self.ycol_s.currentTextChanged.connect(self.update)


    def mkUI(self):

        self.xcol_l = QLabel("X: ")
        self.xcol_s = QComboBox()

        self.ycol_l = QLabel("Y: ")
        self.ycol_s = QComboBox()

        keys = self.parent.data.keys()
        self.xcol_s.addItems(keys)
        self.ycol_s.addItems(keys)
        self.xcol_s.setCurrentIndex(len(keys)-2)
        self.ycol_s.setCurrentIndex(len(keys)-1)

        self.fig = Figure(figsize=(2, 2), linewidth=-1, dpi=100,tight_layout=True, frameon=True)
        self.canvas = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.hide()

        self.pole= QLineEdit()
        self.pole.setReadOnly(True)

        self.cl =  QPushButton('Close', self)
        self.cl.clicked.connect(self.close_window)

        self.setWindowTitle('Figure')
        grid = QGridLayout()

        w = 0
        grid.addWidget(self.ycol_l,w,0)
        grid.addWidget(self.ycol_s,w,1)
        grid.addWidget(self.xcol_l,w,2)
        grid.addWidget(self.xcol_s,w,3)
        w = w + 1
        grid.addWidget(self.canvas,w,0,3,4)
        w = w + 3
        grid.addWidget(self.toolbar,w,0,1,4)
        w = w + 1
        grid.addWidget(self.pole,w,0,1,4)
        w = w + 1
        grid.addWidget(self.cl,w,3,1,1)

        self.setLayout(grid)

        init_panel(self, self.parent, "figure", "Figure", 500, 400, dy=330)

    def update(self):

        self.axes.clear()

        self.axes.set_xlabel(self.xcol_s.currentText())
        self.axes.set_ylabel(self.ycol_s.currentText())

        x = self.parent.data[self.xcol_s.currentText()]
        y = self.parent.data[self.ycol_s.currentText()]

        self.axes.plot(x,y,".b")

        theme.style_figure(self.fig, [self.axes])
        self.canvas.draw()

        show_panel(self)
        #self.pole.setText(self.txt)
        self.parent.activateWindow()

    def style_theme(self):
        theme.style_figure(self.fig, [self.axes])     # bez update(): nie otwiera zamknietego okna
        self.canvas.draw_idle()

    def close_window(self):
        close_panel(self)
        self.parent.update()

    def resizeEvent(self, event):
        if float(self.frameGeometry().width()) > 700 and float(self.frameGeometry().height()) > 500:
            self.toolbar.show()
        else:
            self.toolbar.hide()
        QWidget.resizeEvent(self, event)

def doc_summary(func):
    # pierwszy akapit docstringu metody FFS (podpowiedz do przycisku)
    doc = inspect.getdoc(func) or ""
    return doc.split("\n\n")[0]

def doc_params(func):
    # opisy parametrow z sekcji "Parameters" docstringu (numpydoc): {nazwa: [typ, opis]}
    doc = inspect.getdoc(func) or ""
    out = {}
    if "Parameters\n----------" not in doc: return out
    sekcja = doc.split("Parameters\n----------")[1]
    sekcja = re.split(r"\n\S[^\n]*\n-{3,}", sekcja)[0]          # do nastepnej sekcji (Notes, ...)
    name = None
    for line in sekcja.split("\n"):
        if line and not line.startswith(" "):
            name, _, typ = line.partition(" : ")
            name = name.strip()
            out[name] = [typ.strip(), ""]
        elif name:
            out[name][1] += line.strip() + " "
    return out

def to_value(txt):
    # tekst z pola parametru -> None / int / float / str
    txt = txt.strip()
    if txt in ("", "None"): return None
    for f in (int, float):
        try: return f(txt)
        except ValueError: pass
    return txt

def tooltip(title, txt):
    # rich text, zeby Qt zawijal dlugie opisy
    return "<b>%s</b><br>%s" % (html.escape(title), html.escape(txt).replace("\n", "<br>"))


def power_spectrum(ffs, window=True, min_freq=0.02, exclude=FFS.EXCLUDE_ALL):
    """2D Fourier power spectrum of the cut-out -> (log10 power, strongest peak).

    Periodic patterns (electronic interference, banding, fringes) show up as isolated peaks.
    Computed on the residual image - sky (ffs.maps["sky"] if present, otherwise the median of
    good pixels); pixels in ffs.bad_mask(exclude) are set to 0, so stars and bad pixels do not
    dominate the spectrum. The spectrum is shifted so that the zero frequency is in the centre
    (pixel ny//2, nx//2); it has the cut-out size but it is NOT in image coordinates: offset
    (dx, dy) from the centre is the frequency (dx / nx, dy / ny) cycles/px. The peak is the
    strongest one with frequency >= min_freq: {"period" px, "angle" deg, "peak" power / median}.

    Parameters
    ----------
    window : bool
        Multiply by a 2D Hann window first; without it the frame edges give a strong
        cross along the axes of the spectrum.
    min_freq : float
        Lowest frequency (cycles/px) searched for the peak; lower ones (periods > 1/min_freq px:
        sky gradients, large objects) are skipped.
    exclude : sequence of str
        Names of the masks whose pixels are set to 0 (bad_mask); missing masks are ignored.
    """
    image = ffs.image
    bad = ffs.bad_mask(exclude) | ~np.isfinite(image)
    if "sky" in ffs.maps:
        resid = image - ffs.maps["sky"]
    else:
        good = image[~bad]
        resid = image - (np.median(good) if good.size else 0.)
    resid = np.where(bad | ~np.isfinite(resid), 0., resid).astype(np.float32)
    ny, nx = resid.shape
    if window:
        resid = resid * np.outer(np.hanning(ny), np.hanning(nx)).astype(np.float32)

    power = np.abs(np.fft.fftshift(np.fft.fft2(resid))) ** 2 / resid.size
    fourier = np.log10(power + 1e-30)

    # najsilniejszy pik poza niskimi czestosciami (gradienty tla, duze obiekty)
    fy = (np.arange(ny) - ny // 2) / ny
    fx = (np.arange(nx) - nx // 2) / nx
    freq = np.hypot(fy[:, None], fx[None, :])
    search = freq >= min_freq
    peak = {"period": np.nan, "angle": np.nan, "peak": np.nan}
    if search.any():
        pw = np.where(search, power, -np.inf)
        iy, ix = np.unravel_index(np.argmax(pw), pw.shape)
        peak = {"period": 1.0 / freq[iy, ix],
                "angle": np.degrees(np.arctan2(fy[iy], fx[ix])) % 180.0,
                "peak": power[iy, ix] / max(np.median(power[search]), 1e-30)}
    return fourier, peak


class FFSWindow(QWidget):
    # Okno FFS dla wycinka obrazu (image, przesuniety o dx, dy w pelnej klatce).
    # Pola parametrow sa budowane z sygnatur metod FFS (wartosci domyslne biblioteki, chyba ze
    # nadpisane w self.defaults), podpowiedzi z ich docstringow. Jeden obiekt FFS na wycinek:
    # kazdy przycisk wykonuje swoj krok na nim, korzystajac z masek z poprzednich krokow
    # (np. Statistics po Find stars liczy statystyki bez gwiazd). Nowy obiekt: Reset, nowy wycinek
    # albo zmiana parametrow konstruktora (zakladka Frame). Wyniki (maski, mapy, tabele) sa
    # przenoszone do pelnej klatki; maski i mapy otwierane na zadanie ("Show").

    # maski, ktore krok usuwa przed ponownym liczeniem - inaczej wykluczylyby same siebie
    # (maska threshold pomija piksele "lines", mapa kolumn piksele "bad_columns", ...)
    DROP = {
        "lines": ("lines", "spikes"),
        "calibration": ("bad_columns", "bad_rows", "hot_pixels", "cold_pixels"),
    }
    # tabele FFS: nazwa produktu -> atrybut obiektu FFS
    # maski do wyboru w menu exclude oprocz FFS.EXCLUDE_ALL: przelania ladunku (mk_bleeds_mask) nie sa w zadnej
    # domyslnej liscie FFS (sa podzbiorem saturacji), ale moze byc potrzeba pominac tylko je
    EXTRA_EXCLUDE = ("bleeds",)
    TABLES = {"sky segments": "sky", "bleeds": "bleeds", "lines": "lines", "stars": "stars", "psf grid": "psf_grid"}
    # Run all: kolejnosc jak FFS.calc_frame_fwhm, na koniec tlo i statystyki jeszcze raz, juz z maskami
    RUN_ALL = ["stats", "sky", "cosmics", "lines", "stars", "sky", "stats", "psf"]

    def __init__(self, parent, image, saturation=None,dx=0,dy=0):
        QWidget.__init__(self)          # zwykle okno (nie Qt.WindowType.Tool), zeby nie zaslanialo glownego
        self.parent = parent
        self.image = image
        self.dx=int(dx)
        self.dy=int(dy)

        if saturation is None:
            try: saturation = float(self.parent.saturation_e.text())
            except ValueError: saturation = 50000.

        # wartosci domyslne GUI inne niz w bibliotece
        self.defaults = {
            ("FFS", "saturation"): saturation,
            ("FFS", "autobin"): True,                   # duze klatki: inaczej find_lines potrzebuje >10 GB
            ("find_stars", "threshold"): 10,            # jak calc_frame_fwhm
            ("find_stars", "fwhm"): 5,
            ("star_info", "N_stars"): 100,              # statystyki klatki ze 100 najjasniejszych (jak calc_frame_fwhm)
            ("mk_bad_columns_mask", "threshold"): 5,
            ("mk_hot_pixels_mask", "threshold"): 50,
            ("mk_cold_pixels_mask", "threshold"): 50,
        }

        self.txt = ""
        self.ffs = None
        self.fourier = None          # widmo mocy wycinka (power_spectrum, funkcja FitsView, nie FFS)
        self.toi_views = {}          # przycisk Run fast (calc_frame_fwhm jak TOI): widoki tabeli gwiazd z warunkiem (fv_toi.views), nazwa -> ustawienia
        self.fft_peak = None
        self.params = {}
        self.products = []           # (typ, nazwa, opis) produktow biezacego obiektu FFS
        self.product_step = {}       # (typ, nazwa) -> krok, w ktorym produkt powstal / zmienil sie
        self.changed = set()         # produkty zmienione w ostatnim run()

        self.mkUI()
        self.initFFS()

    def initFFS(self):
        h, w = self.image.shape
        self.info_l.setText("cut: %d x %d px at x=%d, y=%d" % (w, h, int(self.dx), int(self.dy)))
        self.ffs = None                         # nowy wycinek - nowy obiekt FFS
        self.run("stats")

    # ------------------------------------------------------------------ liczenie

    def add_exclude_action(self, e, menu, name, checked):
        a = menu.addAction(name)
        a.setCheckable(True)
        a.setChecked(checked)
        a.setToolTip(self.ffs.masks_description.get(name, "") if self.ffs is not None else "")
        a.toggled.connect(lambda checked, e=e: self.exclude_text(e))

    def add_mask_actions(self, e):
        # maski obiektu FFS, ktorych nie ma jeszcze w menu exclude (niezaznaczone)
        if self.ffs is None: return
        have = {a.text() for a in e.menu().actions()}
        for n in self.ffs.masks:
            if n not in have: self.add_exclude_action(e, e.menu(), n, False)

    def exclude_text(self, e):
        e.setText("%d masks" % sum(a.isChecked() for a in e.menu().actions()))

    def get_params(self, name):
        out = {}
        for k, e in self.params[name].items():
            if isinstance(e, QToolButton): out[k] = tuple(a.text() for a in e.menu().actions() if a.isChecked())
            elif isinstance(e, QCheckBox): out[k] = e.isChecked()
            elif isinstance(e, QComboBox): out[k] = e.currentText()
            else: out[k] = to_value(e.text())
        return out

    def run(self, stage):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.changed = set()
            if stage == "fast":
                self.toi_setup()
            if stage in ("all", "fast") or self.ffs is None:
                self.reset_ffs()
            elif self.get_params("FFS") != self.ffs_params:
                self.pole_e.append("Frame parameters changed: new FFS (masks and maps dropped)")
                self.reset_ffs()
            for st in (self.RUN_ALL if stage == "all" else [stage]):
                before = self.snapshot()
                self.step(st)
                self.step_n = self.step_n + 1                  # kolejny krok na tym obiekcie FFS
                label = "%d: %s" % (self.step_n, st)
                if stage == "all": self.pole_e.append(label)
                for key, obj in self.snapshot().items():      # nowe albo zmienione produkty tego kroku
                    if before.get(key) is not obj:
                        self.product_step[key] = label
                        self.changed.add(key)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            traceback.print_exc()
            self.pole_e.append("ERROR in %s: %s" % (stage, e))
            return
        QApplication.restoreOverrideCursor()

        done = "%d: %s" % (self.step_n, stage) if stage != "all" else "all"
        self.pole_e.append("%s done (bin %d); masks: %s" % (done, self.ffs.bin, ", ".join(self.ffs.masks) or "-"))
        self.show_results(stage)

    def toi_setup(self):
        # przycisk Run fast (calc_frame_fwhm jak TOI): cala klatka i parametry konstruktora jak w TOI (saturacja wg teleskopu, autobin) - pola
        # zakladki Frame dostaja te wartosci, wiec kolejne kroki licza na tym samym obiekcie FFS
        self.image, self.dx, self.dy = self.parent.dane, 0, 0
        h, w = self.image.shape
        self.info_l.setText("cut: %d x %d px at x=0, y=0 (whole frame, Run fast: calc_frame_fwhm as in TOI)" % (w, h))
        sat = fv_toi.saturation_for(getattr(self.parent, "hdr", None))
        self.params["FFS"]["saturation"].setText("%g" % sat)
        self.params["FFS"]["autobin"].setChecked(True)

    def reset_pushed(self):
        # nowy wycinek z aktualnego widoku obrazu
        self.image, self.dx, self.dy = self.parent.ffs_cut()
        self.initFFS()

    def reset_ffs(self):
        # nowy obiekt FFS z parametrami konstruktora (zakladka Frame); maski i mapy od zera
        self.ffs_params = self.get_params("FFS")
        self.ffs = FFS(self.image, **self.ffs_params)
        self.ffs.mk_saturation_mask()
        self.fourier = self.fft_peak = None
        self.toi_views = {}
        self.step_n = 0
        self.product_step = {key: "0: new" for key in self.snapshot()}
        self.changed = set(self.product_step)

    def snapshot(self):
        # produkty obiektu FFS: (typ, nazwa) -> obiekt (porownanie "is" mowi, czy krok go zmienil)
        ffs = self.ffs
        out = {("mask", k): v for k, v in ffs.masks.items()}
        out.update({("map", k): v for k, v in ffs.maps.items()})
        for name, attr in self.TABLES.items():
            if getattr(ffs, attr) is not None: out[("table", name)] = getattr(ffs, attr)
        if ffs.stars is not None:
            for name in self.toi_views: out[("table", name)] = ffs.stars
        if self.fourier is not None: out[("fft", "fourier")] = self.fourier
        return out

    def step(self, stage):
        # jeden krok na biezacym obiekcie FFS
        ffs = self.ffs
        for name in self.DROP.get(stage, ()):
            ffs.masks.pop(name, None)
        if stage == "stats":
            # przelania ladunku z maski saturacji (jak calc_frame_fwhm: zaraz po saturacji, przed statystykami)
            ffs.mk_bleeds_mask(**self.get_params("mk_bleeds_mask"))
            ffs.mk_stats(**self.get_params("mk_stats"))     # wyniki innych krokow (fwhm, psf_*) zostaja
        if stage == "sky":
            ffs.sky_map(**self.get_params("sky_map"))
        if stage == "cosmics":
            ffs.mk_cosmics_mask(**self.get_params("mk_cosmics_mask"))
        if stage == "lines":
            ffs.mk_threshold_mask(**self.get_params("mk_threshold_mask"))
            ffs.mk_ring_mask(**self.get_params("mk_ring_mask"))
            ffs.hough_transform(**self.get_params("hough_transform"))
            ffs.find_lines(**self.get_params("find_lines"))
            ffs.classify_lines(**self.get_params("classify_lines"))
        if stage == "stars":
            ffs.find_stars(**self.get_params("find_stars"))
            ffs.star_info(**self.get_params("star_info"))
            ffs.calc_star_stats(**self.get_params("calc_star_stats"))
            # statystyki klatki z N_stars najjasniejszych; katalog i mapy PSF ze wszystkich zmierzonych
            params = self.get_params("star_info")
            params["N_stars"] = None
            ffs.star_info(**params)
            self.optional(ffs.mk_stars_mask, **self.get_params("mk_stars_mask"))
        if stage == "psf":
            if ffs.stars is None:
                self.pole_e.append("PSF field: run Find stars first")
                return
            self.optional(ffs.mk_star_maps, **self.get_params("mk_star_maps"))
            self.optional(ffs.calc_star_field_stats, **self.get_params("calc_star_field_stats"))
        if stage == "fft":
            self.fourier, self.fft_peak = power_spectrum(ffs, **self.get_params("power_spectrum"))
        if stage == "fast":
            fv_toi.run(ffs)
            hdr = getattr(self.parent, "hdr", None)
            self.toi_views = fv_toi.views(self.ffs_params["saturation"])
            self.toi_html = fv_toi.summary(ffs, fv_toi.pixel_scale(hdr), self.dx, self.dy,
                                           red=theme.hex("bad_fg"), dim=theme.hex("dim_fg"))
        if stage == "calibration":
            ffs.mk_columns_map(**self.get_params("mk_columns_map"))
            ffs.mk_bad_columns_mask(**self.get_params("mk_bad_columns_mask"))
            ffs.mk_pixels_map(**self.get_params("mk_pixels_map"))
            ffs.mk_hot_pixels_mask(**self.get_params("mk_hot_pixels_mask"))
            ffs.mk_cold_pixels_mask(**self.get_params("mk_cold_pixels_mask"))

    def optional(self, func, **params):
        # krok, ktory moze sie nie udac (np. za malo gwiazd) bez utraty reszty wynikow
        try:
            func(**params)
        except ValueError as e:
            self.pole_e.append("%s: %s" % (func.__name__, e))

    def save_pushed(self):
        # wszystkie wyniki (mapy, maski, tabele, statystyki) do jednego pliku MEF (FFS.save_mef)
        if self.ffs is None: return
        fname = str(self.parent.parent.fname).replace(".fits", "") + "_ffs.fits"
        fname = str(QFileDialog.getSaveFileName(self, 'Save FFS results (MEF)', fname)[0])
        if not fname: return
        header = self.parent.hdr.copy() if hasattr(self.parent, "hdr") else fits.Header()
        header["FFCUTX0"] = (self.dx, "FFS cut-out: x of its first column in the frame")
        header["FFCUTY0"] = (self.dy, "FFS cut-out: y of its first row in the frame")
        try:
            self.ffs.save_mef(fname, header=header, overwrite=True)
            self.pole_e.append("saved " + fname)
        except Exception as e:
            traceback.print_exc()
            self.pole_e.append("ERROR in save: %s" % e)

    # ------------------------------------------------------------------ wyniki

    def full_frame(self, a, fill):
        # wynik z wycinka -> tablica w rozmiarze calej klatki (Image.dane)
        out = numpy.full(self.parent.dane.shape, fill, dtype=type(fill) if fill is False else float)
        h, w = a.shape
        out[self.dy:self.dy + h, self.dx:self.dx + w] = a
        return out

    def shift_table(self, table):
        # wspolrzedne tabeli z wycinka -> pelna klatka
        table = table.copy()
        for k in ["x", "x0", "x1", "star_x", "sky_surface_x"]:
            if k in table.colnames: table[k] = table[k] + self.dx
        for k in ["y", "y0", "y1", "star_y", "sky_surface_y"]:
            if k in table.colnames: table[k] = table[k] + self.dy
        if "rho" in table.colnames:
            table["rho"] = table["rho"] + self.dx * numpy.cos(table["theta"]) + self.dy * numpy.sin(table["theta"])
        return table

    def show_results(self, stage):
        ffs = self.ffs

        stats = [(k, v) for k, v in ffs.stats["frame"].items() if numpy.ndim(v) == 0]
        self.stats_t.setRowCount(len(stats))
        for i, (k, v) in enumerate(stats):
            opis = ffs.stats_description["frame"].get(k, "")
            if isinstance(v, str):                                  # psf_pattern
                txt_v = v
            else:
                txt_v = "%d" % v if isinstance(v, (int, numpy.integer)) else "%.4g" % v    # n_excluded, used_stars
            for j, txt in enumerate([k, txt_v]):
                item = QTableWidgetItem(txt)
                item.setToolTip(tooltip(k, opis))
                self.stats_t.setItem(i, j, item)
        self.stats_t.resizeColumnsToContents()

        self.update_products()

        # tabele gwiazd i linii od razu na Image, reszta na zadanie
        if stage in ("stats", "all") and ffs.bleeds is not None and len(ffs.bleeds):
            self.show_product("table", "bleeds")
        if stage in ("lines", "all") and ffs.lines is not None:
            self.show_product("table", "lines")
        if stage in ("stars", "all") and ffs.stars is not None:
            self.show_product("table", "stars")
        if stage in ("stars", "all") and "fwhm" in ffs.stats["frame"]:
            self.pole_e.append("frame_fwhm: %.2f  ellipticity: %.2f  used_stars: %d" % (
                ffs.stats["frame"]["fwhm"], ffs.stats["frame"]["ellipticity"], ffs.stats["frame"]["used_stars"]))

        if stage == "fast":
            # oznaczenia jak w TOI zwyklymi tabelami: linie (odcinki) i gwiazdy z zakresem kolumny (suwaki)
            if ffs.lines is not None: self.show_product("table", "lines")
            if ffs.stars is not None:
                for name in self.toi_views: self.show_product("table", name)
            self.pole_e.append("<b>Run fast</b> (calc_frame_fwhm as in TOI, whole frame):<br>" + self.toi_html)

        if stage == "fft" and self.fourier is not None:
            self.show_product("fft", "fourier")
            pk = self.fft_peak
            self.pole_e.append("fft peak: period %.2f px  angle %.1f deg  peak/median %.3g" % (
                pk["period"], pk["angle"], pk["peak"]))

        # widoczne zakladki produktow zmienionych w tym run() - odswiezamy (schowane zostaja schowane)
        for typ, name, opis in self.products:
            if (typ, name) in self.changed and self.shown(typ, name): self.show_product(typ, name)

    def update_products(self):
        # tabela produktow: shown (zakladka otwarta; klikniecie pokazuje / chowa), typ, nazwa, krok
        ffs = self.ffs
        if ffs is None: return
        self.products = []
        for k in ffs.masks: self.products.append(("mask", k, ffs.masks_description.get(k, "")))
        for k in ffs.maps: self.products.append(("map", k, ffs.maps_description.get(k, "")))
        if ffs.sky is not None: self.products.append(("table", "sky segments", "Sky segments: centres and fitted background (sky_gradient)"))
        if ffs.bleeds is not None: self.products.append(("table", "bleeds", "Charge bleeds: saturated runs along a row or column, drawn as segments (mk_bleeds_mask)"))
        if ffs.lines is not None: self.products.append(("table", "lines", "Detected lines (find_lines, classify_lines)"))
        if ffs.stars is not None: self.products.append(("table", "stars", "Detected stars; not measured have NaN (find_stars, star_info)"))
        if self.fourier is not None: self.products.append(("fft", "fourier", "log10 power spectrum of the cut-out; zero frequency in the centre, offset (dx, dy) = frequency (dx/nx, dy/ny) cycles/px - not image coordinates (power_spectrum)"))
        if ffs.stars is not None:
            for name, v in self.toi_views.items(): self.products.append(("table", name, v["description"]))
        if ffs.psf_grid is not None: self.products.append(("table", "psf grid", "PSF on a grid, drawn as whiskers: direction theta, length ~ ellipticity, the longest 0.9 of a cell (mk_star_maps)"))

        self.products_t.blockSignals(True)
        self.products_t.setRowCount(len(self.products))
        for i, (typ, name, opis) in enumerate(self.products):
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            item.setCheckState(Qt.CheckState.Checked if self.shown(typ, name) else Qt.CheckState.Unchecked)
            item.setToolTip("Tab open: check to show, uncheck to hide")
            self.products_t.setItem(i, 0, item)
            for j, txt in enumerate([typ, name, self.product_step.get((typ, name), "")], 1):
                item = QTableWidgetItem(txt)
                item.setToolTip(tooltip(name, opis))
                self.products_t.setItem(i, j, item)
        self.products_t.resizeColumnsToContents()
        self.products_t.blockSignals(False)

    def gui_entry(self, typ, name):
        # wpis produktu w table_data / map_data / mask_data glownego okna, albo None
        gui = self.parent.parent
        lista = {"mask": gui.mask_data, "map": gui.map_data, "fft": gui.map_data, "table": gui.table_data}[typ]
        i = gui.find_data(lista, self.tab_name(typ, name))
        return None if i is None else lista[i]

    def shown(self, typ, name):
        entry = self.gui_entry(typ, name)
        return entry is not None and not entry.get("hidden") and entry.get("tab") is not None

    def hide_product(self, typ, name):
        if self.shown(typ, name): self.parent.parent.hide_tab(self.gui_entry(typ, name)["tab"])

    def product_checked(self, item):
        if item.column() != 0: return
        typ, name, opis = self.products[item.row()]
        if item.checkState() == Qt.CheckState.Checked:
            self.show_product(typ, name)
            self.goto_product(typ, name)
        else: self.hide_product(typ, name)
        self.update_products()

    def goto_product(self, typ, name):
        # glowne okno przeskakuje na zakladke produktu pokazanego klikiem (nie przy samym liczeniu)
        entry = self.gui_entry(typ, name)
        if entry is not None and entry.get("tab") is not None:
            self.parent.parent.TabWindow.setCurrentWidget(entry["tab"])

    def delete_pushed(self):
        # usuwa zaznaczone produkty z obiektu FFS (kolejne kroki ich nie uzywaja) i chowa ich zakladki
        rows = sorted(set(i.row() for i in self.products_t.selectedIndexes()))
        names = []
        for i in rows:
            typ, name, opis = self.products[i]
            self.hide_product(typ, name)
            if typ == "mask": self.ffs.masks.pop(name, None)
            elif typ == "map": self.ffs.maps.pop(name, None)
            elif typ == "fft": self.fourier = self.fft_peak = None
            elif name in self.toi_views: del self.toi_views[name]      # tylko widok, tabela gwiazd zostaje
            else: setattr(self.ffs, self.TABLES[name], None)
            self.product_step.pop((typ, name), None)
            names.append("%s %s" % (name, typ))
        if names: self.pole_e.append("deleted: " + ", ".join(names))
        self.update_products()

    def tab_name(self, typ, name):
        # np. maska "lines" i tabela "lines" musza miec rozne zakladki
        if typ in ("table", "fft"): return "ffs." + name
        return "ffs.%s %s" % (name, typ)

    def show_product(self, typ, name):
        gui = self.parent.parent
        ffs = self.ffs
        if typ == "mask":
            gui.add_mask(self.full_frame(ffs.masks[name], False), name=self.tab_name(typ, name), description=ffs.masks_description.get(name, ""))
        elif typ == "map":
            gui.add_map(self.full_frame(ffs.maps[name], numpy.nan), name=self.tab_name(typ, name), description=ffs.maps_description.get(name, ""))
        elif typ == "fft":
            # widmo w rozmiarze wycinka, nie w ukladzie klatki - bez full_frame
            desc = [d for t, n, d in self.products if t == typ and n == name]
            gui.add_map(self.fourier, name=self.tab_name(typ, name), description=desc[0] if desc else "", frame=False)
        elif typ == "table" and name in self.toi_views:
            # widok tabeli gwiazd: warunek, marker i kolor jak oznaczenia TOI (pozniej do zmiany w zakladce)
            v = self.toi_views[name]
            gui.add_coo(self.shift_table(ffs.stars), name=self.tab_name(typ, name), color=v["color"], preset=v)
        elif typ == "table":
            table = getattr(ffs, self.TABLES[name])
            if name == "psf grid": table = self.whiskers(table)
            gui.add_coo(self.shift_table(table), name=self.tab_name(typ, name))
        self.update_products()

    def whiskers(self, table):
        # psf_grid -> odcinki x0, y0, x1, y1 (Image rysuje je jak linie): kierunek theta,
        # dlugosc proporcjonalna do eliptycznosci, najdluzszy 0.9 oczka siatki
        table = Table(table)
        h, w = self.image.shape
        g = max(1, int(round(numpy.sqrt(len(table)))))
        e = numpy.nan_to_num(numpy.asarray(table["ellipticity"], dtype=float))
        L = 0.9 * min(w, h) / g * e / max(e.max(), 1e-12)
        c, s = numpy.cos(table["theta"]), numpy.sin(table["theta"])
        table["x0"], table["x1"] = table["x"] - L / 2 * c, table["x"] + L / 2 * c
        table["y0"], table["y1"] = table["y"] - L / 2 * s, table["y"] + L / 2 * s
        return table

    def product_clicked(self, index):
        typ, name, opis = self.products[index.row()]
        self.show_product(typ, name)
        self.goto_product(typ, name)

    # ------------------------------------------------------------------ UI

    def mk_params(self, grid, w, func, label=True):
        # pola parametrow metody FFS: nazwy i wartosci domyslne z sygnatury, podpowiedzi z docstringu
        name = "FFS" if func.__name__ == "__init__" else func.__name__
        docs = doc_params(FFS if name == "FFS" else func)
        self.params[name] = {}
        if label:
            l = QLabel("<i>%s</i>" % name)
            l.setToolTip(tooltip(name, doc_summary(func)))
            grid.addWidget(l, w, 0, 1, 4)
            w = w + 1
        col = 0
        for p in list(inspect.signature(func).parameters.values())[1:]:     # bez self
            if p.name == "image": continue
            default = self.defaults.get((name, p.name), p.default)
            typ, opis = docs.get(p.name, ["", ""])
            if isinstance(default, bool):
                e = QCheckBox()
                e.setChecked(default)
            elif isinstance(default, tuple):              # exclude: nazwy masek pomijanych (bad_mask)
                e = QToolButton()
                e.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
                menu = QMenu(e)
                menu.setToolTipsVisible(True)             # opis maski (masks_description) w podpowiedzi
                # zle piksele i zrodla (FFS.EXCLUDE_ALL), przelania ladunku i domyslne spoza tej listy;
                # inne maski obiektu FFS (np. wczytane z zewnatrz) dochodza przy otwarciu menu
                for n in dict.fromkeys(FFS.EXCLUDE_ALL + self.EXTRA_EXCLUDE + tuple(default)):
                    self.add_exclude_action(e, menu, n, n in default)
                menu.aboutToShow.connect(lambda e=e: self.add_mask_actions(e))
                e.setMenu(menu)
                self.exclude_text(e)
                opis = opis + "\nDefault: " + ", ".join(default)
            elif typ.startswith("{"):
                e = QComboBox()
                e.addItems(re.findall(r'"([^"]+)"', typ))
                e.setCurrentText(str(default))
            else:
                e = QLineEdit(str(default))
                e.setMaximumWidth(80)
            l = QLabel(p.name.replace("_", " ") + ":")       # dlugie nazwy zawijane; prawdziwa nazwa w podpowiedzi
            l.setWordWrap(True)
            l.setMaximumWidth(110)
            for x in [l, e]: x.setToolTip(tooltip("%s  (%s)" % (p.name, typ), opis))
            self.params[name][p.name] = e
            grid.addWidget(l, w, col)
            grid.addWidget(e, w, col + 1)
            col = col + 2
            if col >= 4:
                col = 0
                w = w + 1
        if col > 0: w = w + 1
        return w

    def mk_page(self, funcs):
        # zakladka z parametrami jednego etapu
        page = QWidget()
        grid = QGridLayout()
        w = 0
        for f in funcs:
            w = self.mk_params(grid, w, f, label=len(funcs) > 1)
        grid.setRowStretch(w, 1)
        page.setLayout(grid)
        # przewijana: strona Lines ma ~600 px wysokosci i bez przewijania okno FFS nie miescilo sie na laptopie
        scroll = QScrollArea()
        scroll.setWidget(page)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMinimumWidth(page.minimumSizeHint().width() + scroll.verticalScrollBar().sizeHint().width())
        return scroll

    def mk_button(self, title, funcs, stage):
        p = QPushButton(title)
        p.setToolTip(tooltip(title, "\n\n".join(doc_summary(f) for f in funcs)))
        p.clicked.connect(lambda: self.run(stage))
        return p

    def mkUI(self):
        self.setWindowTitle('FFS')

        self.info_l = QLabel()


        frame = [FFS.__init__, FFS.mk_bleeds_mask, FFS.mk_stats]
        sky = [FFS.sky_map]
        cosmics = [FFS.mk_cosmics_mask]
        lines = [FFS.mk_threshold_mask, FFS.mk_ring_mask, FFS.hough_transform, FFS.find_lines,
                 FFS.classify_lines]
        stars = [FFS.find_stars, FFS.star_info, FFS.calc_star_stats, FFS.mk_stars_mask]
        psf = [FFS.mk_star_maps, FFS.calc_star_field_stats]
        fft = [power_spectrum]
        calib = [FFS.mk_columns_map, FFS.mk_bad_columns_mask, FFS.mk_pixels_map, FFS.mk_hot_pixels_mask, FFS.mk_cold_pixels_mask]

        self.params_t = QTabWidget()
        self.params_t.addTab(self.mk_page(frame), "Frame")
        self.params_t.addTab(self.mk_page(sky), "Sky")
        self.params_t.addTab(self.mk_page(cosmics), "Cosmics")
        self.params_t.addTab(self.mk_page(lines), "Lines")
        self.params_t.addTab(self.mk_page(stars), "Stars")
        self.params_t.addTab(self.mk_page(psf), "PSF")
        self.params_t.addTab(self.mk_page(calib), "Calib.")
        self.params_t.addTab(self.mk_page(fft), "FFT")
        self.params_t.setTabToolTip(0, tooltip("FFS", doc_summary(FFS)))

        # kazdy przycisk to jeden krok na biezacym obiekcie FFS (uzywa masek z poprzednich krokow)
        buttons = QGridLayout()
        buttons.addWidget(self.mk_button("Statistics", frame, "stats"), 0, 0)
        buttons.addWidget(self.mk_button("Sky", sky, "sky"), 0, 1)
        buttons.addWidget(self.mk_button("Cosmics", cosmics, "cosmics"), 0, 2)
        buttons.addWidget(self.mk_button("Find lines", lines, "lines"), 1, 0)
        buttons.addWidget(self.mk_button("Find stars", stars, "stars"), 1, 1)
        buttons.addWidget(self.mk_button("PSF field", psf, "psf"), 1, 2)
        buttons.addWidget(self.mk_button("Calibration", calib, "calibration"), 2, 0)
        run_all = QPushButton("Run all")
        run_all.setToolTip(tooltip("Run all", "New FFS, then: " + ", ".join(self.RUN_ALL) +
                                   "\n\nThe last sky and stats use all masks (cosmics, lines, spikes, stars)."))
        run_all.clicked.connect(lambda: self.run("all"))
        buttons.addWidget(run_all, 3, 1)                 # Run fast i Run all obok siebie
        buttons.addWidget(self.mk_button("Fourier", fft, "fft"), 2, 1)
        toi = QPushButton("Run fast")
        toi.setToolTip(tooltip("Run fast", "FFS.calc_frame_fwhm as TOI does it on every science/snap/focus frame: new FFS on the whole frame "
                               "(saturation by telescope: jk15 150000, else 45000; autobin), calc_frame_fwhm(threshold=10, "
                               "fwhm=5, box=15, N_stars=50), sky_gradient(n_segments=7), calc_star_field_stats(). "
                               "Marked as in TOI with ordinary tables: lines, and the star table twice with a column range "
                               "condition (stars rejected - red squares, stars saturated - red circles). Summary as the TOI "
                               "panel in the log."))
        toi.clicked.connect(lambda: self.run("fast"))
        buttons.addWidget(toi, 3, 0)
        reset = QPushButton("Reset")
        reset.setToolTip(tooltip("Reset", "New cut-out from the current view of the image and new FFS: "
                                 "all masks and maps are dropped, then Statistics."))
        reset.clicked.connect(self.reset_pushed)
        buttons.addWidget(reset, 2, 2)
        self.save_p = QPushButton("Save MEF")
        self.save_p.setToolTip(tooltip("Save MEF", doc_summary(FFS.save_mef) + "\n\nResults of the last run, in cut-out coordinates (FFCUTX0, FFCUTY0 in the header)."))
        self.save_p.clicked.connect(self.save_pushed)
        buttons.addWidget(self.save_p, 3, 2)

        self.stats_t = QTableWidget(0, 2)
        self.stats_t.setHorizontalHeaderLabels(["frame", "value"])
        self.stats_t.verticalHeader().hide()
        self.stats_t.horizontalHeader().setStretchLastSection(True)
        self.stats_t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.products_t = QTableWidget(0, 4)
        self.products_t.setHorizontalHeaderLabels(["shown", "type", "name", "step"])
        self.products_t.verticalHeader().hide()
        self.products_t.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.products_t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.products_t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.products_t.doubleClicked.connect(self.product_clicked)
        self.products_t.itemChanged.connect(self.product_checked)
        self.products_t.setToolTip("shown (or double click): open as a tab (masks are also drawn on the image); "
                                   "step: in which step the product was made or last changed")

        self.delete_p = QPushButton("Delete")
        self.delete_p.setToolTip("Delete the selected products from FFS (later steps do not use them) and hide their tabs")
        self.delete_p.clicked.connect(self.delete_pushed)

        self.pole_e = QTextEdit()
        self.pole_e.setReadOnly(True)
        # log nie rozpycha okna (domyslnie chcial ~200 px i parametry dostawaly kilka wierszy)
        self.pole_e.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        self.pole_e.setMinimumHeight(4 * self.pole_e.fontMetrics().lineSpacing())

        self.cl_p = QPushButton('Close', self)
        self.cl_p.clicked.connect(self.close_window)

        grid = QGridLayout()
        grid.addWidget(self.info_l, 0, 0, 1, 3)
        grid.addWidget(self.params_t, 1, 0, 2, 1)
        grid.addLayout(buttons, 3, 0)
        grid.addWidget(self.pole_e, 4, 0)
        grid.addWidget(self.stats_t, 1, 1, 1, 2)
        grid.addWidget(self.products_t, 2, 1, 2, 2)
        grid.addWidget(self.delete_p, 4, 2, Qt.AlignmentFlag.AlignTop)
        grid.addWidget(self.cl_p, 5, 2)
        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 2)
        grid.setRowStretch(1, 2)
        grid.setRowStretch(2, 2)
        grid.setRowStretch(4, 1)
        self.setLayout(grid)

        init_panel(self, self.parent, "ffs", "FFS", 850, 650)

    def update(self):
        show_panel(self)
        self.pole_e.append(self.txt)
        self.parent.activateWindow()

    def close_window(self):
        close_panel(self)