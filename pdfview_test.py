# Source:
# https://python-forum.io/thread-36741-post-155217.html#pid155217 (Axel_Erfurt)
# https://github.com/Axel-Erfurt (Axel Schneider)

import sys
from os import path

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView


class MainWindow(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()

        self.setWindowTitle("PDF Viewer")
        self.setGeometry(0, 28, 1000, 750)

        self.webView = QWebEngineView()
        self.webView.settings().setAttribute(
            self.webView.settings().WebAttribute.PluginsEnabled, True
        )
        self.webView.settings().setAttribute(
            self.webView.settings().WebAttribute.PdfViewerEnabled, True
        )
        self.setCentralWidget(self.webView)

    def url_changed(self):
        self.setWindowTitle(self.webView.title())

    def go_back(self):
        self.webView.back()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()

    wd = path.dirname(sys.argv[0])
    filepath = "out"
    filename = "u1.pdf"
    pdf_path = str(path.join(wd, filepath, filename)).replace("\\", "/")
    url = QUrl(f"file:///{pdf_path}")
    win.webView.setUrl(url)

    sys.exit(app.exec())
