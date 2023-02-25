from PyQt6.QtWidgets import QMainWindow, QFileDialog
from PyQt6 import uic, QtGui

from models import Format, session


class Window(QMainWindow):
    def __init__(self, parent):
        super(Window, self).__init__(parent)
        uic.loadUi('ui/format.ui', self)

        self.selected_format = None
        self.list_view_model = QtGui.QStandardItemModel()
        self.listView.setModel(self.list_view_model)
        self.listView.clicked.connect(self.list_view_click)
        self.refresh_list_view()
        self.toolButtonAdd.clicked.connect(self.add_format)
        self.toolButtonRemove.clicked.connect(self.remove_format)
        self.pushButtonSave.clicked.connect(self.save)
        self.show()

    def refresh_list_view(self):
        index = None
        self.list_view_model.removeRows(0, self.list_view_model.rowCount())
        formats = session.query(Format).all()
        for i, f in enumerate(formats):
            item = QtGui.QStandardItem(f.title)
            self.list_view_model.appendRow(item)
            if self.selected_format is not None and f.title == self.selected_format.title:
                index = i
        if index:
            model_index = self.list_view_model.index(index, 0)
            self.listView.setCurrentIndex(model_index)

    def list_view_click(self, index):
        result = session.query(Format).filter(Format.title == index.data()).first()
        self.selected_format = result
        self.set_values()
        self.inputs_enabled(True)

    def add_format(self):
        new_format = Format("Untitled")
        session.add(new_format)
        session.commit()
        self.selected_format = new_format
        self.set_values()
        self.inputs_enabled(True)
        self.refresh_list_view()

    def remove_format(self):
        session.delete(self.selected_format)
        session.commit()
        self.selected_format = None
        self.inputs_enabled(False)
        self.refresh_list_view()

    def inputs_enabled(self, enabled):
        self.lineEditTitle.setEnabled(enabled)
        self.lineEditSplitter.setEnabled(enabled)
        self.spinBoxDateTimeIndex.setEnabled(enabled)
        self.spinBoxLevelIndex.setEnabled(enabled)
        self.lineEditDateTimeFormat.setEnabled(enabled)
        self.lineEditKeyValueRegex.setEnabled(enabled)
        self.pushButtonSave.setEnabled(enabled)
        self.toolButtonRemove.setEnabled(enabled)

    def save(self):
        title = self.lineEditTitle.text()
        if len(title) == 0:
            return
        splitter = self.lineEditSplitter.text()
        date_time_index = self.spinBoxDateTimeIndex.value()
        level_index = self.spinBoxLevelIndex.value()
        date_time_format = self.lineEditDateTimeFormat.text()
        key_value_regex = self.lineEditKeyValueRegex.text()
        if date_time_index == level_index:
            return
        self.selected_format.title = title
        self.selected_format.splitter = splitter
        self.selected_format.date_time_index = date_time_index
        self.selected_format.level_index = level_index
        self.selected_format.date_time_format = date_time_format
        self.selected_format.key_value_regex = key_value_regex
        session.commit()
        self.refresh_list_view()

    def set_values(self):
        self.lineEditTitle.setText(self.selected_format.title)

        if self.selected_format.splitter:
            self.lineEditSplitter.setText(self.selected_format.splitter)
        else:
            self.lineEditSplitter.setText("")

        if self.selected_format.date_time_index:
            self.spinBoxDateTimeIndex.setValue(self.selected_format.date_time_index)
        else:
            self.spinBoxDateTimeIndex.setValue(0)

        if self.selected_format.level_index:
            self.spinBoxLevelIndex.setValue(self.selected_format.level_index)
        else:
            self.spinBoxLevelIndex.setValue(0)

        if self.selected_format.date_time_format:
            self.lineEditDateTimeFormat.setText(self.selected_format.date_time_format)
        else:
            self.lineEditDateTimeFormat.setText("")

        if self.selected_format.key_value_regex:
            self.lineEditKeyValueRegex.setText(self.selected_format.key_value_regex)
        else:
            self.lineEditKeyValueRegex.setText("")

    def closeEvent(self, event):
        print(self.parent().refresh_format_menu())
