import scrape_websoc
from datetime import datetime
import time
import pushbullet
import pprint
import traceback
from logger import *
from sqlite_manager import sqlite_manager
from config import *
from pathlib import Path
from Course import Course

class UserData:
    def __init__(self, email: str, user: str, courses: [int]):
        self._user = user
        self._courses = courses
        self._email = email

    def get_email(self) -> str:
        return self._email

    def get_name(self) -> str:
        return self._user

    def get_courses(self) -> str:
        return self._courses
    
    def set_courses(self, course_list):
        self._courses = course_list
        
    def set_email(self, email):
        self._email = email
    
    def __eq__(self, other):
        if type(other) == UserData: return self.get_name() == other.get_name()
        return other == self.get_name()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return 'UserData(email={}, user={}, courses={})'.format(self._email, self._user, self._courses)
    
    def __hash__(self):
        return hash(repr(self))

class App:
    def __init__(self):
        self._users = []
        self._last_course_data = []
        initialize_logger(str(Path(LOG_DIRECTORY)))
        with sqlite_manager(WEBSOC_TERM, row_factory=True) as s_manager:
            for course in s_manager.get_all_latest():
                d = {k:course[k] for k in course.keys() if k != 'last_updated'}
                c = Course()
                c.__dict__ = d
                self._last_course_data.append(c)
                
    def add_user(self, data: UserData) -> None:
        self._users.append(data)

    def get_new_course_data(self) -> [scrape_websoc.Course]:
        courses = set()
        for user in self._users:
            courses.update(user.get_courses())
        return scrape_websoc.query_websoc(list(courses))

    @staticmethod
    def parse_change(changes, old, new):
        old_dict = old.__dict__
        new_dict = new.__dict__
        
        s = '\n    '
        for change in changes:
            s += '{}: {} -> {}\n    '.format(change, old_dict[change], new_dict[change])

        info = '{code} (max: {c_max}) ({num} {c_type} {section} -- {instructor}): {string}'.format(
            c_max = new.max_slots, code = new.code, num = new.num, c_type = new.c_type,
            section = new.section, instructor = new.instructor, string = s.rstrip()
            )


        return info

    @staticmethod
    def notify(affects, info):
        affect_names = [user.get_name() for user in affects]
        logging.info('-- Affects: {}'.format(affect_names))

        for user in affects:
            name = user.get_name()
            email = user.get_email()
            if email:
                try:
                    pushbullet.send_push(email, '{}: websoc-notify'.format(name), info)
                except Exception as e:
                    logging.error('Could not push!')
                    logging.error('\t'+str(traceback.format_exc()))
                
    @staticmethod
    def notify_set(n_set):
        for x in n_set:
            App.notify(x[0], x[1])

    @staticmethod
    def write_sqlite(courses):
        with sqlite_manager(WEBSOC_TERM) as s_manager:
            s_manager.add_many([dict(course.__dict__) for course in courses])

    def refresh(self) -> None:
        now = datetime.now()
        logging.info('=============== {} ==============='.format(str(now)))
        new_data = self.get_new_course_data()

        notification_set = set()
        queued_sql_entries = []
        for new in new_data:
            if new not in self._last_course_data:
                logging.info('Added {code} (max: {c_max}) ({num} {c_type} {section} -- {instructor})'.format(
                    c_max = new.max_slots, code = new.code, num = new.num, c_type = new.c_type,
                    section = new.section, instructor = new.instructor
                    ))
                #pprint.pprint(new.to_dict())
                if new not in queued_sql_entries:
                    queued_sql_entries.append(new)
                    
                self._last_course_data.append(new)
            else:
                i = self._last_course_data.index(new)
                old = self._last_course_data[i]
                self._last_course_data[i] = new
                
                changes = scrape_websoc.dict_changes(old.__dict__, new.__dict__)

                if changes:
                    info = self.parse_change(changes, old, new)
                    logging.info(info)
                    
                    affects = [user for user in self._users if new.code in user.get_courses()]
                    
                    notification_set.add((frozenset(affects), info))
                    
                    if new not in queued_sql_entries:
                        queued_sql_entries.append(new)


        if notification_set:
            self.notify_set(notification_set)
            
        if queued_sql_entries:
            self.write_sqlite(queued_sql_entries)
    
    def loop(self) -> None:
        try:
            self.refresh()
        except Exception as e:
            logging.error('\t'+str(traceback.format_exc()))

    def main(self) -> None:
        while True:
            self.loop()
            time.sleep(15)

    def __del__(self):
        print('del!')
