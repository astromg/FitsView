#!/usr/bin/env python3



import matplotlib, numpy
import matplotlib.patches as patches

from matplotlib import cm
from matplotlib.figure import Figure

from astropy.table import Table

from fitsview import FitsView_widgets

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QCheckBox, QTextEdit, QMessageBox, QLineEdit, \
    QDialog, QTabWidget, QPushButton, QFileDialog, QGridLayout, QHBoxLayout, QVBoxLayout, QInputDialog, QComboBox, \
    QSlider, QTableView
from PyQt5 import QtCore, QtGui

from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, QItemSelectionModel


class Catalog(QWidget):
    def __init__(self,parent,data):
        QWidget.__init__(self)

        self.data = data
        self.mkUI()
        self.initiatie()
        self.select_row(2)


    def initiatie(self):

        self.model = FitsTableModel(self.data)


        self.data_t.setModel(self.model)
        self.data_t.setSortingEnabled(True)
        self.data_t.resizeColumnsToContents()
        self.data_t.setAlternatingRowColors(True)

    def select_row(self, row):
        model = self.data_t.model()

        # jeśli używasz proxy model do sortowania
        if hasattr(model, "mapFromSource"):
            index = model.mapFromSource(model.sourceModel().index(row, 0))
        else:
            index = model.index(row, 0)  # QModelIndex dla kolumny 0

        selection_model = self.data_t.selectionModel()
        selection_model.select(index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        self.data_t.scrollTo(index)

    def on_row_clicked(self,wiersz):
        print("Widok row:", wiersz.row())
        #model_index = self.data_t.model().mapToSource(index) if hasattr(self.data_t.model(), "mapToSource") else index
        #print("Model row:", model_index.row())

    def mkUI(self):
        self.data_t = QTableView(self)
        self.data_t.setSelectionBehavior(QTableView.SelectRows)
        self.data_t.setSelectionMode(QTableView.SingleSelection)
        self.data_t.clicked.connect(self.on_row_clicked)

        self.label_l=QLabel("DUPA")

        grid= QGridLayout()
        w=0
        grid.addWidget(self.label_l, w, 0, 1, 2)
        w = w + 1
        grid.addWidget(self.data_t, w, 0)

        self.setLayout(grid)
        #       grid.setRowStretch(0,0)


        #       grid.setColumnStretch(0, 0)



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
