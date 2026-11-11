#!/usr/bin/env python3


import os
import sys
from fitsview.PyQtX.QtWidgets import QApplication
from fitsview.PyQtX.QtCore import Qt
from fitsview import FitsView_gui

def setup_qt():
    # przed utworzeniem QApplication; przy osadzeniu FitsView w innym programie (np. TOI) decyduje ten program.
    # Wayland: Qt6 na GNOME dziala natywnie na Waylandzie, a tam program nie moze ustawiac pozycji swoich okien
    # (place_window bylby ignorowany) - jak w TOI (toi.py) wymuszamy xcb (XWayland), chyba ze ktos ustawil inaczej.
    if sys.platform.startswith("linux") and os.environ.get("XDG_SESSION_TYPE") == "wayland":
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    # HiDPI: Qt6 skaluje sam. Qt5 (PyQtX bez PyQt6) na laptopie 2880x1800 (Xft.dpi=192) mial skale 1.0 - czcionki
    # podwojne, a rozmiary okien i pol w pikselach polowe za male; w Qt6 tych atrybutow juz nie ma.
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    if hasattr(QApplication, "setHighDpiScaleFactorRoundingPolicy"):      # skale ulamkowe (1.25, 1.5)
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

def main():
    setup_qt()
    app = QApplication(sys.argv)
    from fitsview.fv_theme import theme
    theme.apply_palette()             # motyw (Configuration -> Theme; domyslnie jak w TOI)

    cwd=os.getcwd()   # curent working directory
    pwd = __file__    # app location

    cfg=[]
    #cfg=["flip_X=True","flip_Y=True","saturation=1000.0","cmap=spectral"]
    if FitsView_gui.docking_enabled():             # Configuration -> "Dock panels" (od nastepnego uruchomienia)
        window = FitsView_gui.FitsViewWindow(cfg)  # FitsView w oknie z dokami (panele); main - sam FitsView
        main = window.fv
    else:
        main = FitsView_gui.FitsView(cfg)          # domyslnie: panele jako osobne okna obok glownego

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


    sys.exit(app.exec())

if __name__ == '__main__':
    main()