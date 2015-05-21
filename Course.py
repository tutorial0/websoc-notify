from libs import bs4
from bs4 import BeautifulSoup


FIELDNAMES = ['code', 'name', 'num', 'c_type', 'section', 'instructor',
              'time', 'room', 'max_slots', 'enrolled', 'waitlisted', 'status']

class Course:
    def __init__(self, soup: bs4.element.Tag):
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
        self.code = int(soup[0].string)
        self.c_type = soup[1].string
        self.section = soup[2].string
        instructor = []
        for s in soup[4]:
            if s.string != None:
                instructor.append(s.string)
        self.instructor = '/'.join(instructor)
        self.time = strip_soup(soup[5].string)
        self.room = soup[6].string
        self.max_slots = int(soup[8].string)
        self.enrolled = int(soup[9].string.split('/')[-1].strip())
        self.waitlisted = soup[10].string
        self.status = soup[16].string

        self.num, self.name = self._get_name_and_num(in_soup)

    def _get_name_and_num(self, soup: bs4.element.Tag) -> str:
        for element in soup.previous_elements:
            if type(element).__name__ == 'Tag':
                get_color = element.get('bgcolor')
                td = element.td
                if get_color == '#fff0ff' and type(td.get('class')) == list and 'CourseTitle' in td.get('class'):
                    num = strip_soup(td.contents[0].string)
                    name = strip_soup(td.contents[1].string)
                    return (num, name)

    def to_dict(self) -> dict:
        return self.__dict__

    def __eq__(self, c) -> bool:
        return self.code == c.code

    def __str__(self) -> str:
        return str(self.to_dict())

def strip_soup(s: str) -> str:
    return s.replace('\xa0', '').strip()

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
