#!/usr/bin/env python3

import matplotlib.pyplot as plt
import matplotlib, numpy
import matplotlib.patches as patches
import numpy as np
from astropy.io import fits

from matplotlib.colors import ListedColormap
from matplotlib.collections import LineCollection
from matplotlib.figure import Figure

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from scipy.optimize import curve_fit

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel,QCheckBox, QTextEdit, QMessageBox, QLineEdit, QDialog, QTabWidget, QPushButton, QFileDialog, QGridLayout, QHBoxLayout, QVBoxLayout, QInputDialog,QComboBox, QSlider
from PyQt5 import QtCore, QtGui

from fitsview import FitsView_widgets


class ImageView(QWidget):
    # Wspolna podstawa zakladek z obrazem: Image (HDU), MapTab, MaskTab (FitsView_maps).
    # Wyswietlanie, zoom, viewfinder, miniatura, flip / rot90, min/max, markery i nakladki,
    # klawisze ogolne (m, d, f, g, l, c). Rysowana jest tylko widoczna zakladka (self.dirty),
    # zoom i srodek widoku sa wspolne dla wszystkich zakladek (parent.view).
    def __init__(self,parent,dane):
        QWidget.__init__(self)


        self.points_set = []

        self.int_x=[]
        self.int_y=[]
        self.parent=parent
        self.dane = dane
        self.dirty = True                   # do przerysowania przy pokazaniu zakladki
        self.points_dirty = False           # tylko nakladki (punkty, linie, maski) do przerysowania

        self.text_window=False
        self.r_window=False
        self.c_window=False
        self.e_window=False
        self.s_window=False

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
        self.x,self.y = self.to_screen(int(len(self.dane[0])/2), int(len(self.dane)/2))
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


    def update_mask(self):
        # maski z parent.mask_data (zakladki MaskTab); kontur albo polprzezroczyste wypelnienie
        x1,x2 = self.axes.get_xlim()           # contour/imshow potrafia zmienic zakres osi
        y1,y2 = self.axes.get_ylim()
        for zestaw in self.parent.mask_data:
            if not zestaw["plot_image"] or zestaw.get("hidden"): continue
            mk = zestaw["data"]
            if mk.shape != self.dane.shape: continue
            if self.parent.cfg_rot90: mk = numpy.rot90(mk)   # maska w ukladzie oryginalu, jak dane
            if zestaw["style"] == "fill":
                self.axes.imshow(numpy.ma.masked_where(~mk, mk), cmap=ListedColormap([zestaw["color"]]),
                                 vmin=0, vmax=1, alpha=0.5, interpolation="none")
            else:
                # kontur tylko w prostokacie z pikselami True (+1 px), na pelnej klatce 4k to ~0.6 s na maske
                rows = numpy.flatnonzero(mk.any(axis=1))
                cols = numpy.flatnonzero(mk.any(axis=0))
                if rows.size == 0: continue
                r0, r1 = max(rows[0]-1, 0), min(rows[-1]+2, mk.shape[0])
                c0, c1 = max(cols[0]-1, 0), min(cols[-1]+2, mk.shape[1])
                if r1-r0 < 2 or c1-c0 < 2: continue
                self.axes.contour(mk[r0:r1,c0:c1].astype(float),levels=[0.5],colors=zestaw["color"],linewidths=1.5,
                                  extent=(c0,c1-1,r0,r1-1))
        self.axes.set_xlim(x1,x2)
        self.axes.set_ylim(y1,y2)
        self.canvas.draw_idle()

    def update_segments(self,zestaw):
        # tabela z odcinkami (kolumny x0, y0, x1, y1, np. ffs.lines); spike == True rysowane przerywana linia
        dane = zestaw["data"]
        x0,y0 = self.to_screen(numpy.array(dane["x0"]),numpy.array(dane["y0"]))
        x1,y1 = self.to_screen(numpy.array(dane["x1"]),numpy.array(dane["y1"]))
        segments = [[(a,b),(c,d)] for a,b,c,d in zip(x0,y0,x1,y1)]
        if "spike" in dane.colnames: style = ["--" if s else "-" for s in dane["spike"]]
        else: style = "-"
        color = zestaw["marker_color"] if "marker_color" in zestaw.keys() else "r"
        self.axes.add_collection(LineCollection(segments,colors=color,linestyles=style,linewidths=1.5),autolim=False)
        n = zestaw["selected_index"]
        if 0 <= n < len(segments):
            self.axes.add_collection(LineCollection([segments[n]],colors="r",linewidths=4,alpha=0.5),autolim=False)


    def update_points(self):
        if self.dirty: return                      # i tak przerysuje sie cala przy pokazaniu zakladki
        if not self.isVisible():
            self.points_dirty = True
            return
        self.points_dirty = False
        #DUPA
        # for obj in self.points_set:
        #     obj.remove()
        # self.points_set = []

        for line in list(self.axes.lines):
            try:
                line.remove()
            except Exception:
                pass

        for coll in list(self.axes.collections):
            try:
                coll.remove()
            except Exception:
                pass

        for im in list(self.axes.images):     # wypelnienia masek; obraz zostaje
            if im is not self.image: im.remove()

        for zestaw in self.parent.table_data:
            if zestaw.get("hidden"): continue           # zakladka schowana (Hide)

            if zestaw["plot_image"] and all(k in getattr(zestaw["data"],"colnames",[]) for k in ["x0","y0","x1","y1"]):
                self.update_segments(zestaw)

            elif zestaw["plot_image"]:

                if "xcol" in zestaw.keys() and "ycol" in zestaw.keys():
                    xc = zestaw["xcol"]
                    yc = zestaw["ycol"]

                    x = zestaw["data"][xc]
                    y = zestaw["data"][yc]

                    xs, ys = self.to_screen(x, y)

                    marker = "."
                    mksize = 10
                    mkcolor = "b"
                    valuecol = "None"

                    if "marker" in zestaw.keys():
                        marker = zestaw["marker"]

                    if "mksize" in zestaw.keys():
                        mksize = zestaw["mksize"]

                    if "marker_color" in zestaw.keys():
                        mkcolor = zestaw["marker_color"]

                    if "valuecol" in zestaw.keys():
                        valuecol = zestaw["valuecol"]

                    if valuecol == "None":
                        if marker == "open circle":
                            set = self.axes.plot(xs,ys,marker="o",markersize=mksize,color=mkcolor,mfc='none',linestyle='None')
                        else:
                            set = self.axes.plot(xs,ys,marker=marker,markersize=mksize,color=mkcolor,linestyle='None')
                        self.points_set.append(set[0])

                    else:
                        val = zestaw["data"][valuecol]
                        size_scatter = mksize ** 2  # scatter używa pola powierzchni

                        if marker == "open circle":

                            mask = ~numpy.isnan(val)
                            norm_val = numpy.zeros_like(val)
                            norm_val[mask] = (val[mask] - numpy.min(val[mask])) / (numpy.max(val[mask]) - numpy.min(val[mask]))

                            edge_colors = numpy.zeros((len(val), 4))
                            edge_colors[mask] = plt.cm.viridis(norm_val[mask])

                            sc = self.axes.scatter(xs, ys, s=size_scatter, marker='o',edgecolors=edge_colors, facecolors='none')
                        else:
                            sc = self.axes.scatter(xs, ys, s=size_scatter, c=val, marker=marker, cmap='viridis')
                        self.points_set.append(sc)


                    if zestaw["selected_index"] >= 0:
                        n = zestaw["selected_index"]
                        selection = self.axes.plot(xs[n],ys[n],marker="o",markersize=mksize+5,color="r",mfc='none',linestyle='None')
                        self.points_set.append(selection[0])

        self.update_mask()

    def sync_options(self):
        # checkboxy z konfiguracji (wspolnej dla zakladek); bez sygnalow, zeby np. zmiana_rot90
        # nie przeliczyla drugi raz srodka widoku
        for c, v in [(self.saturation_c, self.parent.cfg_showsat), (self.flipX_c, self.parent.cfg_flipX),
                     (self.flipY_c, self.parent.cfg_flipY), (self.rot90_c, self.parent.cfg_rot90)]:
            c.blockSignals(True)
            c.setChecked(bool(v))
            c.blockSignals(False)

    def showEvent(self,event):
        # przy pokazaniu zakladki: wspolny widok (zoom, srodek) i przerysowanie, jesli cos sie zmienilo
        QWidget.showEvent(self,event)
        self.sync_options()
        if self.parent.view is not None:
            self.x, self.y, zoom = self.parent.view
            self.zoom_s.blockSignals(True)
            self.zoom_s.setValue(zoom)
            self.zoom_s.blockSignals(False)
        if self.dirty: self.update()
        else:
            self.zmiana_zoom()
            if self.points_dirty: self.update_points()

    def update(self):
        # niewidoczna zakladka (nieaktywna) tylko zapamietuje, ze ma sie przerysowac (showEvent)
        if not self.isVisible():
            self.dirty = True
            return

        #try: self.axes.lines[-1].remove()
        #except: pass

        self.sync_options()

        if self.parent.cfg_rot90:
          dane=numpy.rot90(self.dane)
        else: dane=self.dane

        vmin=self.min_s.value()
        vmax=self.max_s.value()

        self.axes.clear()
        self.axes.set_xticks([])
        self.axes.set_yticks([])

        mymap = self.get_cmap()

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

        # to jest stary mechanizm, nie wiem czy zostawic
        self.ext_x=self.parent.ext_x
        self.ext_y=self.parent.ext_y


        if self.showM_c.checkState():
          mksize=int(self.mksize_s.value()/10.)+1
          if len(self.ext_x)>0:
             try:
                if self.parent.cfg_rot90:
                   self.axes.plot(*self.to_screen(self.ext_x,self.ext_y),str(self.parent.cfg_extMarker).strip(),markersize=mksize,mfc='none')
                else: self.axes.plot(self.ext_x,self.ext_y,str(self.parent.cfg_extMarker).strip(),markersize=mksize,mfc='none')
             except ValueError:
                self.msg = QMessageBox()
                self.msg.setText("'"+self.parent.cfg_extMarker.strip()+"'"+ " is not a proper marker style\nCheck configuration!")
                self.msg.exec_()


          mksize=mksize+2
          if len(self.int_x)>0:
             try:
                if self.parent.cfg_rot90:
                   self.axes.plot(*self.to_screen(self.int_x,self.int_y),str(self.parent.cfg_intMarker).strip(),markersize=mksize,alpha=0.5,mfc='none')
                else: self.axes.plot(self.int_x,self.int_y,str(self.parent.cfg_intMarker).strip(),markersize=mksize,alpha=0.5,mfc='none')
             except ValueError:
                self.msg = QMessageBox()
                self.msg.setText("'"+self.parent.cfg_intMarker.strip()+"'"+ " is not a proper marker style\nCheck configuration!")
                self.msg.exec_()

        mymap = self.get_cmap()

        # miniatura ma ~200 px: co k-ty piksel wystarczy (rysowanie calej klatki 4k to ~1 s)
        k = max(1, max(dane.shape) // 1000)
        ny, nx = dane.shape
        self.axes_small.clear()
        self.image_small = self.axes_small.imshow(dane[::k,::k],cmap=mymap,vmin=vmin, vmax=vmax,interpolation="None",aspect="equal",origin='lower',
                                                  extent=(-0.5, ((nx+k-1)//k)*k-0.5, -0.5, ((ny+k-1)//k)*k-0.5))
        self.axes_small.set_xticks([])
        self.axes_small.set_yticks([])

        self.zmiana_zoom()                       # rysuje oba plotna (canvas, canvas_small)
        self.reset_viewfinder()

        self.dirty = False
        self.update_points()

    def reset_viewfinder(self):

        if self.parent.cfg_rot90:
          dane=numpy.rot90(self.dane)
        else: dane=self.dane

        vmin=self.min_s.value()
        vmax=self.max_s.value()

        mymap = self.get_cmap()
        dane2=dane.copy()


        #if self.parent.cfg_showsat:
        #   sat = float(self.parent.cfg_saturation)
        #   dane2[dane>=sat]="nan"
        #   mymap.set_bad("red")

        self.axes_viewfinder.clear()
        self.image_viewfinder = self.axes_viewfinder.imshow(dane2,cmap=mymap,vmin=vmin, vmax=vmax,interpolation="None",aspect="equal")
        self.axes_viewfinder.set_xticks([])
        self.axes_viewfinder.set_yticks([])
        # okno wokol srodka widoku (jak update_viewfinder); bez tego rysowana byla cala klatka (~1.4 s dla 4k)
        wsize=2*int(self.parent.cfg_apersize)+15
        self.axes_viewfinder.set_xlim(self.x-wsize,self.x+wsize)
        self.axes_viewfinder.set_ylim(self.y-wsize,self.y+wsize)
        self.canvas_viewfinder.draw_idle()


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
        self.x,self.y = self.to_screen(int(len(self.dane[0])/2), int(len(self.dane)/2))
        self.zmiana_zoom()

    def zmiana_zoom(self):
       if not self.isVisible(): return          # widok ustawi showEvent (parent.view)

       z=len(self.dane[0]) - self.zoom_s.value() + 1
       z=max(int(z/2.),1)                       # przy maksymalnym zoomie bylo 0 -> zerowy zakres osi
       x0=self.x
       y0=self.y
       self.parent.view = (self.x, self.y, self.zoom_s.value())    # wspolny dla wszystkich zakladek

       if self.parent.cfg_flipX: self.axes.set_xlim(x0+z,x0-z)
       else: self.axes.set_xlim(x0-z,x0+z)
       if self.parent.cfg_flipY: self.axes.set_ylim(y0+z,y0-z)
       else: self.axes.set_ylim(y0-z,y0+z)
       self.canvas.draw_idle()                  # draw_idle: kilka prosb o rysowanie -> jedno rysowanie

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

       ny,nx = self.dane.shape
       if self.parent.cfg_rot90: nx,ny = ny,nx
       if self.parent.cfg_flipX: self.axes_small.set_xlim(nx,0)
       else: self.axes_small.set_xlim(0,nx)
       if self.parent.cfg_flipY: self.axes_small.set_ylim(ny,0)
       else: self.axes_small.set_ylim(0,ny)

       self.canvas_small.draw_idle()

    def view_limits(self):
        # widoczny fragment (x1, x2, y1, y2) w ukladzie ekranu, rosnaco - jak ustawia go zmiana_zoom
        x, y, zoom = self.parent.view if self.parent.view is not None else (self.x, self.y, self.zoom_s.value())
        z = max(int((len(self.dane[0]) - zoom + 1)/2.), 1)
        return x-z, x+z, y-z, y+z

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

       counts=self.pixel_value(x,y)
       xr,yr=self.to_orig(x,y)

       txt = "%.2f %.2f %d"% (xr,yr,counts)
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
       # tylko klikniecie w obrazek lub miniature; poza nimi (margines, skala kolorow MapTab) xdata to None
       if event.inaxes not in (self.axes, self.axes_small) or event.xdata is None: return
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
          self.y=len(self.dane[0])-1-x
       else:
          self.parent.cfg_rot90=False
          x,y=self.x,self.y
          self.x=len(self.dane[0])-1-y
          self.y=x

       self.parent.view = (self.x, self.y, self.zoom_s.value())
       self.parent.update_tabs()                # rot90 wspolne: pozostale zakladki przerysuja sie przy pokazaniu

    def get_cmap(self):
        # cmap z konfiguracji (wspolna dla obrazow); MapTab ma wlasna
        return matplotlib.colormaps[self.parent.cfg_cmap.strip()]   # kopia, mozna ja modyfikowac

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


    # rot90: na ekranie jest numpy.rot90(self.dane), czyli piksel oryginalu (x, y) lezy w X = y, Y = nx - 1 - x
    def to_screen(self, x, y):
        if self.parent.cfg_rot90:
            return y, len(self.dane[0]) - 1 - numpy.asarray(x)
        return x, y

    def to_orig(self, X, Y):
        if self.parent.cfg_rot90:
            return len(self.dane[0]) - 1 - Y, X
        return X, Y

    def pixel_value(self, X, Y):
        # wartosc piksela pod punktem ekranu (X, Y)
        if self.parent.cfg_rot90:
            return self.dane[int(X)][len(self.dane[0]) - 1 - int(Y)]
        return self.dane[int(Y)][int(X)]

    def get_local_stamp(self,xr,yr,r):
       # clamp to array bounds instead of letting negative/overflowing slice
       # indices wrap around to the opposite edge of the array, which was
       # silently pulling in wrong pixels for anything measured near the
       # frame border (background, counts, zero-point, radial profile)
       ny,nx = self.dane.shape
       xlo,xhi = max(0,int(xr)-r), min(nx,int(xr)+r)
       ylo,yhi = max(0,int(yr)-r), min(ny,int(yr)+r)
       dane = self.dane[ylo:yhi,xlo:xhi]
       x0 = xr-xlo
       y0 = yr-ylo
       return dane,x0,y0


    def keypressed(self,event):
        if not self.text_window:
          self.text_window=FitsView_widgets.TextWindow(self)
          self.parent.active_windows.append(self.text_window)

        x=event.xdata
        y=event.ydata
        xr,yr=self.to_orig(x,y)

        if self.parent.special:
          self.parent.com.xPressed.emit(event.key,xr,yr)


        if "m" in event.key:
            self.int_x.append(xr)
            self.int_y.append(yr)
            self.update()
            counts=self.pixel_value(x,y)
            txt=str(xr)+" "+str(yr)+" "+str(counts)+" m"
            txt2 = "marked x=%.2f y=%.2f counts=%d"%(xr,yr,counts)
            self.text_window.txt=txt2
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
            # diffx = numpy.array(self.ext_x)-float(xr)
            # diffy = numpy.array(self.ext_y)-float(yr)
            # diff=diffx**2+diffy**2
            # n=numpy.argmin(diff)
            # x=self.ext_x[n]
            # y=self.ext_y[n]
            # self.int_x.append(x)
            # self.int_y.append(y)
            # self.update()
            # txt = self.parent.ext_l[n]
            # self.text_window.txt=txt
            # self.text_window.update()
            # print(txt)

            # DUPA
            for zestaw in self.parent.table_data:
                if zestaw["plot_image"] and not zestaw.get("hidden"):
                    if "xcol" in zestaw.keys() and "ycol" in zestaw.keys():
                        xc = zestaw["xcol"]
                        yc = zestaw["ycol"]

                        cx = zestaw["data"][xc]
                        cy = zestaw["data"][yc]

                        diffx = numpy.array(cx) - float(xr)
                        diffy = numpy.array(cy) - float(yr)
                        diff = diffx ** 2 + diffy ** 2
                        n = numpy.argmin(diff)

                        if zestaw["selected_index"] == n:
                            zestaw["selected_index"] = -1
                        else:
                            zestaw["selected_index"] = n
                            txt = f'{zestaw["name"]}:\n {zestaw["data"][n]}\n'
                            self.text_window.txt=txt
                            self.text_window.update()
                            print(txt)

                        self.update_points()

            for tab in self.parent.tab:
                if hasattr(tab, "update_selection"):
                    tab.update_selection()



        if "g" in event.key:
          xy, ok = QInputDialog.getText(self, 'Go To', 'Enter X Y:')
          if ok:
             try:
                if "," in xy: gx,gy = float(str(xy).split(",")[0]),float(str(xy).split(",")[1])
                else: gx,gy = float(str(xy).split()[0]),float(str(xy).split()[1])
             except (ValueError,IndexError): ok=False

          if ok:
             self.x, self.y = self.to_screen(gx, gy)
             x, y = self.x, self.y          # viewfinder na koncu keypressed bierze wspolrzedne ekranu
             self.zmiana_zoom()
             self.int_x.append(gx)
             self.int_y.append(gy)
             self.update()
             txt2=str(gx)+" "+str(gy)+" g"
             txt="Marked x=%.1f y=%.1f"%(gx,gy)
             self.text_window.txt=txt
             self.text_window.update()
             print(txt2)


        if "l" in event.key:
          if not self.c_window:
             self.c_window=FitsView_widgets.PlotWindow(self)
             self.parent.active_windows.append(self.c_window)
          self.c_window.show()
          self.c_window.raise_()
          #try: self.axes.lines[-1].remove()
          #except: pass

          if self.parent.cfg_rot90:
              x1, x2 = [self.to_orig(0, Y)[0] for Y in self.axes.get_ylim()]
          else:
              x1, x2 = self.axes.get_xlim()

          x1,x2 = min([x1,x2]),max([x1,x2])

          if x1<0: x1=0
          if x2>len(self.dane[int(yr),:])-1: x2=len(self.dane[int(yr),:])-1

          yyy=self.dane[int(yr),int(x1):int(x2)]
          xxx=numpy.arange(x1,x1+len(yyy),1)

          self.c_window.axes.clear()
          self.c_window.axes.plot(xxx,yyy)
          self.c_window.canvas.draw()

          if self.parent.cfg_rot90: self.vline=x
          else: self.hline=y
          self.update()

          txt="line y=%.2f   "%(yr)
          self.text_window.txt=txt
          self.text_window.update()
          self.c_window.txt=txt
          self.c_window.update()
          self.c_window.raise_()
          print(txt)



        if "c" in event.key:
          if not self.c_window:
             self.c_window=FitsView_widgets.PlotWindow(self)
             self.parent.active_windows.append(self.c_window)
          self.c_window.show()
          self.c_window.raise_()
          #try: self.axes.lines[-1].remove()
          #except: pass

          if self.parent.cfg_rot90:
              y1, y2 = self.axes.get_xlim()
          else:
              y1, y2 = self.axes.get_ylim()

          y1,y2 = min([y1,y2]),max([y1,y2])

          # nie wiem czy to jest potrzebne
          if y1<0: y1=0
          if y2>len(self.dane[:,int(xr)])-1: y2=len(self.dane[:,int(xr)])-1

          yyy=self.dane[int(y1):int(y2),int(xr)]
          xxx=numpy.arange(y1,y1+len(yyy),1)

          self.c_window.axes.clear()
          self.c_window.axes.plot(xxx,yyy)
          self.c_window.canvas.draw()

          if self.parent.cfg_rot90: self.hline=y
          else: self.vline=x
          self.update()

          txt="column x=%.2f "%(xr)
          self.text_window.txt=txt
          self.text_window.update()
          self.c_window.txt=txt
          self.c_window.update()
          self.c_window.raise_()
          print(txt)

        self.key_action(event.key,x,y,xr,yr)

        self.update_viewfinder(x,y)

    def key_action(self,key,x,y,xr,yr):
        # klawisze specyficzne dla podklasy (Image: fotometria i FFS)
        pass

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

       c0 = numpy.nanmedian(self.dane,axis=None)           # nan: mapy (MapTab) moga miec NaN
       c_sigma=numpy.nanstd(self.dane,axis=None)
       if c_sigma==numpy.inf: c_sigma=5.
       if not numpy.isfinite(c0 - c_sigma): c0, c_sigma = 0., 1.
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

       self.savePic_p =  QPushButton('Save Pic')


       # Main image  ---------------------------------------------------------------
       #self.fig = Figure(figsize=(5, 10.0), linewidth=-1, dpi=100,frameon=False)
       self.fig = Figure(linewidth=-1, dpi=100,frameon=False)
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


       grid.addWidget(self.fitI_p,4,7)            # (4,6) Header i (5,6) FFS w Image.mkUI
       grid.addWidget(self.shopt_p,5,7)


       # nad obrazkiem miejsce na ustawienia podklas (MapTab, MaskTab), jak w Catalog
       self.top_l = QVBoxLayout()
       grid.setContentsMargins(0,0,0,0)
       vbox = QVBoxLayout()
       vbox.addLayout(self.top_l)
       vbox.addLayout(grid, 1)
       self.setLayout(vbox)
       self.grid = grid
       grid.setRowStretch(0,0)
       grid.setRowStretch(1,1)
       grid.setRowStretch(2,1)

       grid.setColumnStretch(0, 0)
       grid.setColumnStretch(1, 0)
       grid.setColumnStretch(2, 1)
       grid.setColumnStretch(3, 0)
       grid.setColumnStretch(4, 0)
       grid.setColumnStretch(5, 0)
       grid.setColumnStretch(6, 0)


class Image(ImageView):
    # obraz z HDU: naglowek, FFS i fotometria (klawisze s, b, q, z, e, r)
    def __init__(self,parent,hdu,plane=None):
        self.plane=plane                    # numer plaszczyzny dla danych 3D, None dla zwyklego obrazka
        if plane is None: dane=hdu.data
        else: dane=hdu.data[plane]
        self.hdr=hdu.header
        ImageView.__init__(self,parent,numpy.nan_to_num(dane, nan=0))

        self.header_p.clicked.connect(self.show_header)
        self.ffs_p.clicked.connect(self.open_ffs)

    def mkUI(self):
       ImageView.mkUI(self)
       self.header_p =  QPushButton('Header')
       self.ffs_p =  QPushButton('FFS')
       grid = self.grid
       grid.addWidget(self.header_p,4,6)
       grid.addWidget(self.ffs_p,5,6)

    def show_header(self):
       self.hdrl_window=FitsView_widgets.HeaderTabLocal(self,self.hdr)
       self.parent.active_windows.append(self.hdrl_window)

    def open_ffs(self):
        # okno FFS (klawisz 's' lub przycisk FFS): przy pierwszym uruchomieniu wycinek z widoku,
        # potem tylko pokazanie okna; nowy wycinek bierze Reset w oknie FFS (ffs_cut)
        if not self.s_window:
            image, x1, y1 = self.ffs_cut()
            self.s_window = FitsView_widgets.FFSWindow(self, image, dx=x1, dy=y1)
            self.parent.active_windows.append(self.s_window)

        self.s_window.show()
        self.s_window.raise_()

    def ffs_cut(self):
        # widoczny fragment obrazu (ze wspolnego widoku, tez gdy ta zakladka jest ukryta)
        # -> (wycinek self.dane, x1, y1 jego poczatku w klatce)
        ny, nx = self.dane.shape
        x1, x2, y1, y2 = self.view_limits()
        if self.parent.cfg_rot90:                 # ekran (X,Y) -> oryginal x = nx - 1 - Y, y = X
            x1, x2, y1, y2 = nx - 1 - y2, nx - 1 - y1, x1, x2
        x1, x2 = int(max(x1, 0)), int(min(x2, nx))
        y1, y2 = int(max(y1, 0)), int(min(y2, ny))
        return self.dane[y1:y2, x1:x2], x1, y1

    def key_action(self,key,x,y,xr,yr):
        if "s" in key:
            self.int_x.append(xr)
            self.int_y.append(yr)
            self.update()


            self.open_ffs()


          # q34 = (numpy.quantile(dane, 0.83725) - numpy.quantile(dane, 0.16275))/2.
          #
          # txt = "selected x=(%.2f,%.2f)  y=(%.2f,%.2f)\n"%(x1,x2,y1,y2)
          # txt = txt+"min: %.2f\n"%(dane.min())
          # txt = txt+"max: %.2f\n"%(dane.max())
          # txt = txt+"mean: %.2f\n"%(numpy.mean(dane))
          # txt = txt+"median: %.2f\n"%(numpy.median(dane))
          # txt = txt+"spread: %.2f\n"%(numpy.std(dane))
          # txt = txt + "sigma_q34: %.2f\n" % (q34)
          #
          # self.text_window.txt=txt
          # self.text_window.update()
          # print(txt)



        if "b" in key:
          r=int(self.parent.cfg_apersize)
          dane,x0,y0 = self.get_local_stamp(xr,yr,r)
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


        if "q" in key:
          r=int(self.parent.cfg_apersize)
          dane,x0,y0 = self.get_local_stamp(xr,yr,r)
          XX,YY = numpy.meshgrid(numpy.arange(dane.shape[1]),numpy.arange(dane.shape[0]))
          tmp = numpy.vstack((dane.ravel(),XX.ravel(),YY.ravel()))
          c,xx,yy=tmp[0],tmp[1],tmp[2]
          d=((xx-x0)**2+(yy-y0)**2)**0.5
          mk=d<r
          aper = c[mk]
          zliczenia = aper.sum() - len(aper) * float(self.parent.cfg_bcg)

          if zliczenia>0:
             mag = -2.5*numpy.log10(zliczenia) + float(self.parent.cfg_zp)
             txt2="%.1f %.1f %d %.2f q "%(xr,yr,zliczenia,mag)
             txt="centered x=%.1f y=%.1f : counts=%d m=%.2f  "%(xr,yr,zliczenia,mag)
          else:
             txt2="%.1f %.1f %d nan q "%(xr,yr,zliczenia)
             txt="centered x=%.1f y=%.1f : counts=%d  (non-positive net counts, magnitude undefined)"%(xr,yr,zliczenia)

          self.int_x.append(xr)
          self.int_y.append(yr)
          self.update()
          self.text_window.txt=txt
          self.text_window.update()
          print(txt2)

        if "z" in key:
          r=int(self.parent.cfg_apersize)
          dane,x1,y1 = self.get_local_stamp(xr,yr,r)
          XX,YY = numpy.meshgrid(numpy.arange(dane.shape[1]),numpy.arange(dane.shape[0]))
          tmp = numpy.vstack((dane.ravel(),XX.ravel(),YY.ravel()))
          c,xx,yy=tmp[0],tmp[1],tmp[2]

          x0=numpy.sum(c*xx)/( numpy.sum(c) )
          y0=numpy.sum(c*yy)/( numpy.sum(c) )
          xr=xr+(x0-x1)
          yr=yr+(y0-y1)

          dane,_,_ = self.get_local_stamp(xr,yr,r)
          XX,YY = numpy.meshgrid(numpy.arange(dane.shape[1]),numpy.arange(dane.shape[0]))
          tmp = numpy.vstack((dane.ravel(),XX.ravel(),YY.ravel()))
          c,xx,yy=tmp[0],tmp[1],tmp[2]
          d=((xx-x0)**2+(yy-y0)**2)**0.5
          mk=d<r
          aper = c[mk]
          zliczenia = aper.sum() - len(aper) * float(self.parent.cfg_bcg)

          if zliczenia<=0:
             txt="cannot set zero point: non-positive net counts (%d) in aperture - check background level"%(zliczenia)
             self.text_window.txt=txt
             self.text_window.update()
             print(txt)
          else:
             mag = -2.5*numpy.log10(zliczenia) + float(self.parent.cfg_zp)

             m_std, ok = QInputDialog.getText(self, 'Zero point', 'Enter star magnitude:')
             if ok:
                try: m_std=float(m_std)
                except ValueError: ok=False

             if ok:
                d=m_std-mag
                self.parent.cfg_zp=str(float(self.parent.cfg_zp)+d)
                txt2="%.3f z"%(float(self.parent.cfg_zp))
                txt="zero point set to %.3f"%(float(self.parent.cfg_zp))

                self.int_x.append(xr)
                self.int_y.append(yr)
                self.update()
                self.text_window.txt=txt
                self.text_window.update()
                print(txt2)

        if "e" in key:

          if not self.e_window:
             self.e_window=FitsView_widgets.PlotWindow(self)
             self.parent.active_windows.append(self.e_window)

          self.e_window.show()
          self.e_window.raise_()


          r=int((2*int(self.parent.cfg_apersize)+15)/2.)

          dane,x1,y1 = self.get_local_stamp(xr,yr,r)

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

        if "r" in key:

          if not self.r_window:
             self.r_window=FitsView_widgets.PlotWindow(self)
             self.parent.active_windows.append(self.r_window)

          self.r_window.show()
          self.r_window.raise_()

          r=int(self.parent.cfg_apersize)

          dane,x1,y1 = self.get_local_stamp(xr,yr,r)

          xy = numpy.unravel_index(dane.argmax(), dane.shape)
          dx=x1-xy[1]
          dy=y1-xy[0]
          xr=int(xr)-dx
          yr=int(yr)-dy

          dane,x1,y1 = self.get_local_stamp(xr,yr,r)

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
          amplitude = popt[0]
          sky = popt[2]
          sigma=(popt[1]**2)**0.5
          fwhm=2.355*sigma

          self.r_window.axes.clear()
          self.r_window.axes.plot(d,c,".g")

          self.r_window.axes.plot(xx,yy)
          self.r_window.canvas.draw()
          txt2="%.2f %.2f  %.2f r  "%(xr,yr,fwhm)
          txt="centered x=%.2f y=%.2f amp=%.1f sky=%.1f FWHM=%.2f   "%(xr,yr,amplitude, sky,fwhm)
          self.int_x.append(xr)
          self.int_y.append(yr)
          self.update()
          self.text_window.txt=txt
          self.text_window.update()

          self.r_window.txt=txt
          self.r_window.update()
          self.r_window.raise_()


          print(txt2)

    def gaus(self,x,a,sigma,c0):
       x0=0
       return a*numpy.exp(-(x-x0)**2/(2*sigma**2))+c0

