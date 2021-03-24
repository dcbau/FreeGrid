import numpy as np
from PyQt5 import QtCore


class MeasurementListModel(QtCore.QAbstractTableModel):
    def __init__(self):
        super(MeasurementListModel, self).__init__()
        self._data = np.array([])
        self.header = ["Az", "El", "Radius"]

    def set_data(self, data):
        self.layoutAboutToBeChanged.emit()
        self._data = data
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount(0), self.columnCount(0)))
        self.layoutChanged.emit()

    def add_position(self, row_value):

        if self._data.any():
            new_row = self._data.shape[0] + 1
            self.beginInsertRows(QtCore.QModelIndex(), new_row, new_row)
            self._data = np.append(self._data, row_value, axis=0)
            self.endInsertRows()

        else:
            self.beginResetModel()
            self._data = np.array(row_value, copy=True)
            self.endResetModel()

    def remove_position(self, id):

        try:
            try:
                start = id.min()
                end = id.max()
            except AttributeError:
                start = id
                end = id
            except ValueError:
                raise IndexError
            self.beginRemoveRows(QtCore.QModelIndex(), start, end)
            self._data = np.delete(self._data, id, axis=0)
            self.endRemoveRows()
        except IndexError:
            print("Could not remove measurement from data list: Invalid Id")



    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            if self._data.any():
                value = self._data[index.row(), index.column()]
                return str(value)

    def rowCount(self, index):
        try:
            return self._data.shape[0]
        except IndexError:
            return 0

    def columnCount(self, index):
        try:
            return self._data.shape[1]
        except IndexError:
            return 0

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]

        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return col + 1
        return None