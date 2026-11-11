#!/usr/bin/env python3

# Motyw FitsView = motywy TOI (fitsview/toi_theme.py - kopia toi_theme.py z TOI, zmienione tylko importy PyQtX).
# Wybor w Configuration -> Theme, zapamietany w QSettings("OCA", "FitsView") / "theme":
#   "toi" (domyslnie) - ten sam motyw co TOI (QSettings("OCA", "TOI") / "theme", czytany przy starcie),
#   albo nazwa motywu (day, paper, clearsky, night, cosmic, nord, dim, synthwave).
# FitsView nigdy nie zmienia ustawienia TOI. Po polaczeniu z TOI FitsView wezmie po prostu obiekt theme z TOI.
# Uzycie jak w TOI: theme.c("text"), theme.hex(...), theme.style_figure(fig, axes), theme.on_change(f).

from fitsview.PyQtX.QtCore import QSettings
from fitsview import toi_theme
from fitsview.toi_theme import THEMES, TITLES

FOLLOW_TOI = "toi"


def toi_name():
    name = str(QSettings("OCA", "TOI").value("theme", "day"))
    return name if name in THEMES else "day"


class FVTheme(toi_theme.Theme):
    def __init__(self):
        toi_theme.Theme.__init__(self)              # ustawia self.name z TOI
        self.choice = str(QSettings("OCA", "FitsView").value("theme", FOLLOW_TOI))
        if self.choice != FOLLOW_TOI and self.choice not in THEMES:
            self.choice = FOLLOW_TOI
        self.name = toi_name() if self.choice == FOLLOW_TOI else self.choice

    def choices(self):
        # (klucz, opis) do listy w Configuration
        out = [(FOLLOW_TOI, "Follow TOI (%s)" % TITLES[toi_name()])]
        return out + [(k, TITLES[k]) for k in TITLES]

    def choose(self, choice):
        # jak toi_theme.Theme.set, ale zapis w ustawieniach FitsView, nie TOI
        if choice != FOLLOW_TOI and choice not in THEMES: return
        self.choice = choice
        QSettings("OCA", "FitsView").setValue("theme", choice)
        self.name = toi_name() if choice == FOLLOW_TOI else choice
        self.apply_palette()
        self.repaint_all()
        for f in self._listeners:
            f()

    def set(self, name):
        self.choose(name)

    def bg(self):
        # tlo wykresow i pol wokol obrazka: w dzien biale (jak dotad), inaczej kolor okna motywu
        return self.hex("window") if self.c("window") else "#ffffff"


theme = FVTheme()
