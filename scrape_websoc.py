from libs import bs4
from bs4 import BeautifulSoup
import urllib.request
from Course import *
from config import *
from collections import defaultdict
import re

def dict_changes(past_dict, current_dict):
    current_keys, past_keys = [
            set(d.keys()) for d in (current_dict, past_dict)
            ]
    intersect = current_keys.intersection(past_keys)

    return set(o for o in intersect if past_dict[o] != current_dict[o])

def make_websoc_request(values: dict) -> urllib.request.Request:
    ## TODO:
    ## check to make sure its actually websoc before trying to scrape
    url = 'http://websoc.reg.uci.edu/perl/WebSoc'
    data = urllib.parse.urlencode(values)
    data = data.encode('utf-8')
    req = urllib.request.Request(url, data)
    return req

def query_websoc(course_codes: [int]) -> [Course]:
    classes = []
    for course_codes in [course_codes[i:i+6] for i in range(0,len(course_codes),6)]:
        str_course_codes = ','.join([str(x) for x in course_codes])
        values = {'Submit' : 'Display Web Results',
          'YearTerm' : WEBSOC_TERM,
          'ShowComments' : 'on',
          'ShowFinals' : 'on',
          'CourseCodes' : str_course_codes,
        }
        req = make_websoc_request(values)

        with urllib.request.urlopen(req) as response:
            the_page = response.read()
            soup = BeautifulSoup(the_page)
    
            lines = soup.find_all('td', text=course_codes)
            for line in lines:
                classes.append(Course(line))

    return classes

def get_department(dept: str) -> {str: [Course]}:
    d = defaultdict(list)
    values = {'Submit' : 'Display Web Results',
          'YearTerm' : WEBSOC_TERM,
          'ShowComments' : 'on',
          'ShowFinals' : 'on',
          'Dept' : dept,
    }
    req = make_websoc_request(values)
    with urllib.request.urlopen(req) as response:
        the_page = response.read()
        soup = BeautifulSoup(the_page)

        courses = soup.find_all('td', class_="CourseTitle")
        for course in courses:
            parent = course.parent
            c = strip_soup(course.contents[0])
            for s in parent.find_next_siblings('tr'):
                if (s.has_attr('class') and s['class'] == ['blue-bar']):
                    break
                elif s.find('th') == None and s.find('table') == None:
                    new_c = Course(s.td)
                    for i in d[c]:
                        if new_c.section == i.section:
                            return d
                    d[c].append(new_c)
    return d

def parse_sections(courses: {str: [Course]}) -> {str: {Course: [Course]}}:
    '''
                    Lecture        Corresponding discussions
    'Course Num': { <Course Obj>: [<Course Obj>, <Course Obj>, ...] }
    '''
    o = dict()
    for num,c in courses.items():
        i = iter(c)
        p = next(i)                         # points at current lecture
        d = defaultdict(list)
        p_set = set()
        l_set = set()

        d[p]
        p_set.add(p)
        for course in i:
            if course.c_type == "Lab":      # special case for CS labs
                l_set.add(course)
            elif p.c_type == course.c_type: # is a new lecture
                p = course                  # change pointer
                p_set.add(p)                # for CS labs
                d[p]                        # init in dictionary
            else:                           # otherwise discussion
                d[p].append(course)

        for p in p_set:
            for l in l_set:
                d[p].append(l)
        o[num] = d
    return o


if __name__ == '__main__':
    courses = get_department('CSE')
    d = parse_sections(courses)

    for k,v in sorted(d.items()):
        print(k)
        for i,c_list in sorted(v.items(), key=lambda x:x[0].code):
            print('  ', i.code, i.c_type, i.section)
            for c in sorted(c_list, key=lambda x:x.code):
                print('      ', c.code, c.c_type, c.section)

