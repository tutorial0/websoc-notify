import sqlite3
import os.path
import datetime
from config import SQLITE_DIRECTORY

class sqlite_manager():
    def __init__(self, filename, row_factory=False):
        self.filename = SQLITE_DIRECTORY + filename + '.db'
        self.connection = sqlite3.connect(self.filename, isolation_level="IMMEDIATE")
        if row_factory:
            self.connection.row_factory = sqlite3.Row
        self.cur = self.connection.cursor()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.connection.commit()
        self.connection.close()
    
    def check_tables(self, course_codes):
        sql = ''
        for code in course_codes:
            sql += '''
            create table if not exists '{}' (
                last_updated    timestamp primary key not null,
                code            integer,
                name            text,
                num             text,
                c_type          text,
                section         text,
                instructor      text,
                time            text,
                room            text,
                final           text,
                max_slots       integer,
                enrolled        integer,
                waitlisted      integer,
                status          text
            );
            '''.format(code)
        
        self.cur.executescript(sql)
    
    def add_many(self, data: [dict]):
        self.check_tables([d['code'] for d in data])
        for d in data:
            sql = '''
            insert into '{}' values(:last_updated, :code, :name, :num, :c_type,
                :section, :instructor, :time, :room, :final, :max_slots,
                :enrolled, :waitlisted, :status)
            '''.format(d['code'])
            d['last_updated'] = datetime.datetime.now()
            self.cur.execute(sql, d)
        self.connection.commit()

    def add_row(self, data: dict):
        self.add_many([data])
    
    def get_latest(self, course_code):
        self.cur.execute("SELECT * FROM '{}' ORDER BY last_updated DESC LIMIT 1;".format(course_code))
        return self.cur.fetchone()
    
    def get_all_latest(self):
        self.cur.execute('SELECT name FROM sqlite_master WHERE type = "table"')
        data = []
        for course in self.cur.fetchall():
            data.append(self.get_latest(course[0]))

        return data
