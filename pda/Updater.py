import sys
import json
import os
import socket
import hashlib
import subprocess
import configparser
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QProgressBar, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class UpdateChecker(QThread):
    update_found = pyqtSignal(bool)

    def __init__(self, progress_label):
        super().__init__()
        self.progress_label = progress_label
        self.chklink = "https://ploff.github.io/pda/update.json"

    def run(self):
        if self.is_internet_available():
            config = self.load_config()
            if config.getboolean('Updater', 'checkupdates'):
                current_version = self.get_current_version()
                latest_version = self.get_latest_version_from_server()
                latest_version, latest_hash = self.get_latest_version_from_server()

                if latest_version and latest_version > current_version:
                    if self.check_hash(latest_hash):
                        self.update_found.emit(False)
                    else:
                        self.update_found.emit(True)
                else:
                    self.progress_label.setText(".no_updates_available")
                    reply = QMessageBox.question(None, '.updater', ".no_updates_available, wanna_start_analyzer?", QMessageBox.Yes | QMessageBox.No)

                    if reply == QMessageBox.Yes:
                        subprocess.Popen(["./pda.ploff"])
                        QApplication.exit(0)
                    else:
                        QApplication.exit(0)
            else:
                self.progress_label.setText(".skipping_updater")
                subprocess.Popen(["./pda.ploff"])
                QApplication.quit()
        else:
            print('no internet')
            self.showErrMsg('.no_internet_connection')
            subprocess.Popen(["./pda.ploff"])
            QApplication.quit()

    def check_hash(self, latest_hash):
        if os.path.exists('pda.ploff'):
            with open('pda.ploff', 'rb') as file:
                file_data = file.read()
                calculated_hash = hashlib.md5(file_data).hexdigest()
                return calculated_hash == latest_hash
        else:
            return False

    def load_config(self):
        config = configparser.ConfigParser()
        if not os.path.exists('config.ini'):
            self.create_default_config()
        config.read('config.ini')
        return config
        
    def create_default_config(self):
        config = configparser.ConfigParser()
        config['Updater'] = {'checkupdates': 'False'}
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    def is_internet_available(self):
        try:
            socket.create_connection(("www.google.com", 80))
            return True
        except OSError:
            pass
        return False

    def get_current_version(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        if 'version' in config['DiskAnalyzer']:
            version_str = config['DiskAnalyzer']['version']
            version = float(version_str)
            print(f"installed: {version}")
            return version
        else:
            print(".there_is_no_version_value_in_config")
            return 0.0

    def get_latest_version_from_server(self):
        try:
            response = requests.get(self.chklink)
            response.raise_for_status()
            data = response.json()
            latest_version = data.get('version')
            latest_hash = data.get('hash')
            return float(latest_version), latest_hash
        except requests.exceptions.RequestException as e:
            self.showErrMsg(f'.download_err: {str(e)}')
            return 0.0, None

    def showErrMsg(self, errMsg):
        QMessageBox.critical(None, ".error", errMsg)
        return 0


class UpdaterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('.updater')
        self.setFixedSize(300,100)
        layout = QVBoxLayout()

        self.progress_label = QLabel('.checking_for_updates...')
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)

        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

        self.update_checker = UpdateChecker(self.progress_label)
        self.update_checker.update_found.connect(self.show_update_dialog)
        self.update_checker.start()

    def show_update_dialog(self, update_available):
        if update_available:
            self.progress_label.setText('.update_available')
            self.progress_bar.hide()

            update_button = QPushButton('.update')
            skip_button = QPushButton('.skip')

            update_button.clicked.connect(self.download_update)
            skip_button.clicked.connect(self.skipUpdate)
        
            layout = self.layout()
            layout.addWidget(update_button)
            layout.addWidget(skip_button)

            self.setLayout(layout)

    def download_update(self):
        update_button = self.sender()
        update_button.setEnabled(False)
        update_url = 'https://github.com/ploff/test/releases/download/b00b135/Analyzer'
        self.download_thread = DownloadThread(update_url)
        self.download_thread.update_progress.connect(self.update_progress_bar)
        self.download_thread.finished.connect(self.download_finished)

        for button in self.findChildren(QPushButton):
            if button.text() == ".update" or button.text() == ".skip":
                button.hide()

        self.progress_bar.show()

        self.download_thread.start()

    def no_update_needed(self):
        self.progress_label.setText(".no_update_needed_message")
        subprocess.Popen(["./pda.ploff"])
        QApplication.quit()

    def download_finished(self):
        self.progress_label.setText(".download_finished")

        for button in self.findChildren(QPushButton):
            if button.text() == ".update":
                button.hide()
            elif button.text() == ".skip":
                button.setText(".launch")

        launch_button = QPushButton(".launch")
        launch_button.clicked.connect(self.skipUpdate)
        layout = self.layout()
        layout.addWidget(launch_button)
        self.setLayout(layout)

        self.progress_bar.hide()
        
    def skipUpdate(self):
        self.progress_label.setText(".skipping_update")
        subprocess.Popen(["./pda.ploff"])
        QApplication.quit()
        
    def update_progress_bar(self, received, total):
        received_mb = received / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        percent = int(received * 100 / total)
        self.progress_label.setText(f'.downloading: {received_mb:.2f} MB of {total_mb:.2f} MB')
        self.progress_bar.setValue(percent)

    def showErrMsg(self, errMsg):
        QMessageBox.critical(self, ".error", errMsg)
        self.writeToLog(errMsg)

class DownloadThread(QThread):
    update_progress = pyqtSignal(int, int)

    def __init__(self, update_url):
        super().__init__()
        self.update_url = update_url

    def run(self):
        try:
            response = requests.get(self.update_url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open('pda.ploff', 'wb') as file:
                for data in response.iter_content(chunk_size=1024):
                    file.write(data)
                    downloaded += len(data)
                    self.update_progress.emit(downloaded, total_size)

        except requests.exceptions.RequestException as e:
            self.showErrMsg(f'.download_err: {str(e)}')

        self.update_progress.emit(total_size, total_size)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = UpdaterWindow()
    window.show()
    sys.exit(app.exec_())
