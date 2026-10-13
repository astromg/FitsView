#!/usr/bin/env python3

# Zakladki z mapami i maskami (np. z FFS): parent.map_data / parent.mask_data,
# tak jak Catalog dla parent.table_data. Dane zawsze w ukladzie i rozmiarze oryginalu
# (jak self.dane w Image); flip / rot90 tylko przy wyswietlaniu.

import numpy

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from PyQt5.QtWidgets import QWidget, QLabel, QCheckBox, QLineEdit, QPushButton, QGridLayout, QComboBox

from fitsview.FitsView_catalog import ColorButton


class MapTab(QWidget):
    def __init__(self,parent,data_index):
        QWidget.__init__(self)
        self.parent = parent
        self.data_index = data_index
        self.limits = None                 # widok (zoom toolbara) zachowany miedzy update()

        self.mkUI()
        self.clim_auto()

        self.cmap_s.currentIndexChanged.connect(self.update)
        self.min_e.editingFinished.connect(self.update)
        self.max_e.editingFinished.connect(self.update)
        self.auto_p.clicked.connect(self.auto_pushed)

    def zestaw(self):
        return self.parent.map_data[self.data_index]

    def clim_auto(self):
        dane = numpy.asarray(self.zestaw()["data"], dtype=float)
        dane = dane[numpy.isfinite(dane)]
        if dane.size == 0: dane = numpy.array([0., 1.])
        a, b = numpy.percentile(dane, [0.5, 99.5])
        if a == b: b = a + 1
        self.min_e.setText("%.4g"%a)
        self.max_e.setText("%.4g"%b)

    def auto_pushed(self):
        self.clim_auto()
        self.update()

    def get_clim(self):
        try: return float(self.min_e.text()), float(self.max_e.text())
        except ValueError: return None, None

    def show_data(self,dane):
        vmin, vmax = self.get_clim()
        image = self.axes.imshow(dane, origin="lower", cmap=self.cmap_s.currentText(), vmin=vmin, vmax=vmax, interpolation="none")
        self.fig.colorbar(image, ax=self.axes)

    def update(self):
        zestaw = self.zestaw()
        self.desc_l.setText(zestaw["name"] + ": " + str(zestaw["description"]))

        rot90 = bool(self.parent.cfg_rot90)
        dane = zestaw["data"]
        if rot90: dane = numpy.rot90(dane)

        # zoom z toolbara zostaje, chyba ze zmienil sie obrot
        if self.limits is not None and self.limits[0] == rot90:
            x1, x2 = sorted(self.axes.get_xlim())
            y1, y2 = sorted(self.axes.get_ylim())
        elif zestaw.get("view") is not None:                   # poczatkowy widok, np. wycinek FFS
            x1, x2, y1, y2 = zestaw["view"]
            if rot90:                                           # oryginal -> ekran, jak Image.to_screen
                nx = zestaw["data"].shape[1]
                x1, x2, y1, y2 = y1, y2, nx - 1 - x2, nx - 1 - x1
        else:
            x1, x2 = -0.5, dane.shape[1] - 0.5
            y1, y2 = -0.5, dane.shape[0] - 0.5
        self.limits = (rot90,)

        self.fig.clear()
        self.axes = self.fig.add_subplot(111)
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.show_data(dane)

        if self.parent.cfg_flipX: self.axes.set_xlim(x2, x1)
        else: self.axes.set_xlim(x1, x2)
        if self.parent.cfg_flipY: self.axes.set_ylim(y2, y1)
        else: self.axes.set_ylim(y1, y2)

        self.canvas.draw()

    def mouse_move(self,event):
        if event.inaxes != self.axes or event.xdata is None: return
        dane = self.zestaw()["data"]
        ny, nx = dane.shape
        x, y = event.xdata, event.ydata
        if self.parent.cfg_rot90: x, y = nx - 1 - y, x          # ekran -> oryginal, jak Image.to_orig
        i, j = int(round(y)), int(round(x))
        if 0 <= i < ny and 0 <= j < nx:
            self.coor_l.setText("x=%.1f y=%.1f  value=%.4g" % (x, y, dane[i, j]))

    def mkUI(self):
        self.desc_l = QLabel()
        self.desc_l.setWordWrap(True)

        self.fig = Figure(linewidth=-1, dpi=100, tight_layout=True, frameon=False)
        self.canvas = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.canvas.mpl_connect('motion_notify_event', self.mouse_move)

        self.coor_l = QLabel()

        self.cmap_l = QLabel("Cmap: ")
        self.cmap_s = QComboBox()
        self.cmap_s.addItems(['viridis', 'gray', 'binary', 'gist_heat', 'seismic'])

        self.min_l = QLabel("min: ")
        self.min_e = QLineEdit()
        self.max_l = QLabel("max: ")
        self.max_e = QLineEdit()
        self.auto_p = QPushButton("Auto")

        grid = QGridLayout()
        w = 0
        grid.addWidget(self.desc_l, w, 0, 1, 8)
        w = w + 1
        grid.addWidget(self.canvas, w, 0, 1, 8)
        w = w + 1
        grid.addWidget(self.toolbar, w, 0, 1, 8)
        w = w + 1
        grid.addWidget(self.coor_l, w, 0, 1, 2)
        grid.addWidget(self.cmap_l, w, 2)
        grid.addWidget(self.cmap_s, w, 3)
        grid.addWidget(self.min_l, w, 4)
        grid.addWidget(self.min_e, w, 5)
        grid.addWidget(self.max_l, w, 6)
        grid.addWidget(self.max_e, w, 7)
        w = w + 1
        grid.addWidget(self.auto_p, w, 7)
        self.grid = grid
        self.setLayout(grid)
        grid.setRowStretch(1, 1)


class MaskTab(MapTab):
    # maska: obraz 0/1 bez skali kolorow, plus ustawienia rysowania na Image (jak w Catalog)
    def __init__(self,parent,data_index):
        MapTab.__init__(self,parent,data_index)

        zestaw = self.zestaw()
        self.plot_c.setChecked(bool(zestaw["plot_image"]))
        self.style_s.setCurrentText(zestaw["style"])

        self.plot_c.stateChanged.connect(self.update_data)
        self.style_s.currentTextChanged.connect(self.update_data)
        self.mkcolor_p.clicked.connect(self.update_data)

    def zestaw(self):
        return self.parent.mask_data[self.data_index]

    def clim_auto(self):
        self.min_e.setText("0")
        self.max_e.setText("1")

    def show_data(self,dane):
        self.axes.imshow(dane, origin="lower", cmap="gray", vmin=0, vmax=1, interpolation="none")

    def update(self):
        dane = self.zestaw()["data"]
        n = int(numpy.sum(dane))
        self.count_l.setText("%d pixels (%.3f %%)" % (n, 100. * n / dane.size))
        MapTab.update(self)

    def update_data(self):
        zestaw = self.zestaw()
        zestaw["plot_image"] = self.plot_c.isChecked()
        zestaw["color"] = self.mkcolor_p.color()
        zestaw["style"] = self.style_s.currentText()
        self.parent.update_overlays()

    def mkUI(self):
        MapTab.mkUI(self)
        for x in [self.cmap_l, self.cmap_s, self.min_l, self.min_e, self.max_l, self.max_e, self.auto_p]:
            x.hide()

        self.count_l = QLabel()
        self.plot_c = QCheckBox("Plot on Image")
        self.style_l = QLabel("Style: ")
        self.style_s = QComboBox()
        self.style_s.addItems(["contour", "fill"])
        self.mkcolor_l = QLabel("Color: ")
        self.mkcolor_p = ColorButton(initial_color=self.parent.mask_data[self.data_index]["color"])

        w = 3
        self.grid.addWidget(self.count_l, w, 2, 1, 2)
        w = w + 1
        self.grid.addWidget(self.plot_c, w, 0)
        self.grid.addWidget(self.style_l, w, 2)
        self.grid.addWidget(self.style_s, w, 3)
        self.grid.addWidget(self.mkcolor_l, w, 4)
        self.grid.addWidget(self.mkcolor_p, w, 5)
