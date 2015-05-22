from libs import bs4
from bs4 import BeautifulSoup
import urllib.request
from Course import *
from config import *

def dict_changes(past_dict, current_dict):
    current_keys, past_keys = [
            set(d.keys()) for d in (current_dict, past_dict)
            ]
    intersect = current_keys.intersection(past_keys)

    return set(o for o in intersect if past_dict[o] != current_dict[o])


def query_websoc(course_codes: [int]) -> [Course]:
    classes = []
    for course_codes in [course_codes[i:i+6] for i in range(0,len(course_codes),6)]:
        str_course_codes = ','.join([str(x) for x in course_codes])
        ## TODO:
        ## check to make sure its actually websoc before trying to scrape
        url = 'http://websoc.reg.uci.edu/perl/WebSoc'
        values = {'Submit' : 'Display Web Results',
                  'YearTerm' : WEBSOC_TERM,
                  'ShowComments' : 'on',
                  'ShowFinals' : 'on',
                  'CourseCodes' : str_course_codes,
                  }
        data = urllib.parse.urlencode(values)
        data = data.encode('utf-8')
        req = urllib.request.Request(url, data)
        with urllib.request.urlopen(req) as response:
            the_page = response.read()
            soup = BeautifulSoup(the_page)
    
            lines = soup.find_all('td', text=course_codes)
            for line in lines:
                classes.append(Course(line))

    return classes

