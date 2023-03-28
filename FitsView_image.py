#!/usr/bin/env python3

#----------------
# 23.03.2022
# Marek Gorski
#----------------


import matplotlib, numpy
import matplotlib.patches as patches
from astropy.io import fits

from matplotlib import cm
from matplotlib.figure import Figure


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


from scipy.optimize import curve_fit

from FitsView_widgets import *

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel,QCheckBox, QTextEdit, QMessageBox, QLineEdit, QDialog, QTabWidget, QPushButton, QFileDialog, QGridLayout, QHBoxLayout, QVBoxLayout, QInputDialog,QComboBox, QSlider
from PyQt5 import QtCore, QtGui
 
        
class Image(QWidget):
   def __init__(self,parent,hdu): 
       QWidget.__init__(self)
       

       self.int_x=[]
       self.int_y=[]
       self.parent=parent
       self.dane = numpy.nan_to_num(hdu.data, nan=0)  
       self.hdr=hdu.header
       
       self.text_window=False
       self.r_window=False
       self.c_window=False
       self.e_window=False
       
       self.optiones=False

       
       self.hline=False
       self.vline=False


       self.mkUI()
       self.initiatie()
       #self.update()
       #self.reset_viewfinder()
       self.clim_auto()
       #self.fit_image()
       self.update_cfg()
       self.show_optiones()
       


       self.savePic_p.clicked.connect(self.save_pic)
       self.header_p .clicked.connect(self.show_header)
       self.zoom_s.valueChanged.connect(self.zmiana_zoom)
       self.auto_p.clicked.connect(self.clim_auto)
       self.max_s.valueChanged.connect(self.zmiana_vmax)
       self.min_s.valueChanged.connect(self.zmiana_vmin)
       self.max_e.textChanged.connect(self.change_clim)
       self.min_e.textChanged.connect(self.change_clim)
       self.fitI_p.clicked.connect(self.fit_image)
       self.shopt_p.clicked.connect(self.show_optiones)
       self.showM_c.stateChanged.connect(self.update)
       self.rot90_c.stateChanged.connect(self.zmiana_rot90)
       self.flipX_c.stateChanged.connect(self.zmiana_flipX)
       self.flipY_c.stateChanged.connect(self.zmiana_flipY)
       self.mksize_s.valueChanged.connect(self.update)
       self.saturation_c.stateChanged.connect(self.zmiana_saturation)
       self.cmap_s.currentIndexChanged.connect(self.zmiana_cmap)
       self.saturation_e.editingFinished.connect(self.zmiana_saturation)
       

   def initiatie(self):
       self.x=int(len(self.dane[0])/2)
       self.y=int(len(self.dane)/2)   
       self.saturation_e.setText(str(self.parent.cfg_saturation))
       index = self.cmap_s.findText(str(self.parent.cfg_cmap).strip())
       self.cmap_s.setCurrentIndex(index) 
   
   def zmiana_saturation(self):
       if self.saturation_c.checkState(): self.parent.cfg_showsat=True
       else: self.parent.cfg_showsat=False
       try: self.parent.cfg_saturation=float(self.saturation_e.text())
       except: 
            print("saturation have to be a number!!!")
            self.parent.cfg_saturation=60000
            self.saturation_e.setText(str(self.parent.cfg_saturation))
       self.update()
   
   def show_optiones(self):
    
       if self.optiones:
          self.shopt_p.setText("Hide optiones")
          self.saturation_c.show()
          self.saturation_e.show()
          self.flipX_c.show()
          self.flipY_c.show()
          self.rot90_c.show()
          self.mksize_l.show()
          self.mksize_s.show()
          self.savePic_p.show()
          self.showM_c.show()
          self.cmap_l.show()
          self.cmap_s.show()   
          self.min_e.show()
          self.min_s.show()
          self.max_e.show()
          self.max_s.show()
          self.auto_p.show()
          self.optiones=False
       else:    
          self.shopt_p.setText("Show optiones")     
          self.saturation_c.hide()
          self.saturation_e.hide()
          self.flipX_c.hide()
          self.flipY_c.hide()
          self.rot90_c.hide()
          self.mksize_l.hide()
          self.mksize_s.hide()       
          self.savePic_p.hide()
          self.showM_c.hide()
          self.cmap_l.hide()
          self.cmap_s.hide()  
          self.min_e.hide()
          self.min_s.hide()
          self.max_e.hide()
          self.max_s.hide()
          self.auto_p.hide()
          self.optiones=True


   def update(self): 
     
       #try: self.axes.lines[-1].remove()
       #except: pass     
       
       if self.parent.cfg_showsat: self.saturation_c.setChecked(True)
       else: self.saturation_c.setChecked(False)
     
       if self.parent.cfg_flipX: self.flipX_c.setChecked(True)
       else: self.flipX_c.setChecked(False)
       
       if self.parent.cfg_flipY: self.flipY_c.setChecked(True)
       else: self.flipY_c.setChecked(False)       

       if self.parent.cfg_rot90: self.rot90_c.setChecked(True)
       else: self.rot90_c.setChecked(False)
       
       if self.parent.cfg_rot90: 
          dane=numpy.rot90(self.dane)
       else: dane=self.dane

       vmin=self.min_s.value()
       vmax=self.max_s.value()

       self.axes.clear()
       self.axes.set_xticks([])
       self.axes.set_yticks([])       
      
       if ("3.3.0">matplotlib.__version__):
          mymap = cm.get_cmap(self.parent.cfg_cmap.strip())
       else: mymap = cm.get_cmap(self.parent.cfg_cmap.strip()).copy()
       
       dane2=dane.copy()
       
       #if self.parent.cfg_showsat:
       #   sat = float(self.parent.cfg_saturation)
       #   dane2[dane>=sat]="nan"
       #   mymap.set_bad("red")
       
       self.image = self.axes.imshow(dane2,cmap=mymap,vmin=vmin, vmax=vmax,interpolation="None")
       
       if self.hline:
          self.axes.axhline(y=self.hline,color="r",alpha=0.5)
          self.hline=False

       if self.vline:
          self.axes.axvline(x=self.vline,color="r",alpha=0.5)
          self.vline=False          
       
       self.ext_x=self.parent.ext_x
       self.ext_y=self.parent.ext_y
       
       
       if self.showM_c.checkState():
          mksize=int(self.mksize_s.value()/10.)+1 
          if len(self.ext_x)>0:
             try:
                if self.parent.cfg_rot90: 
                   self.axes.plot(self.ext_y,float(len(dane))-numpy.array(self.ext_x),str(self.parent.cfg_extMarker).strip(),markersize=mksize,mfc='none')
                else: self.axes.plot(self.ext_x,self.ext_y,str(self.parent.cfg_extMarker).strip(),markersize=mksize,mfc='none')
             except ValueError: 
                self.msg = QMessageBox()
                self.msg.setText("'"+self.parent.cfg_extMarker.strip()+"'"+ " is not a proper marker style\nCheck configuration!")   
                self.msg.exec_()


          mksize=mksize+2 
          if len(self.int_x)>0:
             try:
                if self.parent.cfg_rot90: 
                   self.axes.plot(self.int_y,float(len(dane))-numpy.array(self.int_x),str(self.parent.cfg_intMarker).strip(),markersize=mksize,alpha=0.5,mfc='none')
                else: self.axes.plot(self.int_x,self.int_y,str(self.parent.cfg_intMarker).strip(),markersize=mksize,alpha=0.5,mfc='none')
             except ValueError: 
                self.msg = QMessageBox()
                self.msg.setText("'"+self.parent.cfg_intMarker.strip()+"'"+ " is not a proper marker style\nCheck configuration!")   
                self.msg.exec_()       

       self.canvas.draw()

       mymap = cm.get_cmap(self.parent.cfg_cmap.strip())
       dane2=dane.copy()

       self.axes_small.clear()
       self.image_small = self.axes_small.imshow(dane2,cmap=mymap,vmin=vmin, vmax=vmax,interpolation="None",aspect="equal",origin='lower')        
       self.axes_small.set_xticks([])
       self.axes_small.set_yticks([])    
       

       self.canvas_small.draw()
       
       self.zmiana_zoom()
       self.reset_viewfinder()
       
   def reset_viewfinder(self):
     
       if self.parent.cfg_rot90: 
          dane=numpy.rot90(self.dane)
       else: dane=self.dane

       vmin=self.min_s.value()
       vmax=self.max_s.value()     
       
       if ("3.3.0">matplotlib.__version__):
          mymap = cm.get_cmap(self.parent.cfg_cmap.strip())
       else:  mymap = cm.get_cmap(self.parent.cfg_cmap.strip()).copy()
       dane2=dane.copy()      

       #if self.parent.cfg_showsat:
       #   sat = float(self.parent.cfg_saturation)
       #   dane2[dane>=sat]="nan"
       #   mymap.set_bad("red")
     
       self.axes_viewfinder.clear()
       self.image_viewfinder = self.axes_viewfinder.imshow(dane2,cmap=mymap,vmin=vmin, vmax=vmax,interpolation="None",aspect="equal")       
       self.axes_viewfinder.set_xticks([])
       self.axes_viewfinder.set_yticks([])
       self.canvas_viewfinder.draw()   
   

   def change_clim(self):

       a=self.min_e.text()
       b=self.max_e.text()
       try:
          float(a)
          float(b)
          ok=True
       except: ok=False
       if a<b and ok:
          self.min_s.setRange(int(float(a)),int(float(b)))
          self.max_s.setRange(int(float(a)),int(float(b)))

   def clim_auto(self): 
       c0 = numpy.median(self.dane,axis=None)
       c_sigma=numpy.std(self.dane,axis=None)
       if c_sigma==numpy.inf: c_sigma=5.
       self.min_e.setText("%i"%(c0-5*c_sigma))
       self.max_e.setText("%i"%(c0+5*c_sigma))
       a=self.min_e.text()
       b=self.max_e.text()
       self.min_s.setRange(int(float(a)),int(float(b)))
       self.max_s.setRange(int(float(a)),int(float(b)))
       self.min_s.setValue(int(c0-c_sigma))
       self.max_s.setValue(int(c0+c_sigma))

   def fit_image(self):
       self.zoom_s.setValue(1)
       self.x=int(len(self.dane[0])/2)
       self.y=int(len(self.dane)/2)
       self.zmiana_zoom()

   def zmiana_zoom(self):
     
       z=len(self.dane[0]) - self.zoom_s.value() + 1
       z=int(z/2.)
       x0=self.x
       y0=self.y
       
       if self.parent.cfg_flipX: self.axes.set_xlim(x0+z,x0-z)
       else: self.axes.set_xlim(x0-z,x0+z)
       if self.parent.cfg_flipY: self.axes.set_ylim(y0+z,y0-z)
       else: self.axes.set_ylim(y0-z,y0+z)
       self.canvas.draw()
       
       try: self.rectangle.remove()
       except: pass
       #try: self.axes.lines[-1].remove()
       #except: pass
     
       x1,x2 = self.axes.get_xlim()
       y1,y2 = self.axes.get_ylim()
       dx=x2-x1
       dy=y2-y1
       
       self.rectangle=patches.Rectangle((x1,y1),dx,dy,linewidth=0.8,edgecolor='r',facecolor='none')
       self.axes_small.add_patch(self.rectangle)

       if self.parent.cfg_flipX: self.axes_small.set_xlim(len(self.dane[0]),0)
       else: self.axes_small.set_xlim(0,len(self.dane[0]))
       if self.parent.cfg_flipY: self.axes_small.set_ylim(len(self.dane),0)
       else: self.axes_small.set_ylim(0,len(self.dane))       
       
       
       self.canvas_small.draw()

   def update_cfg(self):

       self.zoom_s.setValue(int(float(self.parent.cfg_zoom)))
       if self.parent.cfg_zoomX: self.x=float(self.parent.cfg_zoomX)
       if self.parent.cfg_zoomY: self.y=float(self.parent.cfg_zoomY) 
       
       self.zmiana_zoom()


   def mouse_move(self,event):
       try:
          x=event.xdata
          y=event.ydata
          self.update_viewfinder(x,y)
       except: pass

   def update_viewfinder(self,x,y):
       x=x
       y=y
       
       wsize=2*int(self.parent.cfg_apersize)+15
       apersize=int(self.parent.cfg_apersize)
          
       counts=self.dane[int(y)][int(x)]
       if self.parent.cfg_rot90: counts=self.dane[int(x)][int(len(self.dane[0])-y)] 
       
       txt = "%.2f %.2f %d"% (x,y,counts)
       if self.parent.cfg_rot90: txt = "%.2f %.2f %d"% (float(len(self.dane[0])-y),x,counts)
       self.coor_l.setText(txt)   
       
       try: 
         self.axes_viewfinder.lines[-1].remove()
         self.axes_viewfinder.lines[-1].remove()
         self.aperture.remove()            
       except: pass
       self.axes_viewfinder.set_xlim(x-wsize,x+wsize)
       self.axes_viewfinder.set_ylim(y-wsize,y+wsize)
       
       if self.parent.cfg_flipX: self.axes_viewfinder.set_xlim(x+wsize,x-wsize)
       else: self.axes_viewfinder.set_xlim(x-wsize,x+wsize)
       if self.parent.cfg_flipY: self.axes_viewfinder.set_ylim(y+wsize,y-wsize)
       else: self.axes_viewfinder.set_ylim(y-wsize,y+wsize)          
       
       self.axes_viewfinder.axvline(x=x,color="g",alpha=1)
       self.axes_viewfinder.axhline(y=y,color="g",alpha=1)
       
       self.aperture=patches.Circle((x,y),radius=int(self.parent.cfg_apersize),linewidth=0.5,edgecolor='g',facecolor='none')
       self.axes_viewfinder.add_patch(self.aperture)    
       
                
       self.canvas_viewfinder.draw()
       self.canvas.setFocus()

   def image_clicked(self,event):
       self.x = event.xdata
       self.y = event.ydata
       self.zmiana_zoom()

   def zmiana_flipX(self):
       if self.flipX_c.checkState(): self.parent.cfg_flipX=True
       else: self.parent.cfg_flipX=False
       self.zmiana_zoom()

   def zmiana_flipY(self):
       if self.flipY_c.checkState(): self.parent.cfg_flipY=True
       else: self.parent.cfg_flipY=False
       self.zmiana_zoom()

   def zmiana_rot90(self):
       if self.rot90_c.checkState(): 
          self.parent.cfg_rot90=True
          x,y=self.x,self.y          
          self.x=y
          self.y=len(self.dane)-x               
       else: 
          self.parent.cfg_rot90=False
          x,y=self.x,self.y
          self.x=len(self.dane)-y
          self.y=x

       self.update()
       
   def zmiana_cmap(self):
       self.parent.cfg_cmap=str(self.cmap_s.currentText())
       self.update()

 
   def zmiana_vmin(self): 
       vmin=self.min_s.value()
       vmax=self.max_s.value()
       
       if vmin>vmax: 
          vmax=vmin+0.1
          self.max_s.setValue(int(vmax))
        
       self.image.set_clim(vmin=vmin,vmax=vmax)
       self.image_viewfinder.set_clim(vmin=vmin,vmax=vmax)
       self.image_small.set_clim(vmin=vmin,vmax=vmax)
       self.canvas.draw()
       self.canvas_viewfinder.draw()
       self.canvas_small.draw()

   def zmiana_vmax(self): 
       vmin=self.min_s.value()
       vmax=self.max_s.value()
       
       if vmax<vmin: 
          vmin=vmax-0.1
          self.min_s.setValue(int(vmin))
       
       self.image.set_clim(vmin=vmin,vmax=vmax)
       self.image_viewfinder.set_clim(vmin=vmin,vmax=vmax)
       self.image_small.set_clim(vmin=vmin,vmax=vmax)       
       self.canvas.draw()
       self.canvas_viewfinder.draw()
       self.canvas_small.draw()

   def save_pic(self):
       
       txt="./"+str(self.parent.fname).split(".")[0]+".png"
       sfile = str( QFileDialog.getSaveFileName(self, 'Save as',txt)[0] )
       print(sfile)
       self.fig.savefig(sfile,dpi=300)
       #self.fig.savefig("dupa.png",dpi=300)
       #avefig(fname, dpi=None, facecolor='w', edgecolor='w',  orientation='portrait', papertype=None, format=None, 
       #transparent=False, bbox_inches=None, pad_inches=0.1,
       #frameon=None, metadata=None)

 
   def show_header(self): 
       self.hdrl_window=HeaderTabLocal(self,self.hdr)  
       self.parent.active_windows.append(self.hdrl_window)

       
       
   def keypressed(self,event):
       if not self.text_window: 
          self.text_window=TextWindow(self)
          self.parent.active_windows.append(self.text_window)

       x=event.xdata
       y=event.ydata
       xr,yr=x,y
       
       if self.parent.cfg_rot90:
          xr=len(self.dane[0])-y
          yr=x

       if self.parent.special:
          self.parent.com.xPressed.emit(event.key,xr,yr)


       if "m" in event.key: 
          self.int_x.append(xr)
          self.int_y.append(yr)
          self.update()
          counts=self.dane[int(y)][int(x)]
          txt=str(xr)+" "+str(yr)+" "+str(counts)+" m"
          txt2 = "marked x=%.2f y=%.2f counts=%d"%(xr,yr,counts) 
          self.text_window.txt=txt2
          self.text_window.update()
          print(txt)

          
       if "s" in event.key: 
          self.int_x.append(xr)
          self.int_y.append(yr)
          self.update()

          
          x1,x2 = self.axes.get_xlim()
          if x1<0: x1=0
          if x2>len(self.dane[int(y),:])-1: x2=len(self.dane[int(y),:])-1

          y1,y2 = self.axes.get_ylim()
          if y1<0: y1=0
          if y2>len(self.dane[:,int(x)])-1: y2=len(self.dane[:,int(x)])-1
             
          dane=self.dane[int(y1):int(y2),int(x1):int(x2)]

          txt = "selected x=(%.2f,%.2f)  y=(%.2f,%.2f)\n"%(x1,x2,y1,y2) 
          txt = txt+"min: %.2f\n"%(dane.min()) 
          txt = txt+"max: %.2f\n"%(dane.max()) 
          txt = txt+"mean: %.2f\n"%(numpy.mean(dane)) 
          txt = txt+"median: %.2f\n"%(numpy.median(dane)) 
          txt = txt+"spread: %.2f\n"%(numpy.std(dane))           

          self.text_window.txt=txt
          self.text_window.update()
          print(txt)
             
          
          
       if "d" in event.key and not self.parent.special:
          if len(self.int_x)>0:
             diffx = numpy.array(self.int_x)-float(xr)
             diffy = numpy.array(self.int_y)-float(yr)
             diff=diffx**2+diffy**2
             n=numpy.argmin(diff)
             del self.int_x[n] 
             del self.int_y[n] 
             self.update()          

       if "f" in event.key:
          diffx = numpy.array(self.ext_x)-float(xr)
          diffy = numpy.array(self.ext_y)-float(yr)
          diff=diffx**2+diffy**2
          n=numpy.argmin(diff)
          x=self.ext_x[n]
          y=self.ext_y[n]
          self.int_x.append(x)
          self.int_y.append(y)
          self.update()
          txt = self.parent.ext_l[n]
          self.text_window.txt=txt
          self.text_window.update()
          print(txt)        

       if "b" in event.key:
          r=int(self.parent.cfg_apersize)
          dane = self.dane[int(y)-r:int(y)+r,int(x)-r:int(x)+r]
          x0=(len(dane[0])/2.)
          y0=(len(dane)/2.)        
          XX,YY = numpy.meshgrid(numpy.arange(dane.shape[1]),numpy.arange(dane.shape[0]))
          tmp = numpy.vstack((dane.ravel(),XX.ravel(),YY.ravel()))         
          c,xx,yy=tmp[0],tmp[1],tmp[2]
          d=((xx-x0)**2+(yy-y0)**2)**0.5
          mk=d<r
          aper = c[mk]
          bc = aper.sum()/len(aper)
          self.parent.cfg_bcg=str(bc)
          txt2=str(xr)+" "+str(yr)+" "+str(bc)+" b"
          txt="background level around x=%.1f y=%.1f measured: %.2f / pixel "%(xr,yr,bc)
          self.int_x.append(xr)
          self.int_y.append(yr)
          self.update()
          self.text_window.txt=txt
          self.text_window.update()
          print(txt2)
          

       if "q" in event.key:
          r=int(self.parent.cfg_apersize)
          dane = self.dane[int(y)-r:int(y)+r,int(x)-r:int(x)+r]
          x0=(len(dane[0])/2.)
          y0=(len(dane)/2.) 
          XX,YY = numpy.meshgrid(numpy.arange(dane.shape[1]),numpy.arange(dane.shape[0]))
          tmp = numpy.vstack((dane.ravel(),XX.ravel(),YY.ravel()))         
          c,xx,yy=tmp[0],tmp[1],tmp[2]       
          d=((xx-x0)**2+(yy-y0)**2)**0.5
          mk=d<r
          aper = c[mk]
          zliczenia = aper.sum() - len(aper) * float(self.parent.cfg_bcg)         
          mag = -2.5*numpy.log10(zliczenia) + float(self.parent.cfg_zp)
          txt2="%.1f %.1f %d %.2f q "%(xr,yr,zliczenia,mag)
          txt="centered x=%.1f y=%.1f : counts=%d m=%.2f  "%(xr,yr,zliczenia,mag)
          self.int_x.append(xr)
          self.int_y.append(yr)
          self.update()
          self.text_window.txt=txt
          self.text_window.update()
          print(txt2)

       if "z" in event.key:
          r=int(self.parent.cfg_apersize)
          dane = self.dane[int(y)-r:int(y)+r,int(x)-r:int(x)+r]
          x1=(len(dane[0])/2.)
          y1=(len(dane)/2.) 
          XX,YY = numpy.meshgrid(numpy.arange(dane.shape[1]),numpy.arange(dane.shape[0]))
          tmp = numpy.vstack((dane.ravel(),XX.ravel(),YY.ravel()))         
          c,xx,yy=tmp[0],tmp[1],tmp[2]
           
          x0=numpy.sum(c*xx)/( numpy.sum(c) )
          y0=numpy.sum(c*yy)/( numpy.sum(c) ) 
          x=x+(x0-x1)
          y=y+(y0-y1)
          
          dane = self.dane[int(y)-r:int(y)+r,int(x)-r:int(x)+r]
          XX,YY = numpy.meshgrid(numpy.arange(dane.shape[1]),numpy.arange(dane.shape[0]))
          tmp = numpy.vstack((dane.ravel(),XX.ravel(),YY.ravel()))         
          c,xx,yy=tmp[0],tmp[1],tmp[2]          
          d=((xx-x0)**2+(yy-y0)**2)**0.5
          mk=d<r
          aper = c[mk]
          zliczenia = aper.sum() - len(aper) * float(self.parent.cfg_bcg)

          mag = -2.5*numpy.log10(zliczenia) + float(self.parent.cfg_zp)
          
          m_std=mag
          m_std, ok = QInputDialog.getText(self, 'Zero point', 'Enter star magnitude:')
          d=float(m_std)-mag
          self.parent.cfg_zp=str(float(self.parent.cfg_zp)+d)
          txt2="%.3f z"%(float(self.parent.cfg_zp))
          txt="zero point set to %.3f"%(float(self.parent.cfg_zp))
          
          self.int_x.append(xr)
          self.int_y.append(yr)
          self.update()
          self.text_window.txt=txt
          self.text_window.update()
          print(txt2)            

       if "g" in event.key:
          xy, ok = QInputDialog.getText(self, 'Go To', 'Enter X Y:')
          if "," in xy: x,y = float(str(xy).split(",")[0]),float(str(xy).split(",")[1])
          else: x,y = float(str(xy).split()[0]),float(str(xy).split()[1])
          xr,yr=x,y
          if self.parent.cfg_rot90:
             xr=y
             yr=len(self.dane)-x
          self.x = xr
          self.y = yr
          self.zmiana_zoom()
          self.int_x.append(xr)
          self.int_y.append(yr)
          self.update()
          txt2=str(x)+" "+str(y)+" g" 
          txt="Marked x=%.1f y=%.1f"%(x,y)
          self.text_window.txt=txt
          self.text_window.update()
          print(txt2)     


       if "l" in event.key:
          if not self.c_window: 
             self.c_window=PlotWindow(self) 
             self.parent.active_windows.append(self.c_window)   
          self.c_window.show()
          self.c_window.raise_()  
          #try: self.axes.lines[-1].remove()
          #except: pass
          
          x1,x2 = self.axes.get_xlim()
          if x1<0: x1=0
          if x2>len(self.dane[int(y),:])-1: x2=len(self.dane[int(y),:])-1
          
          yyy=self.dane[int(y),int(x1):int(x2)]
          xxx=numpy.arange(x1,x1+len(yyy),1)
          
          self.c_window.axes.clear()
          self.c_window.axes.plot(xxx,yyy)
          self.c_window.canvas.draw()
          
          self.hline=y
          self.update()

          txt="line y=%.2f   "%(y)
          self.text_window.txt=txt
          self.text_window.update()
          self.c_window.txt=txt
          self.c_window.update()
          self.c_window.raise_()          
          print(txt)



       if "c" in event.key:
          if not self.c_window: 
             self.c_window=PlotWindow(self)   
             self.parent.active_windows.append(self.c_window)  
          self.c_window.show()
          self.c_window.raise_()  
          #try: self.axes.lines[-1].remove()
          #except: pass

          y1,y2 = self.axes.get_ylim()
          if y1<0: y1=0
          if y2>len(self.dane[:,int(x)])-1: y2=len(self.dane[:,int(x)])-1
             
          yyy=self.dane[int(y1):int(y2),int(x)]
          xxx=numpy.arange(y1,y1+len(yyy),1)
          
          self.c_window.axes.clear()
          self.c_window.axes.plot(xxx,yyy)
          self.c_window.canvas.draw()
          
          self.vline=x
          self.update()

          txt="column x=%.2f "%(x)
          self.text_window.txt=txt
          self.text_window.update()
          self.c_window.txt=txt
          self.c_window.update()
          self.c_window.raise_()
          print(txt)

       if "e" in event.key:
         
          if not self.e_window: 
             self.e_window=PlotWindow(self) 
             self.parent.active_windows.append(self.e_window)        

          self.e_window.show()
          self.e_window.raise_()  

         
          r=int((2*int(self.parent.cfg_apersize)+15)/2.) 
      
          dane = self.dane[int(y)-r:int(y)+r,int(x)-r:int(x)+r]
          x1=(len(dane[0])/2.)
          y1=(len(dane)/2.) 

      
          
          XX,YY = numpy.meshgrid(numpy.arange(dane.shape[1]),numpy.arange(dane.shape[0]))
          tmp = numpy.vstack((dane.ravel(),XX.ravel(),YY.ravel()))         
          c,xx,yy=tmp[0],tmp[1],tmp[2]
          c=c-float(self.parent.cfg_bcg)
           
     
                  
          
          self.e_window.axes.clear()
          self.e_window.axes.contour(dane)

          self.e_window.canvas.draw()
          
          txt="centered x=%.2f y=%.2f   "%(xr,yr)
          self.int_x.append(xr)
          self.int_y.append(yr)
          self.update()
          self.text_window.txt=txt
          self.text_window.update()

          self.e_window.txt=txt
          self.e_window.update()
          self.e_window.raise_()
          
          print(txt)

       if "r" in event.key:
         
          if not self.r_window: 
             self.r_window=PlotWindow(self) 
             self.parent.active_windows.append(self.r_window)        

          self.r_window.show()
          self.r_window.raise_()  
         
          r=int(self.parent.cfg_apersize)
          
          dane = self.dane[int(yr)-r:int(yr)+r,int(xr)-r:int(xr)+r]
          x1=(len(dane[0])/2.)
          y1=(len(dane)/2.) 

          xy = numpy.unravel_index(dane.argmax(), dane.shape)
          dx=x1-xy[1]
          dy=y1-xy[0]
          xr=int(xr)-dx
          yr=int(yr)-dy
          
          dane = self.dane[int(yr)-r:int(yr)+r,int(xr)-r:int(xr)+r]
          x1=(len(dane[0])/2.)
          y1=(len(dane)/2.)           
          
          XX,YY = numpy.meshgrid(numpy.arange(dane.shape[1]),numpy.arange(dane.shape[0]))
          tmp = numpy.vstack((dane.ravel(),XX.ravel(),YY.ravel()))         
          c,xx,yy=tmp[0],tmp[1],tmp[2]        
          
          if numpy.min(c)<0 : waga = (c + numpy.min(c) )**2
          else: waga = (c - numpy.min(c) )**2

          x0=numpy.sum(waga*xx)/( numpy.sum(waga) ) 
          y0=numpy.sum(waga*yy)/( numpy.sum(waga) ) 
          dx=float(x1)-x0
          dy=float(y1)-y0
          xr=float(xr-dx)
          yr=float(yr-dy) 
          
          
          d=((xx-x0)**2+(yy-y0)**2)**0.5
          print(numpy.min(d))
          mk=d<r
          c = c[mk]
          d = d[mk]
                    
          popt,pcov = curve_fit(self.gaus,d,c,p0=[1,2,0])
          
          xx=numpy.arange(0,d.max(),0.01)
          yy=self.gaus(xx,popt[0],popt[1],popt[2]) 
          sky = popt[2]
          sigma=(popt[1]**2)**0.5
          fwhm=2.355*sigma
          
          self.r_window.axes.clear()
          self.r_window.axes.plot(d,c,".g")

          self.r_window.axes.plot(xx,yy)
          self.r_window.canvas.draw()
          txt2="%.2f %.2f  %.2f r  "%(xr,yr,fwhm)
          txt="centered x=%.2f y=%.2f FWHM= %.2f   "%(xr,yr,fwhm)
          self.int_x.append(xr)
          self.int_y.append(yr)
          self.update()
          self.text_window.txt=txt
          self.text_window.update()

          self.r_window.txt=txt
          self.r_window.update()
          self.r_window.raise_()
          
          print(txt2)

       self.update_viewfinder(x,y)


   def gaus(self,x,a,sigma,c0):
       x0=0
       return a*numpy.exp(-(x-x0)**2/(2*sigma**2))+c0

   def mkUI(self):       

       self.coor_l=QLabel()
       #self.coor_l=QLineEdit()          

       self.shopt_p = QPushButton('Show Optiones')

       self.flipX_c = QCheckBox("Flip X")
       self.flipX_c.setChecked(False)
       self.flipY_c = QCheckBox("Flip Y")
       self.flipY_c.setChecked(False)       
       self.rot90_c = QCheckBox("Rotate 90")
       self.rot90_c.setChecked(False)

       self.mksize_l=QLabel("Marker Size:")
       self.mksize_s= QSlider(QtCore.Qt.Horizontal)
       self.mksize_s.setRange(int(0),int(200))
       #self.mksize_s.setTickInterval(1)
       self.mksize_s.setValue(25)
       

       self.cmap_l=QLabel("Cmap: ")
       self.cmap_s=QComboBox()
       self.cmap_s.addItems(['gray','binary','gist_heat', 'seismic','viridis'])
       
       self.saturation_c = QCheckBox("Saturation")
       self.saturation_c.setChecked(True)       
       self.saturation_e=QLineEdit()
       self.saturation_e.setText("60000")
       
       self.showM_c =  QCheckBox("Show Markers")
       self.showM_c.setChecked(True)
       
       self.fitI_p =  QPushButton('Fit Image')
       
       self.max_e= QLineEdit()
       #self.max_e.setReadOnly(True)
       self.min_e= QLineEdit()
       #self.min_e.setReadOnly(True)

       c0 = numpy.median(self.dane,axis=None)
       c_sigma=numpy.std(self.dane,axis=None)
       if c_sigma==numpy.inf: c_sigma=5.
       self.min_e.setText("%i"%(c0-5*c_sigma))
       self.max_e.setText("%i"%(c0+5*c_sigma))
       a=self.min_e.text()
       b=self.max_e.text()

       self.min_s= QSlider(QtCore.Qt.Vertical)
       self.min_s.setRange(int(float(a)),int(float(b)))

       self.max_s= QSlider(QtCore.Qt.Vertical)
       self.max_s.setRange(int(float(a)),int(float(b)))
       
       self.auto_p =  QPushButton('Auto')
       
       self.zoom_s= QSlider(QtCore.Qt.Horizontal)
       if len(self.dane)>len(self.dane[0]): self.zoom_s.setRange(int(-0.3*len(self.dane)),int(len(self.dane)-1))
       else: self.zoom_s.setRange(int(-0.3*len(self.dane[0])),int(len(self.dane[0])))
       self.zoom_s.setValue(1)
       
       self.header_p =  QPushButton('Header')
       self.savePic_p =  QPushButton('Save Pic')


       # Main image  ---------------------------------------------------------------
       self.fig = Figure(figsize=(5, 10.0), linewidth=-1, dpi=100,frameon=False)
       self.canvas = FigureCanvas(self.fig) 
       self.axes = self.fig.add_axes([0, 0, 1, 1]) 
       self.axes.axis("off")
       
       self.cid_move=self.canvas.mpl_connect('motion_notify_event', self.mouse_move)
       self.cid_click=self.canvas.mpl_connect('button_press_event', self.image_clicked)
       self.cid_key=self.canvas.mpl_connect('key_press_event', self.keypressed)
       #self.mpl_connect('scroll_event', self._mousescroll)
       

       
       # zoom window  ---------------------------------------------------------------
       self.fig2 = Figure(figsize=(1, 1), linewidth=-1, dpi=50,frameon=False)
       self.canvas_viewfinder = FigureCanvas(self.fig2) 
       self.axes_viewfinder = self.fig2.add_axes([0, 0, 1, 1])         
       self.axes_viewfinder.axis('off')



       # small image   ---------------------------------------------------------------
       self.fig3 = Figure(figsize=(1, 1), linewidth=-1, dpi=50,frameon=False)
       self.canvas_small = FigureCanvas(self.fig3) 
       self.axes_small = self.fig3.add_axes([0, 0, 1, 1]) 
       self.cid_click_small=self.canvas_small.mpl_connect('button_press_event', self.image_clicked)
           

       
       
       grid= QGridLayout()
       w=0
       grid.addWidget(self.max_e,w,0,1,2)
       grid.addWidget(self.canvas,w,2,6,4)
       w=w+1
       grid.addWidget(self.min_s,w,0,5,1)
       grid.addWidget(self.max_s,w,1,5,1)
       w=w+5
       grid.addWidget(self.min_e,w,0,1,2)  
       w=w+1
       grid.addWidget(self.auto_p,w,0,1,2)
       w=w+1
    
       w=6
       grid.addWidget(self.flipX_c,w,2)  
       grid.addWidget(self.flipY_c,w,3)
       grid.addWidget(self.rot90_c,w,4)       
       grid.addWidget(self.showM_c,w,5)    
       grid.addWidget(self.saturation_c,w,6)
       grid.addWidget(self.saturation_e,w,7)
       
       w=w+1
       grid.addWidget(self.mksize_l,w,2)
       grid.addWidget(self.mksize_s,w,3,1,2)
       grid.addWidget(self.savePic_p,w,5)  
       grid.addWidget(self.cmap_l,w,6)
       grid.addWidget(self.cmap_s,w,7)
       
       
    
       # prawa strona
       grid.addWidget(self.coor_l,0,6,1,2)
       grid.addWidget(self.canvas_viewfinder,1,6,1,2)
       grid.addWidget(self.canvas_small,2,6,1,2)
       grid.addWidget(self.zoom_s,3,6,1,2)


       grid.addWidget(self.header_p,4,6)   
       grid.addWidget(self.fitI_p,4,7)
       grid.addWidget(self.shopt_p,5,6,1,2)       


       self.setLayout(grid)
       grid.setRowStretch(0,0)
       grid.setRowStretch(1,1)
       grid.setRowStretch(2,1)

