#!/usr/bin/env python3

# Rozmieszczanie okien na ekranie: okna pomocnicze (Query, Plot, FFS, Header, Configuration, Help)
# obok glownego okna, zawsze w calosci na ekranie, na ktorym jest glowne okno. Wczesniej pozycje
# byly liczone z cfg_geometry (z bledem: gm[1] zamiast gm[0]) i na laptopie okna wychodzily poza ekran.

from fitsview.PyQtX.QtWidgets import QApplication


def available_geometry(widget=None):
    # wolna czesc ekranu (bez paneli pulpitu), na ktorym jest widget (albo glowny ekran)
    screen = None
    if widget is not None:
        screen = QApplication.screenAt(widget.window().frameGeometry().center())
    if screen is None:
        screen = QApplication.primaryScreen()
    return screen.availableGeometry()


def fit_to_screen(win):
    # okno (np. z geometrii zapisanej na wiekszym monitorze) zmniejszone i przesuniete na ekran
    avail = available_geometry(win)
    w = min(win.width(), avail.width())
    h = min(win.height(), avail.height())
    x = min(max(win.x(), avail.left()), avail.right() - w + 1)
    y = min(max(win.y(), avail.top()), avail.bottom() - h + 1)
    win.setGeometry(x, y, w, h)


def place_window(win, anchor, width, height, dy=0):
    # win (okno pomocnicze) o rozmiarze width x height (piksele logiczne, przyciete do ekranu):
    # na prawo od glownego okna, a jesli tam sie nie miesci - na lewo; jesli i tam nie, to przy
    # prawej krawedzi ekranu (zachodzi na glowne okno). dy: przesuniecie w dol wzgledem gory
    # glownego okna, zeby kolejne okna (Query, Plot) nie lezaly jedno na drugim.
    main = anchor.window() if anchor is not None else None
    avail = available_geometry(main)
    w = min(int(width), avail.width())
    h = min(int(height), avail.height())
    if main is None or main is win:
        x, y = avail.left() + (avail.width() - w) // 2, avail.top() + (avail.height() - h) // 2
    else:
        fg = main.frameGeometry()
        if fg.right() + 1 + w <= avail.right() + 1:
            x = fg.right() + 1
        elif fg.left() - w >= avail.left():
            x = fg.left() - w
        else:
            x = avail.right() - w + 1
        y = fg.top() + int(dy)
    x = min(max(x, avail.left()), avail.right() - w + 1)
    y = min(max(y, avail.top()), avail.bottom() - h + 1)
    win.resize(w, h)
    win.move(x, y)
