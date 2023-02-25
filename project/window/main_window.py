from PyQt6.QtWidgets import QMainWindow, QFileDialog, QTableWidgetItem
from PyQt6 import uic, QtGui, QtCore
from sqlalchemy.exc import SQLAlchemyError

from models import LogFile, Format, session
from window import format_configure, draw_plot

from datetime import datetime


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        uic.loadUi('ui/main.ui', self)

        self.log_file = None
        self.selected_format = None
        self.dialogs = list()
        self.format_actions = []
        self.recent_actions = []
        self.apply_filter_on_change = True
        self.key_values = {}
        self.search_text = ""
        self.filtered_lines = []

        self.list_view_model = QtGui.QStandardItemModel()
        self.listView.setModel(self.list_view_model)
        self.refresh_format_menu()
        self.refresh_recent_menu()

        self.dateTimeEditStart.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        self.dateTimeEditStart.dateTimeChanged.connect(self.apply_filter)
        self.dateTimeEditEnd.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        self.dateTimeEditEnd.dateTimeChanged.connect(self.apply_filter)
        self.tableWidgetKeyValues.setColumnCount(2)
        self.tableWidgetKeyValues.setHorizontalHeaderLabels(["Key", "Value"])
        self.tableWidgetKeyValues.itemSelectionChanged.connect(self.table_item_select)
        self.comboBoxLevel.currentIndexChanged.connect(self.apply_filter)
        self.pushButtonAdd.clicked.connect(self.add_key_value)
        self.toolButtonRemove.clicked.connect(self.remove_key_values)
        self.lineEditKey.returnPressed.connect(self.add_key_value)
        self.lineEditValue.returnPressed.connect(self.add_key_value)
        self.lineEditSearch.returnPressed.connect(self.search)
        self.pushButtonSearch.clicked.connect(self.search)

        self.actionOpen.triggered.connect(self.action_open)
        self.actionConfigure.triggered.connect(self.action_configure)
        self.actionDraw.triggered.connect(self.draw_plot)
        self.actionExit.triggered.connect(self.action_exit)
        self.show()

    def action_open(self):
        f_name = QFileDialog.getOpenFileName(self, "Open File", "", "Log Files (*.log)")
        if f_name:
            self.open_log_file(f_name[0])

    def open_log_file(self, file_path):
        print(file_path)
        log_file = session.query(LogFile).filter(LogFile.path == file_path).first()
        if log_file is None:
            self.log_file = LogFile(file_path)
            session.add(self.log_file)
            session.commit()
        else:
            self.log_file = log_file
            self.log_file.read_lines()
            self.log_file.init_format()
            if hasattr(self.log_file, "format"):
                self.labelFormat.setText(f"Format: {self.log_file.format.title}")
                self.selected_format = self.log_file.format
            self.log_file.last_opened = datetime.now()
            session.commit()
        self.lablePath.setText(file_path)
        self.lableCount.setText(str(len(self.log_file)))
        self.list_view_model.removeRows(0, self.list_view_model.rowCount())
        for line in self.log_file:
            item = QtGui.QStandardItem(str(line))
            self.list_view_model.appendRow(item)
        self.change_input_filters()

    def action_configure(self):
        dialog = format_configure.Window(self)
        self.dialogs.append(dialog)
        dialog.show()

    def refresh_format_menu(self):
        for action in self.format_actions:
            self.menuFormat.removeAction(action)
        self.format_actions = []
        formats = session.query(Format).all()
        for f in formats:
            new_action = QtGui.QAction(f.title, self)
            new_action.triggered.connect(self.select_format)
            self.format_actions.append(new_action)
            self.menuFormat.addAction(new_action)

    def refresh_recent_menu(self):
        for action in self.recent_actions:
            self.menuRecent.removeAction(action)
        self.recent_actions = []
        recent_files = session.query(LogFile).all()
        for recent in recent_files:
            new_action = QtGui.QAction(recent.path, self)
            new_action.triggered.connect(self.recent_action_clicked)
            self.recent_actions.append(new_action)
            self.menuRecent.addAction(new_action)

    @QtCore.pyqtSlot()
    def recent_action_clicked(self):
        action = self.sender()
        file_path = action.text()
        self.open_log_file(file_path)

    @QtCore.pyqtSlot()
    def select_format(self):
        action = self.sender()
        format_title = action.text()
        selected_format = session.query(Format).filter(Format.title == format_title).first()
        self.selected_format = selected_format
        self.labelFormat.setText(f"Format: {self.selected_format}")
        if self.log_file:
            self.log_file.set_format(self.selected_format)
            session.commit()

    def change_input_filters(self):
        self.apply_filter_on_change = False
        enable = self.log_file is not None and self.selected_format is not None
        self.dateTimeEditStart.setEnabled(enable)
        self.dateTimeEditStart.setDateTime(self.log_file.min_date_time)
        self.dateTimeEditStart.setMinimumDateTime(self.log_file.min_date_time)
        self.dateTimeEditStart.setMaximumDateTime(self.log_file.max_date_time)
        self.dateTimeEditEnd.setEnabled(enable)
        self.dateTimeEditEnd.setDateTime(self.log_file.max_date_time)
        self.dateTimeEditEnd.setMinimumDateTime(self.log_file.min_date_time)
        self.dateTimeEditEnd.setMaximumDateTime(self.log_file.max_date_time)
        self.comboBoxLevel.setEnabled(enable)
        self.comboBoxLevel.clear()
        self.comboBoxLevel.addItems(["All"] + list(self.log_file.levels))
        self.lineEditKey.setEnabled(enable)
        self.lineEditValue.setEnabled(enable)
        self.pushButtonAdd.setEnabled(enable)
        self.apply_filter_on_change = True
        if enable:
            self.filtered_lines = self.log_file.lines
        print(len(self.filtered_lines))

    def add_key_value(self):
        key = self.lineEditKey.text()
        value = self.lineEditValue.text()
        if len(key) == 0 or len(value) == 0:
            return
        self.lineEditKey.setText("")
        self.lineEditValue.setText("")
        self.key_values[key] = value
        self.update_key_value_table()

    def update_key_value_table(self):
        count_rows = len(self.key_values.keys())
        self.tableWidgetKeyValues.setRowCount(count_rows)
        for index, key in enumerate(self.key_values.keys()):
            self.tableWidgetKeyValues.setItem(index, 0, QTableWidgetItem(key))
            self.tableWidgetKeyValues.setItem(index, 1, QTableWidgetItem(self.key_values[key]))
        self.apply_filter()

    def apply_filter(self):
        if self.apply_filter_on_change:
            self.filtered_lines = []
            start_date_time = self.dateTimeEditStart.dateTime().toPyDateTime()
            end_date_time = self.dateTimeEditEnd.dateTime().toPyDateTime()
            level = self.comboBoxLevel.currentText()
            self.list_view_model.removeRows(0, self.list_view_model.rowCount())
            for line in self.log_file:
                if start_date_time <= line.date_time <= end_date_time:
                    if level == "All" or line.level == level:
                        # print(line.meta)
                        for key in self.key_values:
                            if key not in line.meta or line.meta[key] != self.key_values[key]:
                                break
                        else:
                            if len(self.search_text) == 0 or self.search_text in line.line:
                                item = QtGui.QStandardItem(str(line))
                                self.filtered_lines.append(line)
                                self.list_view_model.appendRow(item)
            self.lableCount.setText(str(self.list_view_model.rowCount()))

    def table_item_select(self):
        items = self.tableWidgetKeyValues.selectedItems()
        self.toolButtonRemove.setEnabled(len(items) > 0)

    def remove_key_values(self):
        items = self.tableWidgetKeyValues.selectedItems()
        rows = []
        for item in items:
            row = item.row()
            if row not in rows:
                rows.append(row)
        keys = [self.tableWidgetKeyValues.item(row, 0).text() for row in rows]
        for key in keys:
            self.key_values.pop(key)
        self.update_key_value_table()

    def search(self):
        self.search_text = self.lineEditSearch.text()
        self.apply_filter()

    def draw_plot(self):
        dialog = draw_plot.Window(self)
        self.dialogs.append(dialog)
        dialog.show()

    def action_exit(self):
        self.close()
