from PyQt6.QtWidgets import QMainWindow
from PyQt6 import uic

from datetime import timedelta


class Window(QMainWindow):
    def __init__(self, parent):
        super(Window, self).__init__(parent)
        uic.loadUi('ui/plot.ui', self)

        start_date_time = parent.dateTimeEditStart.dateTime().toPyDateTime()
        end_date_time = parent.dateTimeEditEnd.dateTime().toPyDateTime()
        date_time_delta_seconds = (end_date_time - start_date_time).total_seconds()
        count_chunks = 100
        chunk_distance = timedelta(seconds=date_time_delta_seconds / count_chunks)
        chunks = [start_date_time]
        for i in range(1, count_chunks):
            chunks.append(chunks[-1] + chunk_distance)
        chunks_dict = dict.fromkeys(chunks, 0)
        for line in parent.filtered_lines:
            for i in range(len(chunks) - 1):
                if chunks[i] <= line.date_time < chunks[i+1]:
                    chunks_dict[chunks[i]] = chunks_dict[chunks[i]] + 1
                    break
            else:
                if chunks[-1] <= line.date_time:
                    chunks_dict[chunks[-1]] = chunks_dict[chunks[-1]] + 1
        self.plot(chunks_dict)

    def plot(self, data_dict):
        self.widget.plot([x.timestamp() for x in data_dict.keys()], list(data_dict.values()))
