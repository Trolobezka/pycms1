[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

![Screenshot](https://i.postimg.cc/HxfVMZvr/pycms1-screenshot-2.png)

## Basic information
* Python: 3.10
* Formatting: [Black](https://github.com/psf/black)
* Type hints: [Yes](https://docs.python.org/3/library/typing.html) with [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)
* PDF creation: [pdfLaTeX](https://tex.stackexchange.com/questions/49569)

## Install dependencies
[PyQt6](https://doc.qt.io/qtforpython/)
```bash
pip install --upgrade pip
pip install PyQt6
```
If you don't have pip installed, follow [this](https://pip.pypa.io/en/stable/installation).

## Run program
Navigate to the root folder of `pycms1` project and run:
```bash
python main.py
```

## Create executable (optional)
[PyInstaller](https://pyinstaller.org/en/stable/)
```bash
pip install --upgrade pip
pip install pyinstaller
pyinstaller --onefile --windowed --name cms1_u1 main.py
```

## Note for playing with PDFs in QWebEngineView
Correctly installing [WebEngine](https://riverbankcomputing.com/software/pyqtwebengine/download) for PyQt6 can be challenging. If you have problems, try the following:

1. Uninstall everything that could interfere with WebEngine installation:
```bash
pip uninstall --yes PyQt-builder qtconsole QtPy PyQt5 PyQt5-Qt5 PyQt5-sip PyQt6 PyQt6-Qt6 PyQt6-sip PyQt6-WebEngine PyQt6-WebEngine-Qt6 PyQtWebEngine PyQtWebEngine-qt5 PySide PySide2
```
2. Install only needed modules:
```bash
pip install --no-cache-dir PyQt6 PyQt6-WebEngine
```
