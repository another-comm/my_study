
                    BetterWMF v4.02

Thank you for installing BetterWMF.

BetterWMF helps you inserting AutoCAD drawings into for example
MS-office documents. BetterWMF will improve the picture on the fly
for you:

- The size of the picture will exactly match the extents of the
  objects. No large empty border to fit the AutoCAD window.
- The picture is transparent, the background color is removed.
- You can assign line weights based on colors.
- In TILEMODE 0 you can merge paperspace and all viewports
- The picture can be converted to black and white.

You can use BetterWMF either by running BCLIPBRD.EXE, or by loading
the correct version of BWMFxxxx.ARX into AutoCAD.

-------------
Registration:
-------------
You are entitled to evaluate this program for 30 days. After that you
must register (see REGISTER.TXT).

-------------------
Starting BetterWMF:
-------------------
For AutoCAD R14, R2000/R2002 or R2004 load BWMF14.ARX, BWMF200x.ARX or
BWMF2004.ARX into AutoCAD, You can now copy drawing parts with
BWMFOUT or BCOPYCLIP and access all BetterWMF properties with
the command BWMFOPT.

Alternative installation method, for applications programs that do not
support ARX extensions: run BCLIPBRD.EXE and BetterWMF will appear as
an icon in the taskbar (bottom right of your screen). It will then
automaticaly intercept the Copy and Paste commands. Double-click the
icon to access the BetterWMF properties screen.

Please refer to the helpfile for more information.

Do not use both methods simultaneously, the result may confuse you.

----------------------
Important information:
----------------------
- When you assign width to lines and insert a picture into MS-Word 97
  you may get overshooting lines ("spikes"). This is solved in newer
  versions of Office 2000.
- When using WIPEOUT objects in your drawings AutoCAD will crash on
  performing a normal WMFOUT. As BetterWMF relies on AutoCAD's normal
  WMFOUT for its operation, it cannot handle drawings with WIPEOUT's
  either.
- When running the clipboard viewer while Bwmfout.arx is used in
  AutoCAD you may get the message 'Cannot open clipboard'. This is
  because BetterWMF is modifying the clipboard so fast the clipboard
  viewer cannot keep up. Please close the clipboard viewer.

---------------
Uninstallation:
---------------
Simply remove all files from the installation directory
(default C:\Program Files\Furix\BetterWMF).
No other files are created or used by BetterWMF.

-----------------
Legal disclaimer:
-----------------
Using BetterWMF means acceptance of this disclaimer of warranty.
BetterWMF is supplied as is. The author disclaims all warranties,
expressed or implied, including, without limitation, the warranties
of merchantability and of fitness for any purpose. The author assumes
no liability for damages, direct or consequential, which may result
from the use of BetterWMF.

-------------------
Reporting Problems:
-------------------
If you encounter problems, please visit http://www.furix.com and
download the latest version to see if the issue has been resolved.
If not, please send a bug report to info@furix.com.