import vendor
vendor.add('libs')

import redis
import pickle
import schedule
from scrape_websoc import parse_sections
import datetime
from schedule import permute_schedules
import itertools
from collections import defaultdict
import urllib.parse
import re

import random

def random_color():
    # hex(52) -> "0x34", so [2:] is the two hex digits, without the 0x prefix
    return "#"+str(hex(random.randint(20,255)))[2:]+str(hex(random.randint(20,255)))[2:]+str(hex(random.randint(20,255)))[2:]

def hsv_to_rgb(h, s, v):
    if s == 0.0: return [v, v, v]
    i = int(h*6.) # XXX assume int() truncates!
    f = (h*6.)-i; p,q,t = v*(1.-s), v*(1.-s*f), v*(1.-s*(1.-f)); i%=6
    if i == 0: return [v, t, p]
    if i == 1: return [q, v, p]
    if i == 2: return [p, v, t]
    if i == 3: return [p, q, v]
    if i == 4: return [t, p, v]
    if i == 5: return [v, p, q]

def sorted_nicely(l):
    """ Sorts the given iterable in the way that is expected.

    Required arguments:
    l -- The iterable to be sorted.

    """
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key.decode())]
    return sorted(l, key = alphanum_key)

def gen(*classes):
    r = redis.StrictRedis()
    course_data = {}
    for c in classes:
        course_data[c] = pickle.loads(r.get(c))
    course_data = parse_sections(course_data)
    start = datetime.datetime.now()
    for i, x in enumerate(permute_schedules(course_data), 1):
        print(['{} {} {} ({})'.format(y.num, y.c_type, y.section, y.code) for y in itertools.chain.from_iterable(x) if y])
    end = datetime.datetime.now()
    print('generated {} schedules in {}s'.format(i, (end-start).total_seconds()))

if __name__ == "__main__":
#     gen('EECS 31L', 'I&C Sci 45C', 'Chinese 1A', 'I&C Sci 6B', 'Math 3D')
    import tornado.web

    class AutoPageHandler(tornado.web.RequestHandler):
        def get(self, courses=None, course_codes=None):
            if courses:
                self.render('auto.html', courses=courses, course_codes=course_codes)
            else:
                self.render('auto-main.html')

        def post(self):
            courses = self.get_argument('courses')
            course_codes = self.get_argument('course_codes')
            self.render('auto.html', courses=courses, course_codes=course_codes)

    class CourseInfoHandler(tornado.web.RequestHandler):
        def get(self, course):
            # '''
            # returns data in the following JSON structure:
            # {
            #     'response': {
            #         "0": {
            #             "lec": {course_data},
            #             "dis": [{course_data}, ...]
            #         }
            #     }
            # }
            # '''
            # r = redis.StrictRedis()
            # self.set_header('Content-Type', 'application/javascript')
            # obj = pickle.loads(r.get(course))
            # obj = parse_sections({course: obj})
            # d = {}
            # for i,(k,v) in enumerate(obj[course].items()):
            #     d[i] = {"lec": k.to_json(), "dis": [x.to_json() for x in v]}
            # self.write({'response': d })
            r = redis.StrictRedis()
            self.set_header('Content-Type', 'application/javascript')
            obj = pickle.loads(r.get(course))
            parsed = parse_sections({course: obj})[course]
            mappings = defaultdict(list)
            for k,v in parsed.items():
                for item in v:
                    mappings[item.code].append(k.code)
            self.write({'response': [x.to_json() for x in obj], 'mappings': mappings})

    class DeptInfoHandler(tornado.web.RequestHandler):
        def get(self, subject=None):
            r = redis.StrictRedis()
            self.set_header('Content-Type', 'application/javascript')
            obj = sorted_nicely(r.smembers(subject)) if subject else r.zrange('DEPARTMENTS', 0, -1)
            self.write({'response': [x.decode() for x in obj]})

    class DataHandler(tornado.web.RequestHandler):
        def set_default_headers(self):
            self.set_header("Access-Control-Allow-Origin", "*")

        date_mapping = {'M': 0, 'Tu': 1, 'W': 2, 'Th': 3, 'F': 4}
        # def get(self, courses, course_codes=set()):
        def post(self):
            courses = self.get_argument('courses')
            course_codes = self.get_argument('course_codes')
            courses = urllib.parse.unquote(courses).replace('&amp;','&').split(',')
            print(courses)
            course_codes = set(int(x) for x in urllib.parse.unquote(course_codes).replace('&amp;','&').split(','))

            r = redis.StrictRedis()
            d = defaultdict(dict)
            d['metadata'] = dict()
            course_data = {}
            for c in courses:
                course_data[c] = pickle.loads(r.get(c))
            course_data = parse_sections(course_data)

            today = datetime.date.today()
            monday = today - datetime.timedelta(days=today.weekday())

            for i, x in enumerate(permute_schedules(course_data, course_codes), 1):
                d[i]['cal_events'] = []
                course_ids = {}
                for c in itertools.filterfalse(lambda x: x is None or x.time.string == ['TBA'], itertools.chain.from_iterable(x)):
                    h,s,v = ((hash(c)**4)%2047)/1000,.7,243.2-25
                    rgb = hsv_to_rgb(h, s, v)
                    rand_color = '#'+str(hex(int(rgb[0])))[2:] + str(hex(int(rgb[1])))[2:] + str(hex(int(rgb[2])))[2:]

                    course_ids[c.code] = rand_color
                    for days, time in c.time.times.items():
                        for day in days:
                            tdelta = datetime.timedelta(days=self.date_mapping[day])
                            d[i]['cal_events'].append({'title': '{} - {} {} ({})'.format(c.num,c.c_type,c.section,c.code),
                                         'start':datetime.datetime.combine(monday+tdelta, time['start']).isoformat(),
                                         'end':datetime.datetime.combine(monday+tdelta, time['end']).isoformat(),
                                         'color':rand_color})
                            d['metadata'][c.code] = c.to_json()
                d[i]['course_ids'] = course_ids
            self.write(d)

        def calc_score(cal_events: []):
            pass


    class Application(tornado.web.Application):
        def __init__(self):
            handlers = [
                (r"/auto_data/", DataHandler),
                (r"/course_info/(.*)", CourseInfoHandler),
                (r"/dept_info(?:/(.*))?", DeptInfoHandler),
                (r"/auto/(.*?)(?:/(.*))+?", AutoPageHandler),
                (r"/auto", AutoPageHandler),
                (r"/assets/(.*)", tornado.web.StaticFileHandler, {'path': 'templates/assets/'})
            ]
            super(Application, self).__init__(handlers, debug=True, template_path='templates/')
    app = Application()
    app.listen(8088)
    tornado.ioloop.IOLoop.current().start()
