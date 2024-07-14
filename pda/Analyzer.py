import hashlib
import configparser
import os
import csv
import json
import subprocess
import time
import platform
import matplotlib.pyplot as plt
# local modules start
from modules.AboutWindow import AboutDialog
from modules.ftm import FileTableModel
from modules.WatchDog import DirectoryEventHandler
from modules.WatchDog import WatchdogThread
# local modules end
from datetime import datetime
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QAbstractItemView, QTableWidgetItem,
    QHeaderView, QTabWidget, QWidget, QVBoxLayout, QLineEdit, QPushButton, QProgressBar,
    QLabel, QAction, QFileDialog, QMessageBox, QSystemTrayIcon, QMenu
)
from PyQt5.QtCore import QAbstractTableModel, QThread, pyqtSignal, QDate

class DiskAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.version = "1.4"

        config = configparser.ConfigParser()
        config.read('config.ini')

        if not os.path.exists('config.ini'): # проверка на существование конфига
            config = configparser.ConfigParser()
            config['DiskAnalyzer'] = {'version': self.version}
            config['Updater'] = {'checkupdates': 'False'}
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
        else: # и проверка на соответствие версии в конфиге
            config = configparser.ConfigParser()
            config.read('config.ini')
            if 'DiskAnalyzer' in config and 'version' in config['DiskAnalyzer']:
                if self.version != config['DiskAnalyzer']['version']:
                    config['DiskAnalyzer']['version'] = self.version
                    with open('config.ini', 'w') as configfile:
                        config.write(configfile)

        self.setWindowTitle(f".ploff_disk_analyzer_{self.version}")
        self.resize(1024, 768)
        self.setMinimumSize(800, 600)

        self.tray = QSystemTrayIcon()

        current_date = QDate.currentDate()

        if current_date.month() == 11 and current_date.day() >= 15 and current_date.day() <= 31:
            self.icon = QIcon("icons/icon_ny.png")
        else:
            self.icon = QIcon("icons/icon.png")

        self.tray.setIcon(self.icon)
        self.tray.setToolTip(f".ploff_disk_analyzer_{self.version}")

        traymenu = QMenu()

        action1 = QAction(".exit", self)
        action1.triggered.connect(self.closeEvent)
        traymenu.addAction(action1)
        
        self.tray.setContextMenu(traymenu)
        self.tray.show()

        self.searchInput = QLineEdit()
        self.searchInput.setEnabled(False)
        self.searchInput.setPlaceholderText(".search")
        self.searchInput.textChanged.connect(self.filterFileTables)

        self.tabWidget = QTabWidget()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.searchInput)
        self.layout.addWidget(self.tabWidget)

        centralWidget = QWidget()
        centralWidget.setLayout(self.layout)
        self.setCentralWidget(centralWidget)

        self.fileData = []
        self.fileTypeDataDict = {}

        self.exportButton = self.menuBar().addMenu(".export_data")
        self.exportButton.setEnabled(False)
        self.exportAsCSV = QAction(".as_csv", self)
        self.exportAsJSON = QAction(".as_json", self)
        self.exportAsCSV.triggered.connect(lambda: self.exportData('csv'))
        self.exportAsJSON.triggered.connect(lambda: self.exportData('json'))
        self.exportButton.addAction(self.exportAsCSV)
        self.exportButton.addAction(self.exportAsJSON)

        self.aboutButton = self.menuBar().addAction(".update")
        self.aboutButton.triggered.connect(self.toUpdate)

        self.aboutButton = self.menuBar().addAction(".about")
        self.aboutButton.triggered.connect(self.aboutWindow)

        self.pathInput = QLineEdit()
        self.pathInput.setContentsMargins(20, 0, 0, 0)
        self.pathInput.setPlaceholderText(".click_here_to_start_work")
        self.pathInput.setReadOnly(True)
        self.pathInput.mousePressEvent = self.chooseDirectoryDialog

        self.scanButton = QPushButton(".scan")
        self.visualButton = QPushButton(".visualize")
        self.visualButton.setEnabled(False)
        self.visualButton.clicked.connect(self.visualizeDiskSpace)
        self.statusBar().addWidget(self.visualButton)

        self.progressBar = QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        self.progressBar.setTextVisible(True)

        self.scanButton.clicked.connect(self.startScan)

        visualizeWidget = QWidget()
        visualizeLayout = QVBoxLayout()
        visualizeLayout.addWidget(self.visualButton)
        visualizeWidget.setLayout(visualizeLayout)
        self.statusBar().addPermanentWidget(visualizeWidget)
        self.statusBar().addPermanentWidget(self.progressBar)
        self.statusBar().addWidget(self.pathInput)
        self.statusBar().addWidget(self.scanButton)
        self.statusLabel = QLabel(".ready")
        self.statusBar().addPermanentWidget(self.statusLabel)

    def filterFileTables(self, text):
        for fileType, data in self.fileTypeDataDict.items():
            tableWidget = data['tableWidget']
            for row in range(tableWidget.rowCount()):
                item = tableWidget.item(row, 0)
                file_path = item.text().lower()
                if text.lower() in file_path:
                    tableWidget.setRowHidden(row, False)
                else:
                    tableWidget.setRowHidden(row, True)

    def aboutWindow(self):
        about = AboutDialog(self.version)
        about.exec_()

    def toUpdate(self, event):
        reply = QMessageBox.question(None, '.updater', ".wanna_check_updates?\n.all_unsaved_data_will_lose", QMessageBox.Yes | QMessageBox.No) # why the fuck i wrote "unsaved"?

        if reply == QMessageBox.Yes:
            subprocess.Popen(["./updater.ploff"])
            print("gone to update")
            QApplication.exit(0)
        else:
            event.ignore()

    def chooseDirectoryDialog(self, event):
        self.folderPath = QFileDialog.getExistingDirectory(self, ".select_directory")
        if self.folderPath:
            self.pathInput.setText(self.folderPath)

    def startScan(self):
        path = self.pathInput.text()
        self.searchInput.setEnabled(False)
        self.visualButton.setEnabled(False)
        self.exportButton.setEnabled(False)
        if not os.path.isdir(path):
            self.showErrMsg(".wrong_directory_path.")
            return

        with open('files.log', 'a') as log_file:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f'.started logging {path} @ {now}\n')

        self.fileData = []
        self.progressBar.setMaximum(0)

        self.scanThread = ScanThread(path)
        self.scanThread.scanFinished.connect(self.scanFinished)
        self.scanThread.errorOccurred.connect(self.showErrMsg)
        self.scanThread.start()

        self.tray.setToolTip(f".ploff_disk_analyzer_{self.version}\n.scanning")
        self.statusLabel.setText(".scanning")

    def scanFinished(self, file_data):
        path = self.pathInput.text()
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(100)
        self.exportButton.setEnabled(True)
        self.visualButton.setEnabled(True)
        self.searchInput.setEnabled(True)
        self.fileData = file_data
        self.tabWidget.clear()

        self.createFileTable("All Files")

        fileTypes = set([fileInfo['fileType'] for fileInfo in self.fileData])
        for fileType in fileTypes:
            if fileType != "All Files" and fileType != "":
                self.createFileTable(fileType)
                
        self.scanThread.stop()
        self.startWatchdog(path)

        self.tray.setToolTip(f".ploff_disk_analyzer_{self.version}\n.scan_finished")
        self.tray.showMessage(".ploff_disk_analyzer", ".scan_finished")

        self.statusLabel.setText(".last_update: " + time.strftime("%H:%M:%S"))

    def startWatchdog(self, path):
        self.path = path
        self.watchdog_thread = WatchdogThread(self.path)
        self.watchdog_thread.signal.connect(self.onWatchdogSignal)
        self.watchdog_thread.start()

    def onWatchdogSignal(self, message):
        with open('files.log', 'a') as log_file:
            log_file.write(f'{message}\n')

    def analyzeDisk(self, path):
        fileData = []

        for root, dirs, files in os.walk(path):
            for file in files:
                filePath = os.path.join(root, file)
                fileExtension = os.path.splitext(filePath)[1][1:]

                checksum = self.calculateChecksum(filePath)
                fileSize = os.path.getsize(filePath)
                creationDate = os.path.getctime(filePath)

                fileData.append({
                    'path': filePath,
                    'checksum': checksum,
                    'hasDuplicate': self.checkDuplicate(checksum, filePath, fileData),
                    'fileSize': fileSize,
                    'creationDate': time.ctime(creationDate),
                    'fileType': fileExtension
                })

        return fileData

    def calculateChecksum(self, filePath):
        if not os.path.isfile(filePath):
            return None

        with open(filePath, 'rb') as file:
            data = file.read()
            checksum = hashlib.md5(data).hexdigest()
            return checksum

    def checkDuplicate(self, checksum, filePath, fileData):
        for data in fileData:
            if data['checksum'] == checksum and data['path'] != filePath:
                return True
        return False

    def openFile(self, row, column, tabIndex):
        if row < self.tableWidget.rowCount() and column < self.tableWidget.columnCount():
            item = self.tableWidget.item(row, column)
            if item:
                file_path = item.text()

                if platform.system() == 'Windows':
                    os.startfile(file_path)
                elif platform.system() == 'Linux':
                    os.system('xdg-open "{}"'.format(file_path))
                else:
                    self.showErrMsg(".unsupported_platform")
            else:
                self.showErrMsg(".empty_item")
        else:
            self.showErrMsg(".out_of_bounds")

    def createFileTable(self, fileType):
        if fileType == "All Files":
            fileTypeData = self.fileData
        else:
            fileTypeData = [fileInfo for fileInfo in self.fileData if fileInfo['fileType'] == fileType]

        self.tableWidget = QTableWidget()
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.cellDoubleClicked.connect(lambda row, column=0, tabIndex=self.tabWidget.currentIndex(): self.openFile(row, column, tabIndex))  # connect double click signal to openFile function with tabIndex
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSortingEnabled(True)
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setRowCount(len(fileTypeData))

        self.tableWidget.setHorizontalHeaderLabels([".path", ".checksum", ".has_duplicate", ".file_size", ".creation_date"])

        for row, fileInfo in enumerate(fileTypeData):
            item = QTableWidgetItem(fileInfo['path'])
            self.tableWidget.setItem(row, 0, item)

            item = QTableWidgetItem(fileInfo['checksum'])
            self.tableWidget.setItem(row, 1, item)

            item = QTableWidgetItem("✔️" if fileInfo['hasDuplicate'] else "❌")
            self.tableWidget.setItem(row, 2, item)

            item = QTableWidgetItem(self.convertSize(fileInfo['fileSize']))
            self.tableWidget.setItem(row, 3, item)

            item = QTableWidgetItem(fileInfo['creationDate'])
            self.tableWidget.setItem(row, 4, item)

        tabIndex = self.tabWidget.addTab(QWidget(), fileType.upper())
        self.tabWidget.setTabToolTip(tabIndex, fileType.upper())
        self.tabWidget.widget(tabIndex).setLayout(QVBoxLayout())
        self.tabWidget.widget(tabIndex).layout().addWidget(self.tableWidget)

        totalSize = sum([fileInfo['fileSize'] for fileInfo in fileTypeData])
        totalFiles = len(fileTypeData)

        totalSizeLabel = QLabel()
        totalFilesLabel = QLabel()

        totalSizeLabel.setText(f".total_size: {self.convertSize(totalSize)}")
        totalFilesLabel.setText(f".total_files: {totalFiles}")

        self.tabWidget.widget(tabIndex).layout().addWidget(totalSizeLabel)
        self.tabWidget.widget(tabIndex).layout().addWidget(totalFilesLabel)

        self.fileTypeDataDict[fileType] = {
            'tableWidget': self.tableWidget,
            'totalSizeLabel': totalSizeLabel,
            'totalFilesLabel': totalFilesLabel
        }

    def highlightDuplicates(self):
        hashCounts = {}
        for fileInfo in self.fileData:
            checksum = fileInfo['checksum']
            if checksum in hashCounts:
                hashCounts[checksum].append(fileInfo)
            else:
                hashCounts[checksum] = [fileInfo]

        for checksum, files in hashCounts.items():
            if len(files) > 1:
                for fileInfo in files:
                    fileInfo['hasDuplicate'] = True

    def showErrMsg(self, errMsg):
        QMessageBox.critical(self, ".error", errMsg)
        self.writeToLog(errMsg)

    def writeToLog(self, errMsg):
        with open("error.log", "a") as ErrLog:
            ErrLog.write(f"{time.ctime()}: {errMsg}\n")

    def convertSize(self, sizeInBytes):
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if sizeInBytes < 1024.0:
                return "%3.1f %s" % (sizeInBytes, unit)
            sizeInBytes /= 1024.0
        return sizeInBytes

    def visualizeDiskSpace(self):
        directory = self.pathInput.text()
        if not os.path.isdir(directory):
            self.showErrMsg(".wrong directory path.")
            return

        file_sizes = {}

        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                file_extension = os.path.splitext(file_path)[1][1:]
                if file_extension in file_sizes:
                    file_sizes[file_extension] += file_size
                else:
                    file_sizes[file_extension] = file_size

        labels = list(file_sizes.keys())
        sizes = list(file_sizes.values())

        fig, ax = plt.subplots(figsize=(10, 7.68))
        ax.set_title('.disk_space_usage_at_directory()')

        colors = plt.cm.tab20.colors

        plt.pie(sizes, startangle=140, wedgeprops={'center': (0.6, 0.0)})

        legend_labels = [f"{label} - {self.convertSize(file_sizes[label])} ({sizes[i] / sum(sizes) * 100:.2f}%)" for i, label in enumerate(labels)]
        ax.legend(legend_labels, loc='center left', bbox_to_anchor=(-0.2, 0.5))

        plt.show()

    def exportData(self, fileFormat):
        dataToExport = self.fileData

        if fileFormat == 'csv':
            with open('export.csv', 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['path', 'checksum', 'hasDuplicate', 'fileSize', 'creationDate', 'fileType']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(dataToExport)
                self.tray.showMessage("ploff_disk_analyzer", "export_at_csv_completed")

        elif fileFormat == 'json':
            with open('export.json', 'w', encoding='utf-8') as jsonfile:
                json.dump(dataToExport, jsonfile, ensure_ascii=False, indent=4)
                self.tray.showMessage("ploff_disk_analyzer", "export_at_json_completed")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '.exit',
            ".really_wanna_quit?\n.all_unsaved_data_will_lose", QMessageBox.Yes |
            QMessageBox.No)

        if reply == QMessageBox.Yes:
            QApplication.exit(0)
        else:
            event.ignore()

class ScanThread(QThread):
    progressChanged = pyqtSignal(int)
    scanFinished = pyqtSignal(list)
    errorOccurred = pyqtSignal(str)

    def __init__(self, path, parent=None):
        super().__init__()
        self.path = path
        self._stop = False
        if parent:
            self.moveToThread(parent.thread())

    def stop(self):
        self._stop = True

    def run(self):
        self._stop = False
        try:
            fileData = DiskAnalyzer().analyzeDisk(self.path)
            if not self._stop:
                self.scanFinished.emit(fileData)
        except Exception as e:
            if not self._stop:
                self.errorOccurred.emit(str(e))

if __name__ == '__main__':
    app = QApplication([])
    window = DiskAnalyzer()
    window.show()
    app.exec()
