#!/usr/bin/env python3
from PyQt5.QtCore import Qt
from astropy.io.misc.asdf.tags.helpers import skycoord_equal
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QTextEdit, QLineEdit, QPushButton, \
    QGridLayout, QHBoxLayout, QVBoxLayout, QComboBox, QCheckBox, QTableWidget, \
    QTableWidgetItem, QApplication, QTabWidget
from PyQt5 import QtCore

import numpy as np
import numpy
import inspect, re, html, traceback

from astropy.table import Table

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
    # nadpisane w self.defaults), podpowiedzi z ich docstringow. Kazdy przycisk liczy od nowa
    # caly ciag krokow do swojego etapu, w kolejnosci jak FFS.calc_frame_fwhm():
    # saturacja, statystyki, tlo, kosmiki, linie, gwiazdy. Wyniki (maski, mapy, tabele) sa
    # przenoszone do pelnej klatki; maski i mapy otwierane na zadanie ("Show").

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
            ("star_info", "N_stars"): 20,               # statystyki klatki z 20 najjasniejszych
            ("mk_bad_columns_mask", "threshold"): 5,
            ("mk_hot_pixels_mask", "threshold"): 50,
            ("mk_cold_pixels_mask", "threshold"): 50,
        }

        self.txt = ""
        self.ffs = None
        self.params = {}
        self.products = []

        self.mkUI()
        self.initFFS()

    def initFFS(self):
        h, w = self.image.shape
        self.info_l.setText("cut: %d x %d px at x=%d, y=%d" % (w, h, int(self.dx), int(self.dy)))
        self.run("stats")

    # ------------------------------------------------------------------ liczenie

    def get_params(self, name):
        out = {}
        for k, e in self.params[name].items():
            if isinstance(e, QCheckBox): out[k] = e.isChecked()
            elif isinstance(e, QComboBox): out[k] = e.currentText()
            else: out[k] = to_value(e.text())
        return out

    def run(self, stage):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            ffs = FFS(self.image, **self.get_params("FFS"))
            ffs.mk_saturation_mask()
            ffs.mk_stats()
            if stage != "stats":
                ffs.sky_map(**self.get_params("sky_map"))
            if stage == "cosmics" or (stage in ("lines", "stars") and self.cosmics_c.isChecked()):
                ffs.mk_cosmics_mask(**self.get_params("mk_cosmics_mask"))
            if stage == "lines" or (stage == "stars" and self.lines_c.isChecked()):
                ffs.mk_threshold_mask(**self.get_params("mk_threshold_mask"))
                ffs.find_lines(**self.get_params("find_lines"))
                ffs.classify_lines(**self.get_params("classify_lines"))
            if stage == "stars":
                ffs.find_stars(**self.get_params("find_stars"))
                ffs.star_info(**self.get_params("star_info"))
                ffs.calc_star_stats(**self.get_params("calc_star_stats"))
                # katalog: wszystkie gwiazdy; star_info zostawia w coo tylko zmierzone, wiec find_stars od nowa
                ffs.find_stars(**self.get_params("find_stars"))
                ffs.star_info(box=self.get_params("star_info")["box"], N_stars=None)
            if stage == "calibration":
                ffs.mk_columns_map(**self.get_params("mk_columns_map"))
                ffs.mk_bad_columns_mask(**self.get_params("mk_bad_columns_mask"))
                ffs.mk_pixels_map(**self.get_params("mk_pixels_map"))
                ffs.mk_hot_pixels_mask(**self.get_params("mk_hot_pixels_mask"))
                ffs.mk_cold_pixels_mask(**self.get_params("mk_cold_pixels_mask"))
        except Exception as e:
            QApplication.restoreOverrideCursor()
            traceback.print_exc()
            self.pole_e.append("ERROR in %s: %s" % (stage, e))
            return
        QApplication.restoreOverrideCursor()

        self.ffs = ffs
        self.pole_e.append("%s done (bin %d)" % (stage, ffs.bin))
        self.show_results(stage)

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
            for j, txt in enumerate([k, "%.4g" % v]):
                item = QTableWidgetItem(txt)
                item.setToolTip(tooltip(k, opis))
                self.stats_t.setItem(i, j, item)
        self.stats_t.resizeColumnsToContents()

        # (typ, nazwa, opis); tabele gwiazd i linii od razu na Image, reszta na zadanie
        self.products = []
        for k in ffs.masks: self.products.append(("mask", k, ffs.masks_description.get(k, "")))
        for k in ffs.maps: self.products.append(("map", k, ffs.maps_description.get(k, "")))
        if ffs.sky is not None: self.products.append(("table", "sky segments", "Sky segments: centres and fitted background (sky_gradient)"))
        if ffs.lines is not None: self.products.append(("table", "lines", "Detected lines (find_lines, classify_lines)"))
        if ffs.stars is not None: self.products.append(("table", "stars", "Measured stars (find_stars, star_info)"))

        self.products_t.setRowCount(len(self.products))
        for i, (typ, name, opis) in enumerate(self.products):
            for j, txt in enumerate([typ, name]):
                item = QTableWidgetItem(txt)
                item.setToolTip(tooltip(name, opis))
                self.products_t.setItem(i, j, item)
        self.products_t.resizeColumnsToContents()

        if stage in ("lines", "stars") and ffs.lines is not None:
            self.show_product("table", "lines")
        if stage == "stars":
            self.show_product("table", "stars")
            self.pole_e.append("frame_fwhm: %.2f  ellipticity: %.2f  used_stars: %d" % (
                ffs.stats["frame"]["fwhm"], ffs.stats["frame"]["ellipticity"], ffs.stats["frame"]["used_stars"]))

        # juz otwarte zakladki z poprzedniego przebiegu - odswiezamy
        gui = self.parent.parent
        for typ, name, opis in self.products:
            if typ == "mask" and gui.find_data(gui.mask_data, self.tab_name(typ, name)) is not None: self.show_product(typ, name)
            if typ == "map" and gui.find_data(gui.map_data, self.tab_name(typ, name)) is not None: self.show_product(typ, name)

    def view(self):
        # wycinek w pelnej klatce (x1, x2, y1, y2): poczatkowy widok zakladek map i masek
        h, w = self.image.shape
        return (self.dx - 0.5, self.dx + w - 0.5, self.dy - 0.5, self.dy + h - 0.5)

    def tab_name(self, typ, name):
        # np. maska "lines" i tabela "lines" musza miec rozne zakladki
        if typ == "table": return "ffs." + name
        return "ffs.%s %s" % (name, typ)

    def show_product(self, typ, name):
        gui = self.parent.parent
        ffs = self.ffs
        if typ == "mask":
            gui.add_mask(self.full_frame(ffs.masks[name], False), name=self.tab_name(typ, name), description=ffs.masks_description.get(name, ""), view=self.view())
        elif typ == "map":
            gui.add_map(self.full_frame(ffs.maps[name], numpy.nan), name=self.tab_name(typ, name), description=ffs.maps_description.get(name, ""), view=self.view())
        elif typ == "table":
            table = {"sky segments": ffs.sky, "lines": ffs.lines, "stars": ffs.stars}[name]
            gui.add_coo(self.shift_table(table), name=self.tab_name(typ, name))

    def show_pushed(self):
        rows = sorted(set(i.row() for i in self.products_t.selectedIndexes()))
        for i in rows:
            typ, name, opis = self.products[i]
            self.show_product(typ, name)

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

    def mk_page(self, funcs, use=None):
        # zakladka z parametrami jednego etapu; use - checkbox wlaczajacy etap w ciagu krokow
        page = QWidget()
        grid = QGridLayout()
        w = 0
        if use is not None:
            grid.addWidget(use, w, 0, 1, 4)
            w = w + 1
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

        self.cosmics_c = QCheckBox("mask cosmics before lines and stars")
        self.cosmics_c.setChecked(True)
        self.lines_c = QCheckBox("find (and mask) lines before stars")
        self.lines_c.setChecked(True)

        frame = [FFS.__init__]
        sky = [FFS.sky_map]
        cosmics = [FFS.mk_cosmics_mask]
        lines = [FFS.mk_threshold_mask, FFS.find_lines, FFS.classify_lines]
        stars = [FFS.find_stars, FFS.star_info, FFS.calc_star_stats]
        calib = [FFS.mk_columns_map, FFS.mk_bad_columns_mask, FFS.mk_pixels_map, FFS.mk_hot_pixels_mask, FFS.mk_cold_pixels_mask]

        self.params_t = QTabWidget()
        self.params_t.addTab(self.mk_page(frame), "Frame")
        self.params_t.addTab(self.mk_page(sky), "Sky")
        self.params_t.addTab(self.mk_page(cosmics, self.cosmics_c), "Cosmics")
        self.params_t.addTab(self.mk_page(lines, self.lines_c), "Lines")
        self.params_t.addTab(self.mk_page(stars), "Stars")
        self.params_t.addTab(self.mk_page(calib), "Calib.")
        self.params_t.setTabToolTip(0, tooltip("FFS", doc_summary(FFS)))

        # kazdy przycisk liczy od nowa wszystkie kroki do swojego etapu
        buttons = QGridLayout()
        buttons.addWidget(self.mk_button("Statistics", frame, "stats"), 0, 0)
        buttons.addWidget(self.mk_button("Sky", sky, "sky"), 0, 1)
        buttons.addWidget(self.mk_button("Cosmics", cosmics, "cosmics"), 0, 2)
        buttons.addWidget(self.mk_button("Find lines", lines, "lines"), 1, 0)
        buttons.addWidget(self.mk_button("Find stars", stars, "stars"), 1, 1)
        buttons.addWidget(self.mk_button("Calibration", calib, "calibration"), 1, 2)

        self.stats_t = QTableWidget(0, 2)
        self.stats_t.setHorizontalHeaderLabels(["frame", "value"])
        self.stats_t.verticalHeader().hide()
        self.stats_t.horizontalHeader().setStretchLastSection(True)
        self.stats_t.setEditTriggers(QTableWidget.NoEditTriggers)

        self.products_t = QTableWidget(0, 2)
        self.products_t.setHorizontalHeaderLabels(["type", "name"])
        self.products_t.verticalHeader().hide()
        self.products_t.horizontalHeader().setStretchLastSection(True)
        self.products_t.setEditTriggers(QTableWidget.NoEditTriggers)
        self.products_t.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_t.doubleClicked.connect(self.product_clicked)
        self.products_t.setToolTip("Double click or Show: open as a tab (masks are also drawn on the image)")

        self.show_p = QPushButton("Show")
        self.show_p.clicked.connect(self.show_pushed)

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
        grid.addWidget(self.show_p, 4, 2, QtCore.Qt.AlignTop)
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