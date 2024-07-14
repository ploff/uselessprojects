import configparser
from PyQt5.QtGui import QPixmap, QFont, QDesktopServices
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QAbstractItemView, QTableWidgetItem,
    QHeaderView, QTabWidget, QWidget, QVBoxLayout, QLineEdit, QPushButton, QProgressBar,
    QLabel, QAction, QFileDialog, QMessageBox, QDialog, QDialogButtonBox, QSystemTrayIcon,
    QCheckBox
)
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QThread, pyqtSignal, pyqtSlot, QTimer, QObject, QDate, QUrl

class AboutDialog(QDialog):
    def __init__(self, version):
        super().__init__()
        self.version = version
        self.setWindowTitle(".about")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        current_date = QDate.currentDate()

        if current_date.month() == 12 and current_date.day() == 22: # bd
            pixmap = QPixmap("icons/icon_hb.png")
            self.link = "https://youtu.be/K-ousdtJCuI?t=1311&si=GkrbMR_nLww7CyhU"
        if current_date.month() == 12 and current_date.day() >= 1 and current_date.day() <= 31: #ny
            pixmap = QPixmap("icons/icon_ny.png")
            self.link = "https://www.youtube.com/watch?v=E6IwkNUTluk"
        else:
            pixmap = QPixmap("icons/icon.png")
            self.link = "https://www.youtube.com/watch?v=zzZ_nkuWwGA"

        scaled_pixmap = pixmap.scaledToWidth(150)
        image_label = QLabel()
        image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        image_label.mousePressEvent = self.onImageClick

        label = QLabel(f".ploff_disk_analyzer_{self.version}")
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("System", 12, QFont.Bold))
        label2 = QLabel("developed by ploff @ 2023")
        label2.setAlignment(Qt.AlignCenter)
        label3 = QLabel("<a href='https://github.com/ploff'>GitHub</a>")
        label3.setAlignment(Qt.AlignCenter)

        self.updateCheckBox = QCheckBox(".check_updates")
        self.loadUpdateState()
        self.updateCheckBox.stateChanged.connect(self.saveUpdateState)

        close_button = QPushButton(".close")
        close_button.clicked.connect(self.close)

        layout.addWidget(image_label)
        layout.addWidget(label)
        layout.addWidget(label2)
        layout.addWidget(label3)
        layout.addWidget(self.updateCheckBox)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def onImageClick(self, event):
        QDesktopServices.openUrl(QUrl(self.link))

    def loadUpdateState(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        autoupdate = config.getboolean('Updater', 'checkUpdates')
        self.updateCheckBox.setChecked(autoupdate)

    def saveUpdateState(self, state):
        config = configparser.ConfigParser()
        config.read('config.ini')
        config.set('Updater', 'checkUpdates', str(bool(state)))
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
