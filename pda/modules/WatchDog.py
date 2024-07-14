# watchdog module for ploff disk analyzer

import logging
import time
import configparser
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PyQt5.QtCore import QThread, pyqtSignal
    
class DirectoryEventHandler(FileSystemEventHandler):
    def __init__(self, tray):
        super().__init__()
        self.tray = tray

    def log_event(self, event):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f'{event.event_type}: {event.src_path} @ {now}'
        if event.is_directory:
            message = f'.directory {message}'
        else:
            message = f'.file {message}'

    def on_deleted(self, event):
        self.log_event(event)

    def on_created(self, event):
        self.log_event(event)

    def on_moved(self, event):
        self.log_event(event)

    def on_modified(self, event):
        self.log_event(event)

class WatchdogThread(QThread):
    signal = pyqtSignal(str)

    def __init__(self, directory_path, parent=None):
        super().__init__()
        self.directory_path = directory_path

    def run(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', filename='files.log')
        logger = logging.getLogger()
        event_handler = DirectoryEventHandler(self.signal)
        observer = Observer()
        observer.schedule(event_handler, path=self.directory_path, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            observer.join()
            QApplication.quit()
