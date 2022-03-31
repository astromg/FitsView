# FitsView
Python Fits Viewer

**FitsView 1.0** 

_31.03.2022_
_Marek Gorski_  

./FitsView.py plik.fits  
**or**  
./FitsView.py plik.fits 400 500 _# mark point_  
./FitsView.py plik.fits plik.out _# mark all point from plik.out_  

#### Basic functions and layout of the program.

Fits file is displayed as the <font color="blue">image</font>. On the right side the upper window shows <font color="blue">vievfinder</font> window with <font color="blue">aperture</font> marked as the green circle. Below is the <font color="blue">thumbnail</font> of the main image. You can <font color="blue">zoom</font> with the slider below this window. You can navigate by left-clicking on the main image, or by left-clicking on the thumbnail.  
The <font color="green">Show optiones</font> allows to to adjast contrast level with sliders on the left. The slider limits can be manualy edited and changed. You can <font color="green">flip</font> the image in X and Y axis, and <font color="green">rotate</font> the image by 90 deg. Those operations **do not change** the working coordinates of the image.  
Other options are rather obvious.



#### Keybord functions

_When the main window is active and pointer is hovering over the image, pressing specific **key** will activate the function. Result will be displayed in a **Querry Window**, or other specific window. Numeric result will be printed in short version to a **terminal**._

*   **m** : mark point on the image
*   **d** : delete marker on the image
*   **g** : goto - put x and y coordinates in a popup dialog window. Marker will be set on this coordinates and image will be centered on this point
*   **f** : find - if coordinate file was loaded, the line from this file with the closest coordinates is printed.
*   **b** : background - measure background in counts/pixel. Measuremetn is averaged from the viefinder aperture. Use before **q** and **z** functions
*   **z** : zero-point - set up a zero point for magnitude calculations. Press over the star with known magnitude, and put this magnitude in a popup dialog window.
*   **q** : querry - get total counts in the vievfinder aperture. If background measuremtn was performed before, background will be subtracted. If zero-point was set-up, magnitude will be calculated with respect to the zero-point.
*   **c** : column - count profile in a specific column is plotted. If used with zoomed image, only visible part of the column is plotted.
*   **l** : line - count profile in a specific line is plotted. If used with zoomed image, only visible part of the line is plotted.
*   **e** : elipse - izophots of part of the image are plotted.
*   **r** : radial profile of counts is plotted. The centroid is calculated and Gauss function is fitted with the resulting FWHM.
*   **x** : xternal - magic option for external functions.

#### Configuration

Number of setting can be set up, and will be used with the next runn of the script. To **save those setting**, in the Config window **activate checkbox** specific value. This value is written and reed from the config file (**FitsView.cfg**). By removing particular line from this file, the default value is adopted. Any of the configuration values can be passed to the program with the <font color="green">Widget approach</font>, as the cfg list passed as the argument of the Widget.

#### Widget

_from pymage_gui import *_ 

_cfg=["x_Col=1","y_Col=2"]_ 

_PM_window = PyMage(cfg)_ 

_PM_window.fname="plik.fits"_ 

_PM_window.newFits()_ 

_PM_window.coo_file="plik.coo"_ 

_PM_window.load_coo()_ 

#### Libraries:

Python3  
Astropy  
NumPy  
SciPy  
matplotlib  
PyQt5

#### Issues & ToDo:

*   On Mac OS Maveric in PyQt5 there is a bug with CSlider. If more than one (horizontal or vertical) are present, the display is messing first with the second.  

*   There can be some problems with PyQt 5.15\. Use later versions.
