import os
from datetime import datetime
import re

from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from main import APP_PATH

Base = declarative_base()


class Format(Base):
    __tablename__ = "formats"
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True, index=True)
    splitter = Column(String)
    date_time_index = Column(Integer)
    date_time_format = Column(String)
    level_index = Column(Integer)
    key_value_regex = Column(String)

    def __init__(self, title: str,
                 splitter=None,
                 date_time_index=None,
                 date_time_format=None,
                 level_index=None,
                 key_value_regex=None):
        self.title = title
        self.splitter = splitter
        self.date_time_index = date_time_index
        self.date_time_format = date_time_format
        self.level_index = level_index
        self.key_value_regex = key_value_regex

    def __repr__(self):
        return self.title


class LogFile(Base):
    __tablename__ = "log_files"

    id = Column(Integer, primary_key=True)
    path = Column(String, index=True)
    format_id = Column(Integer, ForeignKey("formats.id", ondelete='SET NULL'))
    last_opened = Column(DateTime, default=func.now())

    def __init__(self, file_path):
        self.path = file_path
        self.lines = None
        self.format = None
        self.min_date_time = None
        self.max_date_time = None
        self.levels = set()
        self.read_lines()

    def read_lines(self):
        with open(self.path, "r") as f:
            self.lines = [x.strip() for x in f.readlines()]

    def init_format(self):
        if self.format_id is None:
            return
        current_format = session.query(Format).filter(Format.id == self.format_id).first()
        self.set_format(current_format)

    def set_format(self, new_format: Format):
        self.levels = set()
        parsed_lines = []
        self.format_id = new_format.id
        self.format = new_format
        for line in self.lines:
            parsed_line = LogLine(line, self.format)
            if not hasattr(self, "min_date_time") or parsed_line.date_time < self.min_date_time:
                self.min_date_time = parsed_line.date_time
            if not hasattr(self, "max_date_time") or parsed_line.date_time > self.max_date_time:
                self.max_date_time = parsed_line.date_time
            if parsed_line.level not in self.levels:
                self.levels.add(parsed_line.level)
            parsed_lines.append(parsed_line)
        self.lines = parsed_lines

    def __getitem__(self, index):
        return self.lines[index]

    def __len__(self):
        return len(self.lines)


class LogLine:
    def __init__(self, line, new_format):
        if type(line) == str:
            self.line = line
        else:
            self.line = str(line)
        self.format = new_format
        self.date_time = None
        self.level = None
        self.meta = {}
        self.parse()

    def parse(self):
        parts = [self.line]
        if len(self.format.splitter) > 0:
            parts = [x.strip() for x in self.line.split(self.format.splitter)]
        if self.format.date_time_format is not None and self.format.date_time_index is not None:
            count_splitter_in_date_time_format = self.format.date_time_format.count(self.format.splitter)
            if count_splitter_in_date_time_format > 0:
                parts = parts[:self.format.date_time_index] + \
                        [self.format.splitter.join(parts[self.format.date_time_index:self.format.date_time_index + count_splitter_in_date_time_format + 1])] + \
                        parts[self.format.date_time_index + count_splitter_in_date_time_format + 1:]
            datetime_string = parts[self.format.date_time_index]
            datetime_format = self.format.date_time_format
            self.date_time = datetime.strptime(datetime_string, datetime_format)
        if self.format.level_index is not None:
            self.level = parts[self.format.level_index]
        if self.format.key_value_regex is not None:
            results = re.findall(self.format.key_value_regex, self.line)
            for result in results:
                self.meta[result[0]] = result[1]

    def __repr__(self):
        return self.line


db_path = os.path.join(APP_PATH, "main.db")
print(f"sqlite://{db_path}")
engine = create_engine(f"sqlite:///{db_path}", echo=True)
Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)
session = Session()
session.commit()
