#!/usr/bin/env python3



import matplotlib, numpy
import matplotlib.patches as patches

from matplotlib import cm
from matplotlib.figure import Figure

from astropy.table import Table

from fitsview import FitsView_widgets
from fitsview.fv_theme import theme
from fitsview.FitsView_image import WHISKER

from fitsview.PyQtX.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QCheckBox, QTextEdit, QMessageBox, QLineEdit, \
    QDialog, QTabWidget, QPushButton, QFileDialog, QGridLayout, QHBoxLayout, QVBoxLayout, QInputDialog, QComboBox, \
    QSlider, QTableView, QSpinBox, QColorDialog, QAbstractItemView

from fitsview.PyQtX.QtCore import QAbstractTableModel, Qt, QModelIndex, QItemSelectionModel


RANGE_STEPS = 1000          # rozdzielczosc suwakow zakresu


def column_values(data, name):
    # kolumna jako float (NaN dla brakow) albo None, gdy nie liczbowa / brak kolumny
    if name not in getattr(data, "colnames", []): return None
    try:
        return numpy.ma.filled(numpy.ma.asarray(data[name]).astype(float), numpy.nan)
    except (ValueError, TypeError):
        return None


class Catalog(QWidget):
    def __init__(self,parent,data,data_index=None):
        QWidget.__init__(self)


        self.f_window = None

        self.parent = parent
        self.data_index = data_index
        self.data = data
        self.mkUI()
        self.initiatie()
        self.update()

        keys = self.data.keys()
        self.xcol_s.addItems(keys)
        self.ycol_s.addItems(keys)

        if "x" in keys:
            ix = keys.index("x")
            self.xcol_s.setCurrentIndex(ix)
        elif "x_center" in keys:
            ix = keys.index("x_center")
            self.xcol_s.setCurrentIndex(ix)
        elif "x0" in keys:                    # odcinki (np. ffs.lines): poczatek odcinka
            ix = keys.index("x0")
            self.xcol_s.setCurrentIndex(ix)
        else:
            self.xcol_s.setCurrentIndex(0)

        if "y" in keys:
            iy = keys.index("y")
            self.ycol_s.setCurrentIndex(iy)
        elif "y_center" in keys:
            iy = keys.index("y_center")
            self.ycol_s.setCurrentIndex(iy)
        elif "y0" in keys:
            iy = keys.index("y0")
            self.ycol_s.setCurrentIndex(iy)
        else:
            self.ycol_s.setCurrentIndex(1)

        self.color_s.addItems(["None"]+list(keys))
        self.color_s.setCurrentIndex(0)

        size = self.calc_size(len(self.data))

        self.mksize_s.setValue(size)

        # ustawienia zapamietane we wpisie table_data (poprzednia zakladka tej tabeli albo gotowe z add_coo(preset=...))
        zestaw = self.parent.table_data[self.data_index]
        if "marker" in zestaw: self.marker_c.setCurrentText(zestaw["marker"])
        if "mksize" in zestaw: self.mksize_s.setValue(int(zestaw["mksize"]))
        if zestaw.get("valuecol") in keys: self.color_s.setCurrentText(zestaw["valuecol"])
        self.reset_range(zestaw.get("range"), zestaw.get("outside", False))

        self.update_data()

        self.plot_c.stateChanged.connect(self.update_data)
        self.xcol_s.currentTextChanged.connect(self.update_data)
        self.ycol_s.currentTextChanged.connect(self.update_data)
        self.color_s.currentTextChanged.connect(self.color_changed)
        self.lo_s.valueChanged.connect(lambda v: self.slider_moved(self.lo_s))
        self.hi_s.valueChanged.connect(lambda v: self.slider_moved(self.hi_s))
        self.lo_s.sliderReleased.connect(self.update_data)
        self.hi_s.sliderReleased.connect(self.update_data)
        self.lo_e.editingFinished.connect(lambda: self.edit_changed(self.lo_e))
        self.hi_e.editingFinished.connect(lambda: self.edit_changed(self.hi_e))
        self.outside_c.toggled.connect(self.update_data)
        self.marker_c.currentTextChanged.connect(self.update_data)
        self.mksize_s.valueChanged.connect(self.update_data)
        self.mkcolor_p.clicked.connect(self.update_data)



    def initiatie(self):

        self.model = FitsTableModel(self.data)


        self.data_t.setModel(self.model)
        self.data_t.setSortingEnabled(True)            # klik w naglowek: FitsTableModel.sort
        self.data_t.horizontalHeader().setSortIndicator(-1, Qt.SortOrder.AscendingOrder)   # na start kolejnosc z pliku
        self.model.layoutChanged.connect(self.update_selection)
        self.data_t.resizeColumnsToContents()
        self.data_t.setAlternatingRowColors(True)

    def update(self):
        pass

    def update_selection(self):
        i = self.parent.table_data[self.data_index]["selected_index"]
        self.select_row(i)

    def select_row(self, row):
        # row - wiersz danych (selected_index); w widoku moze byc gdzie indziej po sortowaniu
        model = self.data_t.model()
        index = model.index(model.view_row(row), 0) if row >= 0 else model.index(-1, 0)
        selection_model = self.data_t.selectionModel()
        if row >= 0:
            selection_model.select(index, QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows)
            self.data_t.scrollTo(index)
        else:
            selection_model.clearSelection()

    def on_row_clicked(self,wiersz):
        i = self.model.data_row(wiersz.row())
        if i == self.parent.table_data[self.data_index]["selected_index"]:
            self.parent.table_data[self.data_index]["selected_index"] = -1
            self.select_row(-1)
        else:
            self.parent.table_data[self.data_index]["selected_index"] = i
            self.select_row(i)
        self.update_data()

    # ---- zakres kolumny kolorowania (color): dwa suwaki min / max. Obiekty spoza zakresu nie sa rysowane, w tabeli
    # sa wyszarzone i na koncu (FitsTableModel.set_active). "outside" - odwrotnie (np. shape poza oknem 0.55-0.95).
    def reset_range(self, rng=None, outside=False):
        # pelny zakres kolumny (albo rng = (min, max) z ustawien, None = koniec zakresu kolumny)
        v = column_values(self.data, self.color_s.currentText())
        good = v[numpy.isfinite(v)] if v is not None else numpy.array([])
        on = good.size > 0
        for w in (self.range_l, self.lo_s, self.hi_s, self.lo_e, self.hi_e, self.outside_c):
            w.setEnabled(on)
        self.vmin, self.vmax = (float(good.min()), float(good.max())) if on else (0., 1.)
        lo, hi = rng if rng is not None else (None, None)
        self.lo = self.vmin if lo is None else float(lo)
        self.hi = self.vmax if hi is None else float(hi)
        self.outside_c.blockSignals(True)
        self.outside_c.setChecked(bool(outside))
        self.outside_c.blockSignals(False)
        self.show_range()

    def to_pos(self, v):
        if self.vmax <= self.vmin: return 0
        return int(round(min(max((v - self.vmin) / (self.vmax - self.vmin), 0.), 1.) * RANGE_STEPS))

    def show_range(self):
        for s, e, v in ((self.lo_s, self.lo_e, self.lo), (self.hi_s, self.hi_e, self.hi)):
            s.blockSignals(True)
            s.setValue(self.to_pos(v))
            s.blockSignals(False)
            e.setText("%.6g" % v)

    def slider_moved(self, slider):
        v = self.vmin + (self.vmax - self.vmin) * slider.value() / RANGE_STEPS
        if slider is self.lo_s:
            self.lo = v
            if self.hi < v: self.hi = v
        else:
            self.hi = v
            if self.lo > v: self.lo = v
        self.show_range()
        if not slider.isSliderDown(): self.update_data()      # klawiatura / klik; przeciaganie - po puszczeniu

    def edit_changed(self, edit):
        try: v = float(edit.text())
        except ValueError:
            self.show_range()
            return
        if edit is self.lo_e: self.lo, self.hi = v, max(self.hi, v)
        else: self.hi, self.lo = v, min(self.lo, v)
        self.show_range()
        self.update_data()

    def color_changed(self):
        self.reset_range()
        self.update_data()

    def range_mask(self):
        # None - wszystkie (pelny zakres albo kolumna nie liczbowa)
        v = column_values(self.data, self.color_s.currentText())
        if v is None: return None
        outside = self.outside_c.isChecked()
        if not outside and self.lo <= self.vmin and self.hi >= self.vmax: return None
        with numpy.errstate(invalid="ignore"):
            inside = (v >= self.lo) & (v <= self.hi)
            return (~inside & numpy.isfinite(v)) if outside else inside

    def update_data(self):
        self.parent.table_data[self.data_index]["plot_image"] = self.plot_c.isChecked()

        mask = self.range_mask()
        z = self.parent.table_data[self.data_index]
        z["mask"] = mask
        z["range"] = (self.lo, self.hi)
        z["outside"] = self.outside_c.isChecked()
        self.model.set_active(mask)
        n = len(self.data)
        self.count_l.setText("%d rows" % n if mask is None else "%d of %d" % (int(mask.sum()), n))

        self.parent.table_data[self.data_index]["xcol"] = self.xcol_s.currentText()
        self.parent.table_data[self.data_index]["ycol"] = self.ycol_s.currentText()
        self.parent.table_data[self.data_index]["valuecol"] = self.color_s.currentText()

        self.parent.table_data[self.data_index]["marker_color"] = self.mkcolor_p.color()
        self.parent.table_data[self.data_index]["marker"] = self.marker_c.currentText()
        self.parent.table_data[self.data_index]["mksize"] = self.mksize_s.value()

        for tab in self.parent.tab:
            if hasattr(tab, "update_points"):
                tab.update_points()


    def plot_figure(self):
        if not self.f_window:
            self.f_window = FitsView_widgets.FigureWindow(self)
        else:
            self.f_window.update()                  # ponownie pokazuje zamkniety panel
            #self.parent.active_windows.append(self.e_window)

    def mkUI(self):
        self.data_t = QTableView(self)
        self.data_t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.data_t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.data_t.setStyleSheet("""QTableView::item:selected {background-color: #5db0ad;color: black;}""")

        self.data_t.clicked.connect(self.on_row_clicked)

        #self.plot_l = QLabel("Plot Points")
        self.plot_c = QCheckBox("Plot on Image")
        self.plot_c.setChecked(True)

        self.plotFigure_p = QPushButton("Plot Figure")
        self.plotFigure_p.clicked.connect(self.plot_figure)

        self.x_l = QLabel("X: ")
        self.y_l = QLabel("Y: ")
        self.color_l = QLabel("color: ")
        self.xcol_s = QComboBox()
        self.ycol_s = QComboBox()
        self.color_s = QComboBox()
        #self.xcol_s.addItems()
        #self.ycol_s.addItems()

        self.marker_l = QLabel("Marker: ")
        markers = ["open circle","open square","o", ".", ",", "s", "^", "v", "<", ">", "D", "d", "*", "+", "x", "X", "P", "h", "H", "8", "p", "_",
                   "|"]
        self.marker_c = QComboBox()
        self.marker_c.addItems(markers)
        if all(k in getattr(self.data, "colnames", []) for k in ("ellipticity", "theta")):
            # kreska wzdluz osi dluzszej, dlugosc ~ eliptycznosc (ImageView.draw_whiskers)
            self.marker_c.insertItem(2, WHISKER)
            self.marker_c.setItemData(2, "Line through each object along its longer axis (theta), length ~ ellipticity "
                                         "(e = 0.1: 2 % of the visible image width); Size = line thickness", Qt.ItemDataRole.ToolTipRole)
        self.mksize_l = QLabel("Size: ")
        self.mksize_s = QSpinBox()
        self.mkcolor_l = QLabel("Scatter color: ")
        self.mkcolor_p = ColorButton(initial_color=self.parent.table_data[self.data_index]["marker_color"])

        # zakres kolumny "color": min / max (suwaki i pola), outside - obiekty poza zakresem
        self.range_l = QLabel("range: ")
        self.lo_s = QSlider(Qt.Orientation.Horizontal)
        self.hi_s = QSlider(Qt.Orientation.Horizontal)
        for s in (self.lo_s, self.hi_s): s.setRange(0, RANGE_STEPS)
        self.lo_e = QLineEdit()
        self.hi_e = QLineEdit()
        for e in (self.lo_e, self.hi_e): e.setMaximumWidth(90)
        self.outside_c = QCheckBox("outside")
        tip = ("Range of the 'color' column: only objects with min <= value <= max are drawn on the image; the others are\n"
               "greyed out at the end of the table. 'outside': the objects outside the range instead. Full range = all.")
        for w in (self.range_l, self.lo_s, self.hi_s, self.lo_e, self.hi_e, self.outside_c): w.setToolTip(tip)
        self.count_l = QLabel()


        grid= QGridLayout()
        w=0
        #grid.addWidget(self.plot_l, w, 0)
        grid.addWidget(self.plot_c, w, 1)
        grid.addWidget(self.plotFigure_p, w, 3)
        w = w + 1
        grid.addWidget(self.x_l, w, 0)
        grid.addWidget(self.xcol_s, w, 1)
        grid.addWidget(self.y_l, w, 2)
        grid.addWidget(self.ycol_s, w, 3)
        w = w + 1
        grid.addWidget(self.color_l, w, 0)
        grid.addWidget(self.color_s, w, 1)
        w = w + 1
        grid.addWidget(self.marker_l, w, 0)
        grid.addWidget(self.marker_c, w, 1)
        grid.addWidget(self.mksize_l, w, 2)
        grid.addWidget(self.mksize_s, w, 3)
        grid.addWidget(self.mkcolor_l, w, 4)
        grid.addWidget(self.mkcolor_p, w, 5)
        w = w + 1
        rng = QHBoxLayout()
        for x, k in ((self.range_l, 0), (self.lo_s, 1), (self.lo_e, 0), (self.hi_s, 1), (self.hi_e, 0),
                     (self.outside_c, 0), (self.count_l, 0)):
            rng.addWidget(x, k)
        grid.addLayout(rng, w, 0, 1, 6)
        w = w + 1
        grid.addWidget(self.data_t, w, 0, 1, 6)

        self.setLayout(grid)
        #       grid.setRowStretch(0,0)


        #       grid.setColumnStretch(0, 0)


    def calc_size(self,N):
        if N < 20:
            size = 20
        elif N < 500:
            size = int(20 - 20 * N/500)+1
        else:
            size = 1
        return size

class FitsTableModel(QAbstractTableModel):
    def __init__(self, table, parent=None):
        super().__init__(parent)

        self.table = table
        self.columns = table.colnames if hasattr(table, "colnames") else table.dtype.names
        # sortowanie bez zmiany tabeli: order[wiersz widoku] = wiersz danych (selected_index, klawisz f, rysowanie
        # na obrazie zostaja w kolejnosci danych); naglowek wiersza pokazuje numer wiersza danych
        self.order = numpy.arange(len(table))
        self.inverse = numpy.arange(len(table))
        self.sort_key = None                  # (kolumna, kolejnosc) ostatniego sortowania
        self.active = None                    # maska wierszy w zakresie (Catalog); None - wszystkie

    def data_row(self, view_row):
        return int(self.order[view_row])

    def view_row(self, data_row):
        return int(self.inverse[data_row])

    def set_active(self, mask):
        # wiersze poza zakresem (mask False) - wyszarzone, na koncu tabeli
        self.active = mask
        self.reorder()

    def sort(self, column, order=Qt.SortOrder.AscendingOrder):
        if column < 0 or column >= len(self.columns): return
        self.sort_key = (column, order)
        self.reorder()

    def reorder(self):
        klucz = self.sorted_rows()
        if self.active is not None:                       # stabilnie: najpierw aktywne, potem reszta
            a = numpy.asarray(self.active, dtype=bool)[klucz]
            klucz = numpy.concatenate([klucz[a], klucz[~a]])
        self.layoutAboutToBeChanged.emit()
        self.order = klucz
        self.inverse = numpy.empty_like(klucz)
        self.inverse[klucz] = numpy.arange(len(klucz))
        self.layoutChanged.emit()

    def sorted_rows(self):
        if self.sort_key is None: return numpy.arange(len(self.table))
        column, order = self.sort_key
        col = self.table[self.columns[column]]
        try:
            a = numpy.ma.filled(numpy.ma.asarray(col).astype(float), numpy.nan)      # liczby; NaN zawsze na koncu
            klucz = numpy.argsort(a, kind="stable")
            if order == Qt.SortOrder.DescendingOrder:
                nan = numpy.isnan(a[klucz])
                klucz = numpy.concatenate([klucz[~nan][::-1], klucz[nan]])
        except (ValueError, TypeError):
            a = numpy.array([str(v) for v in col])                                    # tekst
            klucz = numpy.argsort(a, kind="stable")
            if order == Qt.SortOrder.DescendingOrder: klucz = klucz[::-1]
        return klucz

    def rowCount(self, parent=QModelIndex()):
        return len(self.table)

    def columnCount(self, parent=QModelIndex()):
        return len(self.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            value = self.table[self.columns[index.column()]][self.order[index.row()]]
            return str(value)
        if role == Qt.ItemDataRole.ForegroundRole and self.active is not None and not self.active[self.order[index.row()]]:
            return theme.qcolor("muted_fg")               # poza zakresem (Catalog) - wyszarzony

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == Qt.Orientation.Horizontal:
            return self.columns[section]
        else:
            return str(self.order[section]) if section < len(self.order) else str(section)



class ColorButton(QPushButton):
    def __init__(self, initial_color="#616bff", parent=None):
        super().__init__(parent)

        self._color = initial_color
        self.update_style()

        self.clicked.connect(self.choose_color)

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self._color = color.name()
            self.update_style()

    def update_style(self):
        self.setStyleSheet(
            f"background-color: {self._color};"
            "border: 1px solid gray;"
        )

    def color(self):
        return self._color