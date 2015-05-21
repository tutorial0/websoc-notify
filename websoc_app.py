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

    def __repr__(self) -> str:
        return 'UserData(email={}, user={}, courses={})'.format(self._email, self._user, self._courses)

class App:
    def __init__(self):
        self._users = []
        self._last_course_data = []
        initialize_logger(str(Path(LOG_DIRECTORY)))

    def add_user(self, data: UserData) -> None:
        self._users.append(data)

    def get_new_course_data(self) -> [scrape_websoc.Course]:
        courses = []
        for user in self._users:
            user_courses = user.get_courses()
            results = scrape_websoc.query_websoc(user_courses)
            courses.extend(results)

        return courses

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
            try:
                pushbullet.send_push(email, '{}: websoc-notify'.format(name), info)
            except Exception as e:
                logging.error('Could not push!')
                logging.error('\t'+str(traceback.format_exc()))

    @staticmethod
    def write_sqlite(course):
        with sqlite_manager(WEBSOC_TERM) as s_manager:
            s_manager.add_row(course.__dict__)

    def refresh(self) -> None:
        now = datetime.now()
        logging.info('=============== {} ==============='.format(str(now)))
        new_data = self.get_new_course_data()

        for new in new_data:
            if new not in self._last_course_data:
                logging.info('Added {code} (max: {c_max}) ({num} {c_type} {section} -- {instructor})'.format(
                    c_max = new.max_slots, code = new.code, num = new.num, c_type = new.c_type,
                    section = new.section, instructor = new.instructor
                    ))
                #pprint.pprint(new.to_dict())
                self.write_sqlite(new)
            else:
                old = self._last_course_data[self._last_course_data.index(new)]
                changes = scrape_websoc.dict_changes(old.__dict__, new.__dict__)

                if changes:
                    info = self.parse_change(changes, old, new)
                    logging.info(info)
                    
                    affects = [user for user in self._users if new.code in user.get_courses()]
                    self.notify(affects, info)

                    self.write_sqlite(new)


        
        self._last_course_data = new_data
    
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
