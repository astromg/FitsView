#!/usr/bin/env python3

#----------------
# 23.03.2022
# Marek Gorski
#----------------

import matplotlib, numpy
import matplotlib.patches as patches
from astropy.io import fits

from matplotlib.figure import Figure

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel,QCheckBox, QTextEdit, QLineEdit, QDialog, QTabWidget, QPushButton, QFileDialog, QGridLayout, QHBoxLayout, QVBoxLayout, QInputDialog,QComboBox, QSlider
    
from PyQt5 import QtCore, QtGui
    

class HeaderTabLocal(QWidget):
   def __init__(self,parent,header): 
       QWidget.__init__(self)
       
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
      #self.parent.canvas.setFocus()
      
  def close_window(self):     
      self.close()      


class PlotWindow(QWidget):
  def __init__(self,parent):
      QWidget.__init__(self)
      self.parent=parent
      self.setWindowTitle('Plot')
      
      self.txt=""


      self.fig = Figure(figsize=(2, 2), linewidth=-1, dpi=100,tight_layout=True, frameon=True)
      self.canvas = FigureCanvas(self.fig)    
      self.axes = self.fig.add_subplot(111)
      self.toolbar = NavigationToolbar(self.canvas, self)      
      #self.axes.axis("on")
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
#      vbox.addStretch(1)
      vbox.addLayout(hbox1)
      vbox.addLayout(hbox1a)
      vbox.addLayout(hbox2)        
      vbox.addLayout(hbox3) 
      self.setLayout(vbox) 
         
      self.pole.setReadOnly(1)
      self.toolbar.hide()
#      self.pole.setLineWrapMode(0)
      self.show()
      gm=eval(self.parent.parent.cfg_geometry)
      self.setGeometry(int(gm[1])+int(gm[2])+10,int(gm[1]+200),400,400)
  def update(self):
      self.show()
      self.pole.setText(self.txt)
      self.parent.activateWindow()
      #self.parent.canvas.setFocus()
      
  def close_window(self):  
      self.close()  
      self.parent.update()
      
  def resizeEvent(self, event):
      if float(self.frameGeometry().width()) > 700 and float(self.frameGeometry().height()) > 500:
         self.toolbar.show()
      else: self.toolbar.hide()
      QMainWindow.resizeEvent(self, event)
          
