# file table model module for ploff disk analyzer

from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex

class FileTableModel(QAbstractTableModel):
    def __init__(self, file_data):
        super().__init__()
        self.fileData = fileData

    def rowCount(self, parent=QModelIndex()):
        return len(self.fileData)

    def columnCount(self, parent=QModelIndex()):
        return 5

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            fileInfo = self.fileData[row]

            if col == 0:
                return fileInfo['path']
            elif col == 1:
                return fileInfo['checksum']
            elif col == 2:
                return "✔️" if fileInfo['hasDuplicate'] else "❌"
            elif col == 3:
                return fileInfo['fileSize']
            elif col == 4:
                return fileInfo['creationDate']

        return None

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                headers = [".path", ".checksum", ".has duplicate", ".file size", ".creation date"]
                return headers[section]

        return None
