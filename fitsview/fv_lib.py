
from astropy.table import Table
import numpy as np

def daophot_files_parser(file_name):
    if file_name.endswith(".ap"):

        with open(file_name) as f:
            lines = [l.rstrip() for l in f if l.strip()]

        dane = []
        bledy = []

        data_lines = lines[2:]  # wywalam naglowek

        for d, e in zip(data_lines[::2], data_lines[1::2]):
            dane.append(d.split())
            bledy.append(e.split())

        dane = list(zip(*dane))
        bledy = list(zip(*bledy))

        cols = {
            "id": np.array(dane[0], dtype=int),
            "x": np.array(dane[1], dtype=float) - 1.0,
            "y": np.array(dane[2], dtype=float) - 1.0,
            "sky": np.array(bledy[0], dtype=float),
            "sigma": np.array(bledy[1], dtype=float),
            "errtot": np.array(bledy[2], dtype=float)
        }

        n_ap = len(dane) - 3
        for i in range(n_ap):
            cols[f"mag{i}"] = np.array(dane[3 + i], dtype=float)
            cols[f"err{i}"] = np.array(bledy[3 + i], dtype=float)

    elif file_name.endswith(".coo"):
        with open(file_name) as f:
            lines = [l.rstrip() for l in f if l.strip()]
            dane = []
            data_lines = lines[2:]  # wywalam naglowek
            for l in data_lines:
                dane.append(l.split())
            dane = list(zip(*dane))
            cols = {
                "id": np.array(dane[0], dtype=int),
                "x": np.array(dane[1], dtype=float) - 1.0,
                "y": np.array(dane[2], dtype=float) - 1.0,
                "mag_fi": np.array(dane[3], dtype=float),
                "sharp": np.array(dane[4], dtype=float),
                "round": np.array(dane[5], dtype=float),
                "param": np.array(dane[6], dtype=float),
            }

    elif file_name.endswith(".lst"):
        with open(file_name) as f:
            lines = [l.rstrip() for l in f if l.strip()]
            dane = []
            data_lines = lines[2:]  # wywalam naglowek
            for l in data_lines:
                dane.append(l.split())
            dane = list(zip(*dane))
            cols = {
                "id": np.array(dane[0], dtype=int),
                "x": np.array(dane[1], dtype=float) - 1.0,
                "y": np.array(dane[2], dtype=float) - 1.0,
                "mag": np.array(dane[3], dtype=float),
                "err": np.array(dane[4], dtype=float),
                "param": np.array(dane[5], dtype=float),
            }

    tab = Table(cols)
    return tab



