import sqlite3
import os.path
import datetime
from config import SQLITE_DIRECTORY

class sqlite_manager():
    def __init__(self, filename):
        self.filename = SQLITE_DIRECTORY + filename + '.db'
        self.connection = sqlite3.connect(self.filename, isolation_level=None)
        self.cur = self.connection.cursor()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.connection.commit()
        self.connection.close()
    
    def check_table(self, course_code):
        sql = '''
        create table if not exists '{}' (
            ts              timestamp primary key not null,
            code            integer,
            name            text,
            num             text,
            c_type          text,
            section         text,
            instructor      text,
            time            text,
            room            text,
            max_slots       integer,
            enrolled        integer,
            waitlisted      integer,
            status          text
        );
        '''.format(course_code)
        
        self.cur.execute(sql)
    
    def add_row(self, data):
        data = dict(data)
        self.check_table(data['code'])
        sql = '''
        insert into '{}' values(:ts, :code, :name, :num, :c_type,
            :section, :instructor, :time, :room, :max_slots,
            :enrolled, :waitlisted, :status)
        '''.format(data['code'])
        if data['waitlisted'] == 'n/a':
            data['waitlisted'] = None
        data['ts'] = datetime.datetime.now()
        self.cur.execute(sql, data)
        
    def get_latest(self, course_code):
        self.cur.execute('SELECT * FROM ? ORDER BY ts DESC LIMIT 1;'(course_code,))
        return self.cur.fetchone()[0]
    
    
