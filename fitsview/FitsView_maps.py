#!/usr/bin/env python3

# Zakladki z mapami i maskami (np. z FFS): parent.map_data / parent.mask_data,
# tak jak Catalog dla parent.table_data. MapTab i MaskTab to ImageView (zoom, viewfinder,
# miniatura, flip / rot90, min/max, markery - jak Image) plus skala kolorow / ustawienia maski.
# Dane zawsze w ukladzie i rozmiarze oryginalu, jak self.dane w Image.

import matplotlib, numpy

from PyQt5.QtWidgets import QLabel, QCheckBox, QComboBox, QHBoxLayout

from fitsview import FitsView_image
from fitsview.FitsView_catalog import ColorButton


class MapTab(FitsView_image.ImageView):
    def __init__(self,parent,data_index):
        self.parent = parent                   # zestaw() potrzebny juz w ImageView.__init__
        self.data_index = data_index
        zestaw = self.zestaw()
        FitsView_image.ImageView.__init__(self,parent,self.mk_dane(zestaw["data"]))

        self.desc_l = QLabel(zestaw["name"] + ": " + str(zestaw["description"]))
        self.desc_l.setWordWrap(True)
        self.top_l.addWidget(self.desc_l)          # MaskTab wstawia swoje ustawienia nad opisem

    def zestaw(self):
        return self.parent.map_data[self.data_index]

    def mk_dane(self,data):
        # NaN zostaja (np. poza wycinkiem FFS) - na obrazie puste
        return numpy.array(data, dtype=float)

    def initiatie(self):
        FitsView_image.ImageView.initiatie(self)
        self.cmap_s.setCurrentText("viridis")

    def get_cmap(self):
        return matplotlib.colormaps[self.cmap_s.currentText()]

    def zmiana_cmap(self):
        self.update()                          # cmap tylko tej mapy, bez zmiany konfiguracji

    def clim_auto(self):
        dane = self.dane[numpy.isfinite(self.dane)]
        if dane.size == 0: dane = numpy.array([0., 1.])
        a, b = numpy.percentile(dane, [0.5, 99.5])
        a, b = int(numpy.floor(a)), int(numpy.ceil(b))
        if b <= a: b = a + 1
        self.min_e.setText("%i" % a)
        self.max_e.setText("%i" % b)
        self.min_s.setRange(a, b)
        self.max_s.setRange(a, b)
        self.min_s.setValue(a)
        self.max_s.setValue(b)

    def mkUI(self):
        FitsView_image.ImageView.mkUI(self)
        self.axes.set_position([0, 0, 0.86, 1])          # miejsce na skale kolorow
        self.cax = self.fig.add_axes([0.89, 0.05, 0.03, 0.9])

    def update(self):
        FitsView_image.ImageView.update(self)
        if self.dirty: return                            # niewidoczna zakladka
        self.cax.clear()
        self.fig.colorbar(self.image, cax=self.cax)      # nadaza za set_clim (suwaki min/max)
        self.canvas.draw_idle()


def pool_max(a, factor):
    # zmniejszenie maski factor razy: blok True, jesli choc jeden piksel jest True
    ny, nx = a.shape
    py, px = -ny % factor, -nx % factor
    a = numpy.pad(numpy.asarray(a, dtype=bool), ((0, py), (0, px)))
    return a.reshape((ny + py) // factor, factor, (nx + px) // factor, factor).any(axis=(1, 3))


class MaskTab(MapTab):
    # maska: True czarne na bialym, bez skali kolorow, plus ustawienia rysowania na Image (jak w Catalog)
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

    def mk_dane(self,data):
        return numpy.asarray(data, dtype=bool)

    def get_cmap(self):
        return matplotlib.colormaps["gray_r"]

    def clim_auto(self):
        self.min_e.setText("0")
        self.max_e.setText("1")
        self.min_s.setRange(0, 1)
        self.max_s.setRange(0, 1)
        self.min_s.setValue(0)
        self.max_s.setValue(1)

    def mkUI(self):
        FitsView_image.ImageView.mkUI(self)              # bez skali kolorow
        self.cmap_s.setEnabled(False)

        self.count_l = QLabel()
        self.plot_c = QCheckBox("Plot on Image")
        self.style_l = QLabel("Style: ")
        self.style_s = QComboBox()
        self.style_s.addItems(["contour", "fill"])
        self.mkcolor_l = QLabel("Color: ")
        self.mkcolor_p = ColorButton(initial_color=self.parent.mask_data[self.data_index]["color"])

        hbox = QHBoxLayout()
        for x in [self.plot_c, self.style_l, self.style_s, self.mkcolor_l, self.mkcolor_p]:
            hbox.addWidget(x)
        hbox.addStretch(1)
        hbox.addWidget(self.count_l)
        self.top_l.addLayout(hbox)

    def update(self):
        n = int(numpy.sum(self.dane))
        self.count_l.setText("%d pixels (%.3f %%)" % (n, 100. * n / self.dane.size))
        FitsView_image.ImageView.update(self)
        self.repool()

    def zmiana_zoom(self):
        FitsView_image.ImageView.zmiana_zoom(self)
        self.repool()

    def resizeEvent(self,event):
        MapTab.resizeEvent(self,event)
        self.repool()

    def repool(self):
        # Przy zmniejszaniu matplotlib bierze co n-ty piksel i pojedyncze piksele maski znikaja.
        # Glowny obraz i miniatura dostaja maske zmniejszona przez maksimum w blokach
        # (factor z widocznego fragmentu i rozmiaru na ekranie); viewfinder pokazuje piksele.
        if self.dirty or not self.isVisible(): return
        dane = numpy.rot90(self.dane) if self.parent.cfg_rot90 else self.dane
        for axes, image, origin in [(self.axes, self.image, "upper"), (self.axes_small, self.image_small, "lower")]:
            x1, x2 = axes.get_xlim()
            y1, y2 = axes.get_ylim()
            bbox = axes.bbox
            factor = max(1, int(numpy.ceil(max(abs(x2 - x1) / max(bbox.width, 1), abs(y2 - y1) / max(bbox.height, 1)))))
            a = pool_max(dane, factor)
            w, h = a.shape[1] * factor, a.shape[0] * factor
            image.set_data(a)
            if origin == "upper": image.set_extent((-0.5, w - 0.5, h - 0.5, -0.5))
            else: image.set_extent((-0.5, w - 0.5, -0.5, h - 0.5))
            axes.set_xlim(x1, x2)                         # set_extent potrafi zmienic zakres osi
            axes.set_ylim(y1, y2)
        self.canvas.draw_idle()
        self.canvas_small.draw_idle()

    def update_data(self):
        zestaw = self.zestaw()
        zestaw["plot_image"] = self.plot_c.isChecked()
        zestaw["color"] = self.mkcolor_p.color()
        zestaw["style"] = self.style_s.currentText()
        self.parent.update_overlays()
