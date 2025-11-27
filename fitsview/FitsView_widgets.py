#!/usr/bin/env python3
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QTextEdit, QLineEdit, QPushButton, \
    QGridLayout, QHBoxLayout, QVBoxLayout

import fitsq

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

class FQWindow(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.setWindowFlag(Qt.Tool)
        self.parent = parent
        self.setWindowTitle('Fitsonometry')

        self.mkUI()
        self.txt_e.append(f'Fits Q version={fitsq.__version__}\n')

    def basic_stats(self):
        self.fq = fitsq.FQS()
        self.fq.image = self.parent.dane
        self.fq.basic_stats()
        txt = str(self.fq.stats)
        self.txt_e.append(txt+"\n")

    def find_stars(self):

        th = float(self.th_e.text())
        fwhm = float(self.fwhm_e.text())
        self.fq.find_stars(threshold=th, kernel_size=30, fwhm=fwhm)
        coo = self.fq.stats["stars"]["coo"]
        x = coo[:,0]
        y = coo[:,1]
        self.parent.axes.plot(y, x, 'o', markerfacecolor='none', markeredgecolor='blue', markersize=10,alpha=0.5)
        self.parent.canvas.draw()

    def mkUI(self):


        grid = QGridLayout()
        w = 0
        self.basic_p = QPushButton('Basic stats', self)
        self.basic_p.clicked.connect(self.basic_stats)

        grid.addWidget(self.basic_p, w, 0)
        w = w + 1

        self.find_p = QPushButton('Find stars', self)
        self.find_p.clicked.connect(self.find_stars)
        self.th_l = QLabel("th:")
        self.th_e = QLineEdit("5")
        self.fwhm_l = QLabel("fwhm:")
        self.fwhm_e = QLineEdit("3")

        grid.addWidget(self.th_l, w, 0)
        grid.addWidget(self.th_e, w, 1)
        w = w + 1
        grid.addWidget(self.fwhm_l, w, 0)
        grid.addWidget(self.fwhm_e, w, 1)
        w = w + 1
        grid.addWidget(self.find_p, w, 0)
        w = w + 1

        self.txt_e = QTextEdit()

        grid.addWidget(self.txt_e, w, 0, 1, 3)
        w = w + 3

        self.cl = QPushButton('Close', self)
        self.cl.clicked.connect(self.close_window)

        grid.addWidget(self.cl, w, 0)

        self.setLayout(grid)
        gm = eval(self.parent.parent.cfg_geometry)
        self.setGeometry(int(gm[1]) + int(gm[2]) + 10, int(gm[1]), 400, 500)
        self.show()

    def close_window(self):
        self.close()
