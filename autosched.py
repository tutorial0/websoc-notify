import redis
import pickle
import schedule
from scrape_websoc import parse_sections
import datetime
from schedule import permute_schedules
import itertools
from collections import defaultdict



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
    gen('EECS 31L', 'I&C Sci 45C', 'Chinese 1A', 'I&C Sci 6B', 'Math 3D')
    import tornado.web
    class DataHandler(tornado.web.RequestHandler):
        def set_default_headers(self):
            self.set_header("Access-Control-Allow-Origin", "*")
        date_mapping = {'M': 0, 'Tu': 1, 'W': 2, 'Th': 3, 'F': 4}

        def get(self):
            r = redis.StrictRedis()
            d = defaultdict(dict)
            d['metadata'] = dict()
            course_data = {}
            for c in ['EECS 31L', 'I&C Sci 45C', 'Chinese 1A', 'I&C Sci 6B', 'Math 3D']:
                course_data[c] = pickle.loads(r.get(c))
            course_data = parse_sections(course_data)

            today = datetime.date.today()
            monday = today - datetime.timedelta(days=today.weekday())

            for i, x in enumerate(permute_schedules(course_data), 1):
                d[i]['cal_events'] = []
                course_ids = set()
                for c in itertools.filterfalse(lambda x: x is None, itertools.chain.from_iterable(x)):
                    h,s,v = ((hash(c)**4)%2047)/1000,.7,243.2-25
                    rgb = hsv_to_rgb(h, s, v)
                    rand_color = '#'+str(hex(int(rgb[0])))[2:] + str(hex(int(rgb[1])))[2:] + str(hex(int(rgb[2])))[2:]
                    for days, time in c.time.times.items():
                        for day in days:
                            tdelta = datetime.timedelta(days=self.date_mapping[day])
                            d[i]['cal_events'].append({'title': '{} - {} {} ({})'.format(c.num,c.c_type,c.section,c.code),
                                         'start':datetime.datetime.combine(monday+tdelta, time['start']).isoformat(),
                                         'end':datetime.datetime.combine(monday+tdelta, time['end']).isoformat(),
                                         'color':rand_color})
                            course_ids.add(c.code)
                            d['metadata'][c.code] = c.to_json()
                d[i]['course_ids'] = list(sorted(course_ids))
            self.write(d)

    class Application(tornado.web.Application):
        def __init__(self):
            handlers = [
                (r"/auto_data", DataHandler),
            ]
            super(Application, self).__init__(handlers, debug=True)
    app = Application()
    app.listen(8088)
    tornado.ioloop.IOLoop.current().start()
