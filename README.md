[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Basic information
* Python: 3.10
* Formatting: [Black](https://github.com/psf/black)
* Type hints: [Yes](https://docs.python.org/3/library/typing.html)
* PDF creation: [pdfLaTeX](https://tex.stackexchange.com/questions/49569)

## Install dependencies
[PyQt6](https://doc.qt.io/qtforpython/)
```
pip install --upgrade pip
pip install PyQt6
```

## Create executable
[PyInstaller](https://pyinstaller.org/en/stable/)
```
pip install --upgrade pip
pip install pyinstaller
pyinstaller --onefile --windowed --name cms1_u1 main.py
```
