#!/usr/bin/env python3

# Rozmieszczanie okien na ekranie: okna pomocnicze (Query, Plot, FFS, Header, Configuration, Help)
# obok glownego okna, zawsze w calosci na ekranie, na ktorym jest glowne okno. Wczesniej pozycje
# byly liczone z cfg_geometry (z bledem: gm[1] zamiast gm[0]) i na laptopie okna wychodzily poza ekran.

from fitsview.PyQtX.QtWidgets import QApplication
from fitsview.PyQtX.QtCore import Qt
from fitsview.PyQtX.QtGui import QKeySequence
try:
    from fitsview.PyQtX.QtGui import QShortcut          # PyQt6
except ImportError:
    from fitsview.PyQtX.QtWidgets import QShortcut      # PyQt5


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


# ---------------------------------------------------------------------------------------------------------------
# Panele: okna pomocnicze (Query, wykresy, FFS, Header, Figure, Configuration, Help). Gdy FitsView siedzi w
# FitsViewWindow (QMainWindow, samodzielne uruchomienie), panel jest dokiem (QDockWidget) - mozna go przesunac,
# ulozyc w zakladkach, odpiac (podwojne klikniecie w tytul) i zamknac; uklad zapamietuje sie sam. Bez takiego
# okna (FitsView osadzony w innym programie, np. TOI) panel jest zwyklym oknem obok glownego (place_window).
# Jeden dok na rodzaj (kind): kolejny widget tego rodzaju (np. Query z nowej klatki albo innej plaszczyzny kostki)
# podmienia widget w doku; poprzedni wraca do doku, gdy zostanie znow pokazany (show_panel).

def panel_host(anchor):
    win = anchor.window() if anchor is not None else None
    return win if hasattr(win, "fv_dock") else None


def init_panel(win, anchor, kind, title, width, height, dy=0):
    # zamiast place_window w konstruktorze okna pomocniczego; okno pokazuje show_panel
    win._fv_kind = kind
    win._fv_title = title
    win._fv_dock = None
    host = panel_host(anchor)
    if host is not None:
        host.fv_dock(win, kind, title)
    else:
        place_window(win, anchor, width, height, dy)
    # Esc w panelu zamyka go (z obrazu: Esc zamyka ostatnio pokazany panel, close_last_panel)
    win._fv_esc = QShortcut(QKeySequence("Esc"), win)
    win._fv_esc.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
    win._fv_esc.activated.connect(lambda: close_panel(win))


def docked(win):
    return getattr(win, "_fv_dock", None) is not None


_shown = []        # panele w kolejnosci pokazywania (ostatni - ostatnio pokazany), dla close_last_panel


def show_panel(win):
    if win in _shown: _shown.remove(win)
    _shown.append(win)
    dock = getattr(win, "_fv_dock", None)
    if dock is None:
        win.show()
        win.raise_()
        return
    if dock.widget() is not win:                 # w doku jest teraz inny widget tego rodzaju
        dock.window().fv_dock(win, win._fv_kind, win._fv_title)
    win.show()
    dock.show()
    dock.raise_()                                # zakladka doku na wierzch


def close_panel(win):
    dock = getattr(win, "_fv_dock", None)
    if dock is not None and dock.widget() is win:
        dock.hide()
    elif dock is None:
        win.close()


def panel_visible(win):
    dock = getattr(win, "_fv_dock", None)
    if dock is not None: return dock.isVisible() and dock.widget() is win
    return win.isVisible()


def close_last_panel():
    # Esc nad obrazem: zamyka ostatnio pokazany, wciaz widoczny panel; True, jesli jakis zamknieto
    for win in reversed(list(_shown)):
        try:
            visible = panel_visible(win)
        except RuntimeError:                     # obiekt Qt juz usuniety
            _shown.remove(win)
            continue
        if visible:
            close_panel(win)
            return True
    return False
