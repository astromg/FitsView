#!/usr/bin/env python3



import matplotlib, numpy
import matplotlib.patches as patches

from matplotlib import cm
from matplotlib.figure import Figure

from astropy.table import Table

from fitsview import FitsView_widgets

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QCheckBox, QTextEdit, QMessageBox, QLineEdit, \
    QDialog, QTabWidget, QPushButton, QFileDialog, QGridLayout, QHBoxLayout, QVBoxLayout, QInputDialog, QComboBox, \
    QSlider, QTableView, QSpinBox, QColorDialog
from PyQt5 import QtCore, QtGui

from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, QItemSelectionModel


class Catalog(QWidget):
    def __init__(self,parent,data,data_index=None):
        QWidget.__init__(self)

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
        else:
            self.xcol_s.setCurrentIndex(0)

        if "y" in keys:
            iy = keys.index("y")
            self.ycol_s.setCurrentIndex(iy)
        elif "y_center" in keys:
            iy = keys.index("y_center")
            self.ycol_s.setCurrentIndex(iy)
        else:
            self.ycol_s.setCurrentIndex(1)

        self.color_s.addItems(["None"]+list(keys))
        self.color_s.setCurrentIndex(0)

        size = self.calc_size(len(self.data))

        self.mksize_s.setValue(size)

        self.update_data()

        self.plot_c.stateChanged.connect(self.update_data)
        self.xcol_s.currentTextChanged.connect(self.update_data)
        self.ycol_s.currentTextChanged.connect(self.update_data)
        self.color_s.currentTextChanged.connect(self.update_data)
        self.marker_c.currentTextChanged.connect(self.update_data)
        self.mksize_s.valueChanged.connect(self.update_data)
        self.mkcolor_p.clicked.connect(self.update_data)



    def initiatie(self):

        self.model = FitsTableModel(self.data)


        self.data_t.setModel(self.model)
        self.data_t.setSortingEnabled(True)
        self.data_t.resizeColumnsToContents()
        self.data_t.setAlternatingRowColors(True)

    def update(self):
        pass

    def update_selection(self):
        i = self.parent.table_data[self.data_index]["selected_index"]
        self.select_row(i)

    def select_row(self, row):
        model = self.data_t.model()
        index = model.index(row, 0)
        selection_model = self.data_t.selectionModel()
        if row >= 0:
            selection_model.select(index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
            self.data_t.scrollTo(index)
        else:
            selection_model.clearSelection()

    def on_row_clicked(self,wiersz):
        i = wiersz.row()
        if i == self.parent.table_data[self.data_index]["selected_index"]:
            self.parent.table_data[self.data_index]["selected_index"] = -1
            self.select_row(-1)
        else:
            self.parent.table_data[self.data_index]["selected_index"] = i
            self.select_row(i)
        self.update_data()

    def update_data(self):
        self.parent.table_data[self.data_index]["plot_image"] = self.plot_c.checkState()

        self.parent.table_data[self.data_index]["xcol"] = self.xcol_s.currentText()
        self.parent.table_data[self.data_index]["ycol"] = self.ycol_s.currentText()
        self.parent.table_data[self.data_index]["valuecol"] = self.color_s.currentText()

        self.parent.table_data[self.data_index]["marker_color"] = self.mkcolor_p.color()
        self.parent.table_data[self.data_index]["marker"] = self.marker_c.currentText()
        self.parent.table_data[self.data_index]["mksize"] = self.mksize_s.value()

        for tab in self.parent.tab:
            if hasattr(tab, "update_points"):
                tab.update_points()



    def mkUI(self):
        self.data_t = QTableView(self)
        self.data_t.setSelectionBehavior(QTableView.SelectRows)
        self.data_t.setSelectionMode(QTableView.SingleSelection)
        self.data_t.setStyleSheet("""QTableView::item:selected {background-color: #5db0ad;color: black;}""")

        self.data_t.clicked.connect(self.on_row_clicked)

        self.plot_l = QLabel("Plot Points")
        self.plot_c = QCheckBox("Plot on Image")
        self.plot_c.setChecked(True)

        self.x_l = QLabel("X: ")
        self.y_l = QLabel("Y: ")
        self.color_l = QLabel("color: ")
        self.xcol_s = QComboBox()
        self.ycol_s = QComboBox()
        self.color_s = QComboBox()
        #self.xcol_s.addItems()
        #self.ycol_s.addItems()

        self.marker_l = QLabel("Marker: ")
        markers = ["open circle","o", ".", ",", "s", "^", "v", "<", ">", "D", "d", "*", "+", "x", "X", "P", "h", "H", "8", "p", "_",
                   "|"]
        self.marker_c = QComboBox()
        self.marker_c.addItems(markers)
        self.mksize_l = QLabel("Size: ")
        self.mksize_s = QSpinBox()
        self.mkcolor_l = QLabel("Scatter color: ")
        self.mkcolor_p = ColorButton(initial_color=self.parent.table_data[self.data_index]["marker_color"])


        grid= QGridLayout()
        w=0
        grid.addWidget(self.plot_l, w, 0)
        grid.addWidget(self.plot_c, w, 1)
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

    def rowCount(self, parent=QModelIndex()):
        return len(self.table)

    def columnCount(self, parent=QModelIndex()):
        return len(self.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            value = self.table[self.columns[index.column()]][index.row()]
            return str(value)

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return self.columns[section]
        else:
            return str(section)



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