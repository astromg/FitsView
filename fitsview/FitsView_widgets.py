#!/usr/bin/env python3
import numpy as np

from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QTextEdit, QLineEdit, QPushButton, \
    QGridLayout, QHBoxLayout, QVBoxLayout

import fitsview.fitsq as fitsq

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
        self.txt_e.append(txt)

    def find_stars(self):

        th = float(self.th_e.text())
        fwhm = float(self.fwhm_e.text())
        self.fq.find_stars(threshold=th, kernel_size=30, fwhm=fwhm)
        coo = self.fq.stats["stars"]["coo"]
        x = coo[:,0]
        y = coo[:,1]
        self.markings, = self.parent.axes.plot(y, x, 'o', markerfacecolor='none', markeredgecolor='blue', markersize=10,alpha=0.5)
        self.parent.canvas.draw()

    def fwhm_clicked(self):
        self.fq.fwhm(self.fq.stats,saturation=65000, radius=10, all_stars=True)
        txt = f'fwhm x = {self.fq.stats["fwhm_x"]:.2f}'
        self.txt_e.append(txt)
        txt = f'fwhm y = {self.fq.stats["fwhm_y"]:.2f}'
        self.txt_e.append(txt)
        self.markings.remove()

        coo = self.fq.stats["stars"]["coo"]
        x = coo[:,0]
        y = coo[:,1]
        fwhm = (np.array(self.fq.stats["stars"]["fwhm_xarr"]) + np.array(self.fq.stats["stars"]["fwhm_xarr"]))/2

        self.markings = self.parent.axes.scatter(y,x, marker="o",c=fwhm, facecolors="none", edgecolors="face", s=fwhm, linewidths=0.5, alpha=1)
        self.parent.canvas.draw()

    def cray_clicked(self):
        #self.markings.remove()
        maska0, crays_x, crays_y = self.fq.cosmic_ray_detection(self.fq.image)
        X, Y = np.meshgrid(np.arange(self.fq.image.shape[1]), np.arange(self.fq.image.shape[0]))
        self.countours = self.parent.axes.contour(X,Y, maska0, 0, colors='red',linewidths=1)
        self.parent.canvas.draw()


    def flines_clicked(self):

        k1 = int(self.k1_e.text())
        k2 = int(self.k2_e.text())
        th1 = float(self.k1th_e.text())
        th2 = float(self.k2th_e.text())

        maska0 = self.fq.line_detection(self.fq.image,k1=k1,k2=k2,th1=th1,th2=th2)

        try:
            self.markings.remove()
        except AttributeError:
            pass

        X, Y = np.meshgrid(np.arange(self.fq.image.shape[1]), np.arange(self.fq.image.shape[0]))
        self.markings = self.parent.axes.contour(X,Y, maska0, 0, colors='red',linewidths=1)
        self.parent.canvas.draw()



    def sky_background_clicked(self):
        self.fq.sky_gradient(self.fq.image,n_segments=10)

        txt = f"max amplitude: {self.fq.max_amplitude:.2f}"
        self.txt_e.append(txt)
        txt = f"max frame gradient: {self.fq.frame_gradient:.2f}"
        self.txt_e.append(txt)

        x = self.fq.sky_surface_x
        y = self.fq.sky_surface_y
        bk = self.fq.sky_surface_bk

        try:
            self.markings.remove()
        except AttributeError:
            pass
        self.markings = self.parent.axes.scatter(x,y, marker="o",c=bk, facecolors="none", edgecolors="face", s=50, linewidths=0.5, alpha=1)
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
        self.th_e = QLineEdit("10")
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
        self.fwhm_p = QPushButton('find FWHM', self)
        self.fwhm_p.clicked.connect(self.fwhm_clicked)
        grid.addWidget(self.fwhm_p, w, 0)
        w = w + 1
        self.bkg_p = QPushButton('sky background', self)
        self.bkg_p.clicked.connect(self.sky_background_clicked)
        grid.addWidget(self.bkg_p, w, 0)
        w = w + 1
        self.k1_l = QLabel("k1 / th1:")
        self.k1_e = QLineEdit("3")
        self.k1th_e = QLineEdit("3")

        self.k2_l = QLabel("k2 / th2:")
        self.k2_e = QLineEdit("7")
        self.k2th_e = QLineEdit("3")

        self.flines_p = QPushButton('find lines', self)
        self.flines_p.clicked.connect(self.flines_clicked)
        grid.addWidget(self.k1_l, w, 0)
        grid.addWidget(self.k1_e, w, 1)
        grid.addWidget(self.k1th_e, w, 2)
        w = w + 1
        grid.addWidget(self.k2_l, w, 0)
        grid.addWidget(self.k2_e, w, 1)
        grid.addWidget(self.k2th_e, w, 2)
        w = w + 1
        grid.addWidget(self.flines_p, w, 0)
        w = w + 1
        self.cray_p = QPushButton('find cosmic rays', self)
        self.cray_p.clicked.connect(self.cray_clicked)
        grid.addWidget(self.cray_p, w, 0)
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

