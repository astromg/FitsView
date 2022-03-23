#!/usr/bin/env python

#----------------
# 20.04.2020 - start pracy nad programem
# 23.03.2022
# Marek Gorski
#----------------

import sys, os
from FitsView_gui import *
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)

cwd=os.getcwd()   # curent working directory
pwd = __file__    # app location

cfg=[]
#cfg=["flip_X=True","flip_Y=True","saturation=1000.0","cmap=spectral"]
main = FitsView(cfg)


fits=False
mi=0
mx=False
my=False
coo=False




for a in sys.argv:
    if ".fits" in a or ".fz" in a:
       fits=a
    elif os.path.isfile(a) and ".py" not in a:
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
   main.load_coo()


sys.exit(app.exec_())

