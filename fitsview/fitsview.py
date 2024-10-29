#!/usr/bin/env python3


import os
import sys
from PyQt5.QtWidgets import QApplication
from fitsview import FitsView_gui

def main():
    app = QApplication(sys.argv)

    cwd=os.getcwd()   # curent working directory
    pwd = __file__    # app location

    cfg=[]
    #cfg=["flip_X=True","flip_Y=True","saturation=1000.0","cmap=spectral"]
    main = FitsView_gui.FitsView(cfg)

    fits=None
    mi=0
    mx=False
    my=False
    coo=False

    for i,a in enumerate(sys.argv):
        if ".fits" in a or ".fz" in a and i >= 1:
           fits=a
        elif os.path.isfile(a) and ".py" not in a and i >= 1:
          coo=a
        else:
          if not mx:
             try: mx=float(a)
             except: mx=False
          else:
             try: my=float(a)
             except: my=False

    #main.config_file="special.cfg"           # load with predifined configuration file
    #main.conf()

    if fits:
       main.fname=fits
       main.newFits()

    if mx and my:
       main.ext_x=[mx]
       main.ext_y=[my]
       main.ext_l=["p1"]   # label tego punktu ktory chcemy zaznaczyc
       main.update()

    if coo:
        main.coo_file=coo
        if main.coo_file!=None:
            main.load_coo()


    sys.exit(app.exec_())

if __name__ == '__main__':
    main()