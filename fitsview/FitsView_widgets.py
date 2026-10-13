#!/usr/bin/env python3
from PyQt5.QtCore import Qt
from astropy.io.misc.asdf.tags.helpers import skycoord_equal
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QTextEdit, QLineEdit, QPushButton, \
    QGridLayout, QHBoxLayout, QVBoxLayout, QComboBox, QCheckBox, QTableWidget, \
    QTableWidgetItem, QApplication, QTabWidget, QToolButton, QMenu, QFileDialog, QHeaderView
from PyQt5 import QtCore

import numpy as np
import numpy
import inspect, re, html, traceback

from astropy.table import Table
from astropy.io import fits

from pyaraucaria.ffs import FFS

class HeaderTabLocal(QWidget):
   def __init__(self,parent,header): 
       QWidget.__init__(self)
       self.setWindowFlag(Qt.Tool)
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
       self.update()
       gm=eval(self.parent.parent.cfg_geometry)
       self.setGeometry(int(gm[1])+50,int(gm[1]+50),600,600)

       

   def update(self):     
       hdr=repr(self.header)
       hdr=hdr.split("\n")
       text=self.filter_e.text()
       txt=""
       for x in hdr:
           if str(text).lower() in str(x).lower(): txt=txt+str(x)+"\n"
       self.heder_e.setText(txt) 
       self.show()


   def close_window(self): 
       self.close()     

class TextWindow(QWidget):
  def __init__(self,parent):
      QWidget.__init__(self)
      self.setWindowFlag(Qt.Tool)
      self.parent=parent
      self.setWindowTitle('Querry')
      
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
         
      self.pole.setReadOnly(1)
#      self.pole.setLineWrapMode(0)
      gm=eval(self.parent.parent.cfg_geometry)
      self.setGeometry(int(gm[1])+int(gm[2])+10,int(gm[1]),400,500)
  def update(self):
      self.show()
      self.pole.append(self.txt)
      self.parent.activateWindow()
      
  def close_window(self):     
      self.close()      

class PlotWindow(QWidget):
    def __init__(self,parent):
        QWidget.__init__(self)
        self.setWindowFlag(Qt.Tool)
        self.parent=parent
        self.setWindowTitle('Plot')
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

        self.pole.setReadOnly(1)
        self.toolbar.hide()
        self.show()
        gm=eval(self.parent.parent.cfg_geometry)
        self.setGeometry(int(gm[1])+int(gm[2])+10,int(gm[1]+200),400,400)

    def update(self):
        self.show()
        self.pole.setText(self.txt)
        self.parent.activateWindow()

    def close_window(self):
        self.close()
        self.parent.update()

    def resizeEvent(self, event):
        if float(self.frameGeometry().width()) > 700 and float(self.frameGeometry().height()) > 500:
            self.toolbar.show()
        else:
            self.toolbar.hide()
        QMainWindow.resizeEvent(self, event)


class FigureWindow(QWidget):
    def __init__(self,parent):
        QWidget.__init__(self)
        self.setWindowFlag(Qt.Tool)
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
        self.pole.setReadOnly(1)

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

        self.show()
        gm=eval(self.parent.parent.cfg_geometry)
        self.setGeometry(int(gm[1])+int(gm[2])+10,int(gm[1]+200),500,400)

    def update(self):

        self.axes.clear()

        self.axes.set_xlabel(self.xcol_s.currentText())
        self.axes.set_ylabel(self.ycol_s.currentText())

        x = self.parent.data[self.xcol_s.currentText()]
        y = self.parent.data[self.ycol_s.currentText()]

        self.axes.plot(x,y,".b")

        self.canvas.draw()

        self.show()
        #self.pole.setText(self.txt)
        self.parent.activateWindow()

    def close_window(self):
        self.close()
        self.parent.update()

    def resizeEvent(self, event):
        if float(self.frameGeometry().width()) > 700 and float(self.frameGeometry().height()) > 500:
            self.toolbar.show()
        else:
            self.toolbar.hide()
        QMainWindow.resizeEvent(self, event)

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
    TABLES = {"sky segments": "sky", "lines": "lines", "stars": "stars", "psf grid": "psf_grid"}
    # Run all: kolejnosc jak FFS.calc_frame_fwhm, na koniec tlo i statystyki jeszcze raz, juz z maskami
    RUN_ALL = ["stats", "sky", "cosmics", "lines", "stars", "sky", "stats", "psf"]

    def __init__(self, parent, image, saturation=None,dx=0,dy=0):
        QWidget.__init__(self)          # zwykle okno (nie Qt.Tool), zeby nie zaslanialo glownego
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
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.changed = set()
            if stage == "all" or self.ffs is None:
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

    def reset_pushed(self):
        # nowy wycinek z aktualnego widoku obrazu
        self.image, self.dx, self.dy = self.parent.ffs_cut()
        self.initFFS()

    def reset_ffs(self):
        # nowy obiekt FFS z parametrami konstruktora (zakladka Frame); maski i mapy od zera
        self.ffs_params = self.get_params("FFS")
        self.ffs = FFS(self.image, **self.ffs_params)
        self.ffs.mk_saturation_mask()
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
        return out

    def step(self, stage):
        # jeden krok na biezacym obiekcie FFS
        ffs = self.ffs
        for name in self.DROP.get(stage, ()):
            ffs.masks.pop(name, None)
        if stage == "stats":
            ffs.mk_stats(**self.get_params("mk_stats"))     # wyniki innych krokow (fwhm, psf_*) zostaja
        if stage == "sky":
            ffs.sky_map(**self.get_params("sky_map"))
        if stage == "cosmics":
            ffs.mk_cosmics_mask(**self.get_params("mk_cosmics_mask"))
        if stage == "lines":
            ffs.mk_threshold_mask(**self.get_params("mk_threshold_mask"))
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
            txt_v = "%d" % v if isinstance(v, (int, numpy.integer)) else "%.4g" % v    # n_excluded, used_stars
            for j, txt in enumerate([k, txt_v]):
                item = QTableWidgetItem(txt)
                item.setToolTip(tooltip(k, opis))
                self.stats_t.setItem(i, j, item)
        self.stats_t.resizeColumnsToContents()

        self.update_products()

        # tabele gwiazd i linii od razu na Image, reszta na zadanie
        if stage in ("lines", "all") and ffs.lines is not None:
            self.show_product("table", "lines")
        if stage in ("stars", "all") and ffs.stars is not None:
            self.show_product("table", "stars")
        if stage in ("stars", "all") and "fwhm" in ffs.stats["frame"]:
            self.pole_e.append("frame_fwhm: %.2f  ellipticity: %.2f  used_stars: %d" % (
                ffs.stats["frame"]["fwhm"], ffs.stats["frame"]["ellipticity"], ffs.stats["frame"]["used_stars"]))

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
        if ffs.lines is not None: self.products.append(("table", "lines", "Detected lines (find_lines, classify_lines)"))
        if ffs.stars is not None: self.products.append(("table", "stars", "Detected stars; not measured have NaN (find_stars, star_info)"))
        if ffs.psf_grid is not None: self.products.append(("table", "psf grid", "PSF on a grid, drawn as whiskers: direction theta, length ~ ellipticity, the longest 0.9 of a cell (mk_star_maps)"))

        self.products_t.blockSignals(True)
        self.products_t.setRowCount(len(self.products))
        for i, (typ, name, opis) in enumerate(self.products):
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item.setCheckState(Qt.Checked if self.shown(typ, name) else Qt.Unchecked)
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
        lista = {"mask": gui.mask_data, "map": gui.map_data, "table": gui.table_data}[typ]
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
        if item.checkState() == Qt.Checked: self.show_product(typ, name)
        else: self.hide_product(typ, name)
        self.update_products()

    def delete_pushed(self):
        # usuwa zaznaczone produkty z obiektu FFS (kolejne kroki ich nie uzywaja) i chowa ich zakladki
        rows = sorted(set(i.row() for i in self.products_t.selectedIndexes()))
        names = []
        for i in rows:
            typ, name, opis = self.products[i]
            self.hide_product(typ, name)
            if typ == "mask": self.ffs.masks.pop(name, None)
            elif typ == "map": self.ffs.maps.pop(name, None)
            else: setattr(self.ffs, self.TABLES[name], None)
            self.product_step.pop((typ, name), None)
            names.append("%s %s" % (name, typ))
        if names: self.pole_e.append("deleted: " + ", ".join(names))
        self.update_products()

    def tab_name(self, typ, name):
        # np. maska "lines" i tabela "lines" musza miec rozne zakladki
        if typ == "table": return "ffs." + name
        return "ffs.%s %s" % (name, typ)

    def show_product(self, typ, name):
        gui = self.parent.parent
        ffs = self.ffs
        if typ == "mask":
            gui.add_mask(self.full_frame(ffs.masks[name], False), name=self.tab_name(typ, name), description=ffs.masks_description.get(name, ""))
        elif typ == "map":
            gui.add_map(self.full_frame(ffs.maps[name], numpy.nan), name=self.tab_name(typ, name), description=ffs.maps_description.get(name, ""))
        elif typ == "table":
            table = {"sky segments": ffs.sky, "lines": ffs.lines, "stars": ffs.stars, "psf grid": ffs.psf_grid}[name]
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
                e.setPopupMode(QToolButton.InstantPopup)
                menu = QMenu(e)
                for n in FFS.EXCLUDE_ALL:
                    a = menu.addAction(n)
                    a.setCheckable(True)
                    a.setChecked(n in default)
                    a.toggled.connect(lambda checked, e=e: self.exclude_text(e))
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
        return page

    def mk_button(self, title, funcs, stage):
        p = QPushButton(title)
        p.setToolTip(tooltip(title, "\n\n".join(doc_summary(f) for f in funcs)))
        p.clicked.connect(lambda: self.run(stage))
        return p

    def mkUI(self):
        self.setWindowTitle('FFS')

        self.info_l = QLabel()


        frame = [FFS.__init__, FFS.mk_stats]
        sky = [FFS.sky_map]
        cosmics = [FFS.mk_cosmics_mask]
        lines = [FFS.mk_threshold_mask, FFS.find_lines, FFS.classify_lines]
        stars = [FFS.find_stars, FFS.star_info, FFS.calc_star_stats, FFS.mk_stars_mask]
        psf = [FFS.mk_star_maps, FFS.calc_star_field_stats]
        calib = [FFS.mk_columns_map, FFS.mk_bad_columns_mask, FFS.mk_pixels_map, FFS.mk_hot_pixels_mask, FFS.mk_cold_pixels_mask]

        self.params_t = QTabWidget()
        self.params_t.addTab(self.mk_page(frame), "Frame")
        self.params_t.addTab(self.mk_page(sky), "Sky")
        self.params_t.addTab(self.mk_page(cosmics), "Cosmics")
        self.params_t.addTab(self.mk_page(lines), "Lines")
        self.params_t.addTab(self.mk_page(stars), "Stars")
        self.params_t.addTab(self.mk_page(psf), "PSF")
        self.params_t.addTab(self.mk_page(calib), "Calib.")
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
        buttons.addWidget(run_all, 2, 1)
        reset = QPushButton("Reset")
        reset.setToolTip(tooltip("Reset", "New cut-out from the current view of the image and new FFS: "
                                 "all masks and maps are dropped, then Statistics."))
        reset.clicked.connect(self.reset_pushed)
        buttons.addWidget(reset, 3, 0)
        self.save_p = QPushButton("Save MEF")
        self.save_p.setToolTip(tooltip("Save MEF", doc_summary(FFS.save_mef) + "\n\nResults of the last run, in cut-out coordinates (FFCUTX0, FFCUTY0 in the header)."))
        self.save_p.clicked.connect(self.save_pushed)
        buttons.addWidget(self.save_p, 3, 2)

        self.stats_t = QTableWidget(0, 2)
        self.stats_t.setHorizontalHeaderLabels(["frame", "value"])
        self.stats_t.verticalHeader().hide()
        self.stats_t.horizontalHeader().setStretchLastSection(True)
        self.stats_t.setEditTriggers(QTableWidget.NoEditTriggers)

        self.products_t = QTableWidget(0, 4)
        self.products_t.setHorizontalHeaderLabels(["shown", "type", "name", "step"])
        self.products_t.verticalHeader().hide()
        self.products_t.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.products_t.setEditTriggers(QTableWidget.NoEditTriggers)
        self.products_t.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_t.doubleClicked.connect(self.product_clicked)
        self.products_t.itemChanged.connect(self.product_checked)
        self.products_t.setToolTip("shown (or double click): open as a tab (masks are also drawn on the image); "
                                   "step: in which step the product was made or last changed")

        self.delete_p = QPushButton("Delete")
        self.delete_p.setToolTip("Delete the selected products from FFS (later steps do not use them) and hide their tabs")
        self.delete_p.clicked.connect(self.delete_pushed)

        self.pole_e = QTextEdit()
        self.pole_e.setReadOnly(1)

        self.cl_p = QPushButton('Close', self)
        self.cl_p.clicked.connect(self.close_window)

        grid = QGridLayout()
        grid.addWidget(self.info_l, 0, 0, 1, 3)
        grid.addWidget(self.params_t, 1, 0, 2, 1)
        grid.addLayout(buttons, 3, 0)
        grid.addWidget(self.pole_e, 4, 0)
        grid.addWidget(self.stats_t, 1, 1, 1, 2)
        grid.addWidget(self.products_t, 2, 1, 2, 2)
        grid.addWidget(self.delete_p, 4, 2, QtCore.Qt.AlignTop)
        grid.addWidget(self.cl_p, 5, 2)
        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 2)
        grid.setRowStretch(1, 1)
        grid.setRowStretch(2, 1)
        self.setLayout(grid)

        gm = eval(self.parent.parent.cfg_geometry)
        self.setGeometry(int(gm[1]) + int(gm[2]) + 10, int(gm[1]), 850, 650)

    def update(self):
        self.show()
        self.pole_e.append(self.txt)
        self.parent.activateWindow()

    def close_window(self):
        self.hide()