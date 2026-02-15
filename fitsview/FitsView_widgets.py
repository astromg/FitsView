#!/usr/bin/env python3
from PyQt5.QtCore import Qt
from astropy.io.misc.asdf.tags.helpers import skycoord_equal
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QTextEdit, QLineEdit, QPushButton, \
    QGridLayout, QHBoxLayout, QVBoxLayout, QComboBox

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

class FFSWindow(QWidget):
    def __init__(self, parent, image, saturation=50000,dx=0,dy=0):
        QWidget.__init__(self)
        self.setWindowFlag(Qt.Tool)
        self.parent = parent
        self.image = image
        self.saturation = saturation
        self.dx=int(dx)
        self.dy=int(dy)

        self.txt = ""

        self.mkUI()
        self.initFFS()

    def initFFS(self):
        size = self.image.shape
        txt = f'------ {size} -------'
        self.pole_e.append(txt)

        self.ffs = FFS(self.image)
        self.ffs.saturation = self.saturation
        self.ffs.mk_stats()
        for k in self.ffs.stats.keys():
            txt = f'{k}: {self.ffs.stats[k]:.2f}'
            self.pole_e.append(txt)
            #print(f'{k}: {ffs.stats[k]} // {ffs.stats_description[k]}')


        #ffs.sky_gradient(n_segments=10)
        #ffs.find_lines()
        #ffs.star_info(box=15, N_stars=20)
        #ffs.calc_star_stats()

    def find_pushed(self):
        th = float(self.th_e.text())
        fwhm = float(self.fwhm_e.text())
        box = int(2 * fwhm)
        self.ffs.find_stars(threshold=th, fwhm=fwhm)
        self.ffs.calc_frame_fwhm(threshold=th, fwhm=fwhm, box=box, N_stars=20)
        self.ffs.star_info(box=box, N_stars=None)

        stars = self.ffs.stars
        stars["x"] = stars["x"] + self.dx
        stars["y"] = stars["y"] + self.dy

        self.parent.parent.add_coo(stars, name="ffs.star_info")

        txt = f'{"frame_fwhm"}: {self.ffs.stats["frame_fwhm"]:.2f}'
        self.pole_e.append(txt)
        txt = f'{"frame_ellipticity"}: {self.ffs.stats["frame_ellipticity"]:.2f}'
        self.pole_e.append(txt)
        txt = f'{"frame_cpe"}: {self.ffs.stats["frame_cpe"]:.2f}'
        self.pole_e.append(txt)

    def calc_gradient(self):
        n = int(self.segments_e.text())
        self.ffs.sky_gradient(n_segments=n)
        txt = f'{"sky max amplitude"}: {self.ffs.stats["bkg_max_amplitude"]:.2f}'
        self.pole_e.append(txt)
        txt = f'{"sky frame gradient"}: {self.ffs.stats["bkg_frame_gradient"]:.2f}'
        self.pole_e.append(txt)

        sky = self.ffs.sky
        sky["sky_surface_x"] = sky["sky_surface_x"] + self.dx
        sky["sky_surface_y"] = sky["sky_surface_y"] + self.dy
        self.parent.parent.add_coo(sky, name="ffs.sky")


    def mkUI(self):
        self.setWindowTitle('FFS')
        grid = QGridLayout()

        w = 0
        self.find_p = QPushButton('Find stars', self)
        self.find_p.clicked.connect(self.find_pushed)

        self.th_l = QLabel("Th:", self)
        self.th_e = QLineEdit("10")
        self.fwhm_l = QLabel("fwhm:")
        self.fwhm_e = QLineEdit("5")

        grid.addWidget(self.find_p, w, 0)
        grid.addWidget(self.th_l, w, 1)
        grid.addWidget(self.th_e, w, 2)
        grid.addWidget(self.fwhm_l, w, 3)
        grid.addWidget(self.fwhm_e, w, 4)

        w = w + 1

        self.gradient_p = QPushButton("Check sky:", self)
        self.gradient_p.clicked.connect(self.calc_gradient)

        self.segments_l = QLabel("Segments:", self)
        self.segments_e = QLineEdit("10")

        grid.addWidget(self.gradient_p, w, 0)
        grid.addWidget(self.segments_l, w, 1)
        grid.addWidget(self.segments_e, w, 2)

        w = w + 1

        self.pole_e = QTextEdit()
        self.pole_e.setReadOnly(1)

        grid.addWidget(self.pole_e, w, 0, 3, 5)

        w = w + 3
        self.cl_p = QPushButton('Close', self)
        self.cl_p.clicked.connect(self.close_window)
        grid.addWidget(self.cl_p, w, 1, 1, 2)

        self.setLayout(grid)

        gm = eval(self.parent.parent.cfg_geometry)
        self.setGeometry(int(gm[1]) + int(gm[2]) + 10, int(gm[1]), 400, 500)

    def update(self):
        self.show()
        self.pole_e.append(self.txt)
        self.parent.activateWindow()

    def close_window(self):
        self.hide()