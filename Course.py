from libs import bs4
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta, time

FIELDNAMES = ['code', 'name', 'num', 'c_type', 'section', 'instructor',
              'time', 'room', 'final', 'max_slots', 'enrolled', 'waitlisted', 'status']

DAYS = {'Monday':'M', 'Tuesday':'Tu', 'Wednesday':'W', 'Thursday':'Th', 'Friday':'F'}

class CourseTime:
    def __init__(self, timestring):
        self.string = timestring
        if 'TBA' in timestring:
            return
        self.times = dict()

        for ts in timestring:
            days, s_time = strip_soup(ts).split()

            day_set = set()
            start, end = [datetime.strptime(t, '%I:%M').time() for t in s_time.strip('p').split('-')]

            if s_time[-1] == 'p':
                end = end.replace(hour=end.hour+12)
                # TODO: ugly
                if start < time(hour=10) or start == time():
                    start = start.replace(hour=start.hour+12)

            for d in DAYS.values():
                if d in days:
                    day_set.add(d)

            self.times[tuple(day_set)] = {'start': start, 'end': end }

    def conflicts_with(self, other) -> bool:
        if 'TBA' in self.string or 'TBA' in other.string:
            return True
        for day1,time1 in self.times.items():
            for day2,time2 in other.times.items():
                if time1['start'] < time2['end'] and time2['start'] < time1['end'] and set(day1).intersection(set(day2)):
                    return True
        return False

    def __repr__(self):
        return 'CourseTime({})'.format(self.string)

    def __str__(self):
        return self.string

class Course:
    def __init__(self, soup: bs4.element.Tag=None):
        for name in FIELDNAMES:
            self.__dict__[name] = None

        if type(soup).__name__ == 'Tag':
            self._parse(soup)
            

    def _parse(self, in_soup: bs4.element.Tag):
        '''
        format of expected input:
                         [
        0  course code     <td bgcolor="#D5E5FF" nowrap="nowrap">16000</td>,
        1  type            <td nowrap="nowrap">Lec</td>,
        2  section         <td bgcolor="#D5E5FF" nowrap="nowrap">A</td>,
        3  units           <td nowrap="nowrap">4</td>,
        4  instructor      <td bgcolor="#D5E5FF" nowrap="nowrap">DANG, Q.</td>,
        5  time            <td nowrap="nowrap">MWF    3:00- 3:50p</td>,
        6  room            <td bgcolor="#D5E5FF" nowrap="nowrap"><a href="http://www.classrooms.uci.edu/GAC/DBH1100.html" target="_blank">DBH 1100</a></td>,
        7  final           <td nowrap="nowrap">Mon, Jun 8, 4:00-6:00pm</td>,
        8  max_slots       <td align="right" bgcolor="#D5E5FF" nowrap="nowrap">200</td>,
        9  enrolled        <td align="right" nowrap="nowrap">38 / 107</td>,
        10 waitlist        <td align="right" bgcolor="#D5E5FF" nowrap="nowrap">n/a</td>,
        11 requested       <td align="right" nowrap="nowrap">44</td>,
        12 nor             <td align="right" bgcolor="#D5E5FF" nowrap="nowrap">0</td>,
        13 restrictions    <td nowrap="nowrap">A and N</td>,
        14 bookstore_link  <td bgcolor="#D5E5FF" nowrap="nowrap"><a href="http://book.uci.edu/ePOS?this_category=76&amp;store=446&amp;form=shared3/gm/main.html&amp;design=446" target="_blank">Bookstore</a></td>,
        15 web_link        <td nowrap="nowrap"> </td>,
        16 status          <td bgcolor="#D5E5FF" nowrap="nowrap"><b><font color="green">OPEN</font></b></td>
                          ]
        '''
        soup = in_soup.parent.contents
        print(soup)
        self.code = int(_str(soup[0]))
        self.c_type = _str(soup[1])
        self.section = _str(soup[2])
        instructor = []
        for s in soup[4]:
            if s.string != None:
                instructor.append(_str(s))
        self.instructor = '/'.join(instructor)
        self.time = CourseTime(list(soup[5].stripped_strings))
        self.room = _str(soup[6])
        self.final = strip_soup(_str(soup[7]))
        self.max_slots = int(_str(soup[8]))
        self.enrolled = int(_str(soup[9]).split('/')[-1].strip())
        self.waitlisted = int(_str(soup[10])) if _str(soup[10]) != 'n/a' and 'off' not in _str(soup[10]) else None
        self.status = _str(soup[16])

        self.num, self.name = self._get_name_and_num(in_soup)

    def _get_name_and_num(self, soup: bs4.element.Tag) -> str:
        for element in soup.previous_elements:
            if type(element).__name__ == 'Tag':
                get_color = element.get('bgcolor')
                td = element.td
                if get_color == '#fff0ff' and type(td.get('class')) == list and 'CourseTitle' in td.get('class'):
                    num = strip_soup(_str(td.contents[0]))
                    name = strip_soup(_str(td.contents[1]))
                    return (num, name)

    def conflicts_with(self, other):
        if other is None: return False
        return self.time.conflicts_with(other.time)

    def to_dict(self) -> dict:
        return self.__dict__

    def __eq__(self, c) -> bool:
        return self.code == c.code
    
    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        c = self.code
        other = other.code if type(other) != int else other
        if c < other:
            return -1
        if c == other:
            return 0
        else:
            return 1
 
    def __str__(self) -> str:
        return str(self.to_dict())
    
    def __hash__(self):
        return hash(self.code)
    
    
def _str(soup):
    return str(soup.string)

spaces = re.compile(r' {2,}')
def strip_soup(s: str) -> str:
    return spaces.sub(' ', s.replace('\xa0', '').strip()).replace('- ', '-')

def course_from_data(code, num, name, c_type, section, instructor,
                     time, room, max_slots, enrolled, status) -> Course:
    self = Course('')
    self.code = code
    self.num = num
    self.name = name
    self.c_type = c_type
    self.section = section
    self.instructor = instructor
    self.time = time
    self.room = room
    self.max_slots = max_slots
    self.enrolled = enrolled
    self.status = status

    return self
