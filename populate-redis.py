import redis
import schedule
from bs4 import BeautifulSoup
import urllib
import pickle


def get_all_departments():
    depts = []
    url = 'http://websoc.reg.uci.edu/perl/WebSoc'
    with urllib.request.urlopen(url) as response:
        page = response.read()
        soup = BeautifulSoup(page)
        dept_select = soup.find('select', attrs={'name':'Dept'})
        for dept in dept_select.find_all('option'):
            if dept.get('style') == None and dept['value'] != ' ALL': 
                depts.append(dept['value'])
    return depts

def populate_redis():
    depts = get_all_departments()
    r = redis.Redis(host='localhost', port=6379, db=0)
    for i, dept in enumerate(depts, 1):
        with r.pipeline() as pipe:
            print('----', dept)
            pipe.zadd('DEPARTMENTS', dept, i)
            data = schedule.get_department(dept)
            if data.keys(): # in case of no courses
                pipe.sadd(dept, *data.keys())
                for d,c in data.items():
                    pipe.set(d,pickle.dumps(c))
                    print('        ', c)
                pipe.execute()
    print('========\nDone!')

populate_redis()