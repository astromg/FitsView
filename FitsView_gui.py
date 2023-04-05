#!/usr/bin/env python3

#----------------
# 23.03.2022
# Marek Gorski
#----------------

import time

import os,sys
import warnings
import matplotlib, numpy
import matplotlib.patches as patches
from astropy.io import fits
from astropy.utils.exceptions import AstropyWarning
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QMessageBox, QLabel,QCheckBox, QComboBox, QTextEdit, QLineEdit, QDialog, QTabWidget, QPushButton, QFileDialog, QGridLayout, QHBoxLayout, QVBoxLayout, QMessageBox
from PyQt5 import QtCore, QtGui


from FitsView_image import *

warnings.simplefilter('ignore', category=AstropyWarning)

#print(matplotlib.__version__)

class FitsView(QWidget):
   def __init__(self,args,parent=None): 
       QWidget.__init__(self) 


       txt=__file__
       if ".pyc" in txt: self.pwd=txt.strip("FitsView_gui.pyc")
       else:  self.pwd=txt.strip("FitsView_gui.py")     
         
       
       self.args=args
       
       self.active_windows=[]
       self.initiate()
       self.mkUI()
       self.conf()
       gm=eval(self.cfg_geometry)
       #self.setGeometry(gm[0],gm[1],800,750)          # Jak sie ustawi size okna zle to wypieprza caly program 
       self.setGeometry(gm[0],gm[1],gm[2],gm[3])
       self.show() 
       self.raise_()   
       self.com=Communicate()
  
       #self.update()
       
   def initiate(self):
       self.config_file="FitsView.cfg"
       self.fname=False
       
       self.coo_file=False
       
       self.ext_x=[]
       self.ext_y=[]
       self.ext_l=[]      
       self.special=False

       
       #print(self.hdu.info())

   def nextFits(self):   
          lista=[f for f in os.listdir(os.getcwd()) if ".fits" in f]
          i=lista.index(self.fname)
          if i<len(lista)-1: 
            i=i+1
            self.fname=lista[i] 
            self.newFits()   


   def prevFits(self):   
          lista=[f for f in os.listdir(os.getcwd()) if ".fits" in f]
          i=lista.index(self.fname)
          if i>0: 
            i=i-1
            self.fname=lista[i] 
            self.newFits()   

   def newFits(self):

       if ".fits" in self.fname:
         
          self.TabWindow.clear() 
          
          self.coo_file=False
          
          self.ext_x=[]
          self.ext_y=[]
          self.ext_l=[]            
          

          self.getFits()
          self.updateUI()
          self.TabWindow.setCurrentIndex(1)
          self.TabWindow.setCurrentIndex(int(self.cfg_active_tab))
          self.updateCooList()
       else: 
          self.msg = QMessageBox()
          self.msg.setText(self.fname.split("/")[-1] + " is not a FITS file")   
          self.msg.exec_()

   def updateCooList(self):
       basename=self.fname.replace(".fits","").split("/")[-1]
       opcje = [f for f in os.listdir(os.getcwd()) if basename in f]
       opcje=["other file"]+opcje
       if self.fname.split("/")[-1] in opcje: opcje.remove(self.fname.split("/")[-1])
       self.coo_l.clear()
       self.coo_l.addItems(opcje)
       self.coo_p.setStyleSheet("")

   def coo_index_changed(self):
       self.coo_p.setStyleSheet("color: rgb(255,140,0);")
     

   def open_confWindow(self):
       self.cfg_window=Settings(self)    
       self.active_windows.append(self.cfg_window) 
       try:
          i = self.TabWindow.currentIndex()
          self.cfg_active_tab=i
          self.cfg_zoom  = self.tab[i].zoom_s.value()
          self.cfg_zoomX = self.tab[i].x
          self.cfg_zoomY = self.tab[i].y
       except: print("EXCEPTION 003") 
       
       gm=eval(str(self.cfg_geometry))
       self.cfg_window.setGeometry(gm[1]+600,gm[2]+100,400,500)     
       self.cfg_window.show()
       self.cfg_window.update()
       

   def zamknij(self):
       for okno in self.active_windows: okno.close()
       self.close()

   def mkUI(self):
       
       
       self.TabWindow=QTabWidget()
       
       self.load_p = QPushButton("Load FITS")
       self.load_p.clicked.connect(self.load_fits)
       self.close_p = QPushButton("Close")
       self.close_p.clicked.connect(self.zamknij)

       self.hinfo_e=QTextEdit()
       self.hinfo_e.setReadOnly(True)

       self.coo_p = QPushButton("Load COO")
       self.coo_p.clicked.connect(self.get_coo)
       self.coo_l=QComboBox()
       self.coo_l.currentIndexChanged.connect(self.coo_index_changed)

       self.config_p = QPushButton("Configuration")
       self.config_p.clicked.connect(self.open_confWindow)
       
       self.help_p = QPushButton("HELP")
       self.help_p.clicked.connect(self.open_help)

       self.next_p = QPushButton("\u2192")
       self.next_p.clicked.connect(self.nextFits)
       self.prev_p = QPushButton("\u2190")
       self.prev_p.clicked.connect(self.prevFits)              
              
       grid = QGridLayout()  
       
       grid.addWidget(self.hinfo_e,0,0,3,5) 

       grid.addWidget(self.TabWindow,3,0,4,5)

       grid.addWidget(self.load_p,8,0)
       grid.addWidget(self.coo_p,8,1)
       grid.addWidget(self.coo_l,8,2)
       grid.addWidget(self.prev_p,8,3)
       grid.addWidget(self.next_p,8,4)

       grid.addWidget(self.help_p,9,0)       
       grid.addWidget(self.config_p,9,1)
         
       grid.addWidget(self.close_p,9,3,1,2)
       grid.setSpacing(10)
       self.setLayout(grid)
       self.setGeometry(50, 50, 800, 750)


   def open_help(self):
       tmp=self.pwd+"FitsView.hlp"
       help_window = HelpWindow(self,tmp)
       self.active_windows.append(help_window)


   def get_coo(self):
       if self.coo_l.currentIndex()==0:
          ok=False
          try: 
            self.coo_file = str(QFileDialog.getOpenFileName(self, 'Open file','.')[0] )
            ok=True
          except: ok=False
          if ok: self.load_coo()
       else: 
          self.coo_file=self.coo_l.currentText()    
          self.load_coo()
       

   def load_coo(self):       
       plik=open(self.coo_file,'r')
       self.setWindowTitle(self.fname+"   "+self.coo_file.split("/")[-1])
              
       self.ext_x=[]
       self.ext_y=[]
       self.ext_l=[]

       i=0       
       if ".ap" in self.coo_file:
          przelacznik=2
          txt=""
          for line in plik:
             if i>2:
                if przelacznik == 0:
                   txt=line
                   self.ext_x.append(float(line.split()[1])-1.)
                   self.ext_y.append(float(line.split()[2])-1.)
                   przelacznik=1
                elif przelacznik == 1:
                   txt=txt+line
                   self.ext_l.append(txt)
                   przelacznik=2
                elif przelacznik == 2:
                   przelacznik=0               
             i=i+1


       elif ".raw" in self.coo_file or ".tfr" in self.coo_file or ".out" in self.coo_file or ".coo" in self.coo_file or ".als" in self.coo_file or ".lst" in self.coo_file or ".rsl" in self.coo_file: 
          for line in plik:
             if i>2 and len(line.split())>1: 
                self.ext_x.append(float(line.split()[1])-1.)
                self.ext_y.append(float(line.split()[2])-1.)
                self.ext_l.append(line)
             i=i+1


       elif ".cal" in self.coo_file: 
          for line in plik:
             if i>2 and len(line.split())>1: 
                if "_J" in self.fname.split("/")[-1]:
                   self.ext_x.append(float(line.split()[2])-1.)
                   self.ext_y.append(float(line.split()[3])-1.)
                   self.ext_l.append(line)
                if "_K" in self.fname.split("/")[-1]:
                   self.ext_x.append(float(line.split()[4])-1.)
                   self.ext_y.append(float(line.split()[5])-1.)
                   self.ext_l.append(line)
             i=i+1
             
       else:
          try: 
             for line in plik:
                 if "#" not in line and len(line.strip())>0: 
                    self.ext_x.append(float(line.split()[int(self.cfg_xCol)]))
                    self.ext_y.append(float(line.split()[int(self.cfg_yCol)]))
                    self.ext_l.append(line)                 
          except IndexError: 
                 self.ext_x,self.ext_y,self.ext_l=[],[],[]
                 self.msg = QMessageBox()
                 self.msg.setText("Wrong column definition in COO file.\nCheck configuration!")   
                 self.msg.exec_()          
       self.coo_p.setStyleSheet("") 
       self.coo_p.repaint()      # trzeba to tu bo na mac os czasem sie nie updatuje
       for x in self.tab: x.update()  


   def updateHInfo(self):
     
       self.setWindowTitle(self.fname)
       self.hinfo_e.clear()
       self.hinfo_e.setFont(QtGui.QFont("Courier"))
       
       hdu=self.hdu[0].header
       
       txt=self.cfg_hdr_keywords[0][0]
       tmp="unknown"
       for x in self.cfg_hdr_keywords[0]:
           try: tmp=str(hdu[x])
           except: pass
       self.hinfo_e.setTextColor(QtCore.Qt.black)  
       self.hinfo_e.insertPlainText(txt.ljust(10))
       self.hinfo_e.setTextColor(QtCore.Qt.darkRed)
       self.hinfo_e.insertPlainText(tmp.ljust(20))

       txt=self.cfg_hdr_keywords[3][0]
       tmp="unknown"
       for x in self.cfg_hdr_keywords[3]:
           try: tmp=str(hdu[x])
           except: pass
       self.hinfo_e.setTextColor(QtCore.Qt.black)  
       self.hinfo_e.insertPlainText(txt.ljust(15))
       self.hinfo_e.setTextColor(QtCore.Qt.darkRed)
       self.hinfo_e.insertPlainText(tmp.ljust(15))

       txt=self.cfg_hdr_keywords[6][0]
       tmp="unknown"
       for x in self.cfg_hdr_keywords[6]:
           try: tmp=str(hdu[x])
           except: pass
       self.hinfo_e.setTextColor(QtCore.Qt.black)  
       self.hinfo_e.insertPlainText(txt.ljust(10))
       self.hinfo_e.setTextColor(QtCore.Qt.darkRed)
       self.hinfo_e.insertPlainText(tmp)
       
       self.hinfo_e.insertPlainText("\n")
       #----------------------------------------      
      
       txt=self.cfg_hdr_keywords[1][0]
       tmp="unknown"
       for x in self.cfg_hdr_keywords[1]:
           try: tmp=str(hdu[x])
           except: pass
       self.hinfo_e.setTextColor(QtCore.Qt.black)  
       self.hinfo_e.insertPlainText(txt.ljust(10))
       self.hinfo_e.setTextColor(QtCore.Qt.darkRed)
       self.hinfo_e.insertPlainText(tmp.ljust(20))       
       
       txt=self.cfg_hdr_keywords[4][0]
       tmp="unknown"
       for x in self.cfg_hdr_keywords[4]:
           try: tmp=str(hdu[x])
           except: pass
       self.hinfo_e.setTextColor(QtCore.Qt.black)  
       self.hinfo_e.insertPlainText(txt.ljust(15))
       self.hinfo_e.setTextColor(QtCore.Qt.darkRed)
       self.hinfo_e.insertPlainText(tmp.ljust(15))       

       txt=self.cfg_hdr_keywords[7][0]
       tmp="unknown"
       for x in self.cfg_hdr_keywords[7]:
           try: tmp=str(hdu[x])
           except: pass
       self.hinfo_e.setTextColor(QtCore.Qt.black)  
       self.hinfo_e.insertPlainText(txt.ljust(10))
       self.hinfo_e.setTextColor(QtCore.Qt.darkRed)
       self.hinfo_e.insertPlainText(tmp)  
       
       self.hinfo_e.insertPlainText("\n")       
       #----------------------------------------


       txt=self.cfg_hdr_keywords[2][0]
       tmp="unknown"
       for x in self.cfg_hdr_keywords[2]:
           try: tmp=str(hdu[x])
           except: pass
       self.hinfo_e.setTextColor(QtCore.Qt.black)  
       self.hinfo_e.insertPlainText(txt.ljust(10))
       self.hinfo_e.setTextColor(QtCore.Qt.darkRed)
       self.hinfo_e.insertPlainText(tmp.ljust(20))  

       txt=self.cfg_hdr_keywords[5][0]
       tmp="unknown"
       for x in self.cfg_hdr_keywords[5]:
           try: tmp=str(hdu[x])
           except: pass
       self.hinfo_e.setTextColor(QtCore.Qt.black)  
       self.hinfo_e.insertPlainText(txt.ljust(15))
       self.hinfo_e.setTextColor(QtCore.Qt.darkRed)
       self.hinfo_e.insertPlainText(tmp.ljust(15)) 
       
       txt=self.cfg_hdr_keywords[8][0]
       tmp="unknown"
       for x in self.cfg_hdr_keywords[8]:
           try: tmp=str(hdu[x])
           except: pass
       self.hinfo_e.setTextColor(QtCore.Qt.black)  
       self.hinfo_e.insertPlainText(txt.ljust(10))
       self.hinfo_e.setTextColor(QtCore.Qt.darkRed)
       self.hinfo_e.insertPlainText(tmp)        
       

   def load_fits(self):
       self.fname = str( QFileDialog.getOpenFileName(self, 'Open file','.')[0] )
       self.newFits()


   def errmssg(self,txt):
       self.msg = QMessageBox()
       self.msg.setText(txt)   
       self.msg.exec_()         

   def updateUI(self):

       self.updateHInfo()
       n=0
       i=0
 
       self.tab=[]
       self.tab.append(HeaderTab(self,self.hdu[0].header))

       self.TabWindow.insertTab(i,self.tab[-1],"Primary Header")
       i=i+1
       while n<self.Nhdu:   
          if self.hdu[n].data is None: pass
          else: 
             OK=False 
             try: 
                self.hdu[n].data.min()
                OK=True
             except: OK=False
             if OK:
                self.tab.append(Image(self,self.hdu[n]))
                self.tab[-1].update()
                self.TabWindow.insertTab(i,self.tab[-1],"IMAGE")
                i=i+1
  
          n=n+1
       #self.TabWindow.setCurrentIndex(0)          
      # self.TabWindow.addTab(self.tab[0],"Settings")           

          
   def update(self):
       gm=eval(self.cfg_geometry)
       #self.setGeometry(gm[0],gm[1],gm[2],gm[3]) 
       self.updateHInfo()
       for x in self.tab: x.update()
    

   def getFits(self):
       self.hdu=fits.open(self.fname)
       self.Nhdu = len(self.hdu)
       
       #print self.hdu.info()

   def conf(self):       # CONFIG LOAD AND DEFINE
       cfg_file=[]
       cfg_fname=self.pwd+self.config_file
       try: 
         cfg_f=open(cfg_fname)
         for l in cfg_f: cfg_file.append(l)
       except: print("no FitsView.cfg file")
       

       tmp="geometry"                                   
       wartosc="(50,50,800,750)"                                     
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1]     
       self.cfg_geometry=wartosc  

       tmp="loud"                                     # TUTAJ
       wartosc=True                                         # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1]     
       self.cfg_loud=wartosc                          # TUTAJ

       tmp="active_tab"                                     # TUTAJ
       wartosc="1"                                         # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1]     
       self.cfg_active_tab=wartosc                          # TUTAJ            


       #######################

       tmp="aper_size"                                     # TUTAJ
       wartosc="10"                                         # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1]     
       self.cfg_apersize=wartosc                          # TUTAJ


       tmp="background"                                     # TUTAJ
       wartosc="0"                                         # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1]     
       self.cfg_bcg=wartosc                          # TUTAJ

       tmp="zero_point"                                     # TUTAJ
       wartosc="40"                                         # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1]      
       self.cfg_zp=wartosc                          # TUTAJ

       #############################

       tmp="zoom_Z"                                     # TUTAJ
       wartosc=False                                         # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1]  
       self.cfg_zoom=wartosc                          # TUTAJ

       tmp="zoom_X"                                     # TUTAJ
       wartosc=False                                         # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1] 
       self.cfg_zoomX=wartosc                          # TUTAJ

       tmp="zoom_Y"                                     # TUTAJ
       wartosc=False                                         # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1] 
       self.cfg_zoomY=wartosc                          # TUTAJ

       ################################
       
       tmp="flip_X"                                     # TUTAJ
       wartosc=False                                         # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1]     
       self.cfg_flipX=eval(str(wartosc))                          # TUTAJ


       tmp="flip_Y"                                     # TUTAJ
       wartosc=False                                         # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1]   
       self.cfg_flipY=eval(str(wartosc))                          # TUTAJ


       tmp="rot90"                                     # TUTAJ
       wartosc=False                                         # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1]   
       self.cfg_rot90=eval(str(wartosc))                          # TUTAJ

       tmp="cmap"                                     # TUTAJ
       wartosc="gray"                                       # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1]         
       self.cfg_cmap=str(wartosc)                      # TUTAJ

       tmp="show_saturation"                                     # TUTAJ
       wartosc="True"                                       # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1]         
       self.cfg_showsat=eval(wartosc)                      # TUTAJ

       tmp="saturation"                                     # TUTAJ
       wartosc="50000"                                       # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1]         
       self.cfg_saturation=str(wartosc)                      # TUTAJ
       
       ############################3

       
       tmp="x_Col"                                     # TUTAJ
       wartosc=0                                         # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1] 
       try: int(wartosc)+1
       except: 
            self.errmssg("x_Col has wrong value!\n Set to '0' ") 
            wartosc=0      
       self.cfg_xCol=wartosc                          # TUTAJ

       tmp="y_Col"                                     # TUTAJ
       wartosc=1                                         # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1] 
       try: int(wartosc)+1
       except: 
            self.errmssg("y_Col has wrong value!\n Set to '0' ") 
            wartosc=0                    
       self.cfg_yCol=wartosc                          # TUTAJ   


       tmp="ext_Marker"                                     # TUTAJ
       wartosc=".g"                                         # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1]     
       self.cfg_extMarker=wartosc                          # TUTAJ   


       tmp="int_Marker"                                     # TUTAJ
       wartosc="xb"                                         # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1]     
       self.cfg_intMarker=wartosc                          # TUTAJ   
       

       tmp="hdr_keywords"                                     # TUTAJ
       wartosc=str((["OBJECT","HIERARCH ESO OBS NAME",],["RA",],["DEC",],["BAND","FILTER","FILTER2","HIERARCH ESO INS FILT1 NAME"],["TYPE","OBSTYPE","HIERARCH ESO DPR TYPE",],["TEL/INST","TELESCOP","INSTRUME",],["DIT","EXPTIME","HIERARCH ESO DET DIT","EXPOS"],["AIRMASS","HIERARCH ESO TEL AIRM START",],["DATE",]))                                         # TUTAJ
       
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1] 
       self.cfg_hdr_keywords=eval(wartosc)   # TUTAJ    

       tmp="save_chx"                                     # TUTAJ
       wartosc="(False,False,False)"                                         # TUTAJ
       for l in cfg_file: 
           if tmp in l: 
              wartosc=l.split("=")[1] 
       for x in self.args: 
           if tmp in x: 
              wartosc=x.split("=")[1]     
       self.cfg_save_chx=wartosc                          # TUTAJ  


       
class Communicate(QtCore.QObject):
      xPressed = QtCore.pyqtSignal(str,int,int)


class HeaderTab(QWidget):
   def __init__(self,parent,header): 
       QWidget.__init__(self)
       
       self.header=header
       self.filter_l=QLabel("Filter: ")

       self.filter_e=QLineEdit()
       self.filter_e.setText("") 
       self.filter_e.textChanged.connect(self.update)
       
       self.heder_e=QTextEdit()
       self.heder_e.setReadOnly(True)
       
       grid=QGridLayout()   
       grid.addWidget(self.filter_l,0,0)
       grid.addWidget(self.filter_e,0,1)
       grid.addWidget(self.heder_e,1,0,3,2)
       self.setLayout(grid)
       self.update()

   def update(self):       
       hdr=repr(self.header)
       hdr=hdr.split("\n")
       text=self.filter_e.text()
       txt=""
       for x in hdr:
           if str(text).lower() in str(x).lower(): txt=txt+str(x)+"\n"
       self.heder_e.setText(txt) 


class HelpWindow(QDialog):
  def __init__(self,parent,plik):
      QWidget.__init__(self)
      self.parent=parent
      self.setWindowTitle('Help')
      self.pole=QTextEdit()
      self.cl = QPushButton('Close', self)
      self.cl.clicked.connect(lambda: self.close())
       
       
       
      hbox1 = QHBoxLayout()
#      hbox1.addStretch(1)
      hbox1.addWidget(self.pole)
      hbox2 = QHBoxLayout()
      hbox2.addStretch(1)
      hbox2.addWidget(self.cl)
      vbox = QVBoxLayout()
#      vbox.addStretch(1)
      vbox.addLayout(hbox1)
      vbox.addLayout(hbox2)        
      self.setLayout(vbox) 

      gm=eval(str(self.parent.cfg_geometry))
      self.setGeometry(int(gm[1])+60,int(gm[1]+10),600,600)      

      
      try: f=open(plik,"r")
      except: 
           f=open(plik,"w+")
           txt=""
           txt=txt+"<b>This is help for FitsView </b><br>"+"\n"
           txt=txt+"<i>7.05.2020 Marek Gorski</i><br>"+"\n"
           txt=txt+"<h4>Initialization</h4>"+"\n"
           txt=txt+"connect push help button with function: help_window=HelpWindow(\"file.hlp\")"+"\n"
           txt=txt+"<ul>"+"\n"
           txt=txt+"<li>just use html text formating</li>"+"\n"           
           txt=txt+"</ul>"+"\n"
           txt=txt+"<p><b>Optiones</b> : not so many</p>"+"\n"
           txt=txt+"<ol>"+"\n"
           txt=txt+"<li>can add number list</li><br>"+"\n"
           txt=txt+"<li>with few points</li><br>"+"\n"
           txt=txt+"</ol>"+"\n"
           txt=txt+"<p><b>Help</b> : that's it</p>"+"\n"          

           f.write(txt) 
           f.close()
           f=open(plik,"r")
         
      self.text=f.read()
      self.pole.setReadOnly(1)
#      self.pole.setLineWrapMode(0)
      self.pole.setText(self.text)
      #self.pole.setMarkdown(self.text)
      #self.resize(600,500)
      self.show()
      

#==================================================================================
#
#
#==================================================================================

class Settings(QWidget):   # DEFINCE CONFIG
   def __init__(self,parent): 
       QWidget.__init__(self)
       self.parent=parent
       
       #print(self.parent.cfg_save_chx)
       self.parent.cfg_save_chx=eval(str(self.parent.cfg_save_chx))
       self.geometry_c=QCheckBox("Save App window settings")   
       if self.parent.cfg_save_chx[0]: self.geometry_c.setChecked(True)
       self.display_c=QCheckBox("Save Image display settings") 
       if self.parent.cfg_save_chx[1]: self.display_c.setChecked(True)
       self.zoom_c=QCheckBox("Save Zoom settings")        
       if self.parent.cfg_save_chx[2]: self.zoom_c.setChecked(True)


       
       self.apsize_l=QLabel("Aperture size: ")
       self.apsize_e=QLineEdit()
       self.apsize_e.setText(str(self.parent.cfg_apersize))

       self.bcg_l=QLabel("Background level: ")
       self.bcg_e=QLineEdit()
       self.bcg_e.setText(str(self.parent.cfg_bcg))

       self.zp_l=QLabel("Zero point: ")
       self.zp_e=QLineEdit()
       self.zp_e.setText(str(self.parent.cfg_zp))

        

       self.xcol_l=QLabel("X column: ")
       self.xcol_e=QLineEdit()
       self.xcol_e.setText(str(self.parent.cfg_xCol))

       self.ycol_l=QLabel("Y column: ")
       self.ycol_e=QLineEdit()
       self.ycol_e.setText(str(self.parent.cfg_yCol))
       
       self.mk1_l=QLabel("Marker 1 symbol: ")
       self.mk1_e=QLineEdit()
       self.mk1_e.setText(self.parent.cfg_extMarker)       

       self.mk2_l=QLabel("Marker 2 symbol: ")
       self.mk2_e=QLineEdit()
       self.mk2_e.setText(self.parent.cfg_intMarker)             

       self.update_p = QPushButton("Update CFG")
       self.update_p.clicked.connect(self.update_cfg)


       self.save_p = QPushButton("Save CFG")
       self.save_p.clicked.connect(self.save_cfg)

       self.close_p = QPushButton("Close")
       self.close_p.clicked.connect(self.close_cfg)

       grid=QGridLayout()  
       w=0
       grid.addWidget(self.geometry_c,w,0)
       w=w+1
       grid.addWidget(self.display_c,w,0)
       w=w+1
       grid.addWidget(self.zoom_c,w,0)

       w=w+1
       grid.addWidget(self.apsize_l,w,0)
       grid.addWidget(self.apsize_e,w,1)       
       w=w+1       
       grid.addWidget(self.bcg_l,w,0)
       grid.addWidget(self.bcg_e,w,1)  
       w=w+1
       grid.addWidget(self.zp_l,w,0)
       grid.addWidget(self.zp_e,w,1)         

       w=w+1
       grid.addWidget(self.xcol_l,w,0)
       grid.addWidget(self.xcol_e,w,1)  
       w=w+1
       grid.addWidget(self.ycol_l,w,0)
       grid.addWidget(self.ycol_e,w,1)  
       w=w+1
       grid.addWidget(self.mk1_l,w,0)
       grid.addWidget(self.mk1_e,w,1)   
       w=w+1
       grid.addWidget(self.mk2_l,w,0)
       grid.addWidget(self.mk2_e,w,1)   
       w=w+1       
       grid.addWidget(self.update_p,w,0)
       grid.addWidget(self.save_p,w,1)
       w=w+1
       grid.addWidget(self.close_p,w,1)
       
       self.setLayout(grid)       
       
   
   def update(self):     # CONFIG WINDOW UPDATE
       
       tmp=4
       #self.parent.cfg_geometry=self.parent.geometry().getRect()


   def update_cfg(self):       
       self.parent.cfg_apersize=int(self.apsize_e.text())
       self.parent.cfg_bcg = float(self.bcg_e.text())
       self.parent.cfg_zp = float(self.zp_e.text())

       self.parent.cfg_xCol = int(self.xcol_e.text())
       self.parent.cfg_yCol = int(self.ycol_e.text())
       self.parent.cfg_extMarker = str(self.mk1_e.text())
       self.parent.cfg_intMarker = str(self.mk2_e.text())
        
       for x in self.parent.tab: x.update()   
       


       
   def save_cfg(self):        # CONFIG SAVE
       
       cfg_fname=self.parent.pwd+"FitsView.cfg"     
       cfg_file=open(cfg_fname,"w+")
       chx1,chx2,chx3=False,False,False
       txt=""
       
       if self.geometry_c.checkState():
          chx1=True
          self.parent.cfg_geometry=self.parent.geometry().getRect()
          txt=txt+"geometry="+str(self.parent.cfg_geometry)+"\n"
          txt=txt+"active_tab="+str(self.parent.cfg_active_tab)+"\n"

       if self.display_c.checkState():
          chx2=True
          txt=txt+"flip_X="+str(self.parent.cfg_flipX)+"\n"
          txt=txt+"flip_Y="+str(self.parent.cfg_flipY)+"\n"    
          txt=txt+"rot90="+str(self.parent.cfg_rot90)+"\n"          
          txt=txt+"cmap="+str(self.parent.cfg_cmap)+"\n"
          txt=txt+"show_saturation="+str(self.parent.cfg_showsat)+"\n"
          txt=txt+"saturation="+str(self.parent.cfg_saturation)+"\n"          

       
       if self.zoom_c.checkState():
          chx3=True
          txt=txt+"zoom_Z="+str(self.parent.cfg_zoom)+"\n"
          txt=txt+"zoom_X="+str(self.parent.cfg_zoomX)+"\n"
          txt=txt+"zoom_Y="+str(self.parent.cfg_zoomY)+"\n"


       txt=txt+"aper_size="+str(self.apsize_e.text())+"\n"
       txt=txt+"background="+str(self.bcg_e.text())+"\n"
       txt=txt+"zero_point="+str(self.zp_e.text())+"\n"

       txt=txt+"x_Col="+str(self.xcol_e.text())+"\n"
       txt=txt+"y_Col="+str(self.ycol_e.text())+"\n"
       txt=txt+"ext_Marker="+str(self.mk1_e.text())+"\n"
       txt=txt+"int_Marker="+str(self.mk2_e.text())+"\n"
       self.parent.cfg_save_chx=(chx1,chx2,chx3)
       txt=txt+"save_chx="+str(self.parent.cfg_save_chx)+"\n"       
       txt=txt+"hdr_keywords="+str(self.parent.cfg_hdr_keywords)+"\n"

       
       cfg_file.write(txt)
       cfg_file.close()

   def close_cfg(self):        # CONFIG SAVE
       self.close()
