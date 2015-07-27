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




def gen(*classes):
    r = redis.StrictRedis()
    course_data = {}
    for c in classes:
        course_data[c] = pickle.loads(r.get(c))
    course_data = parse_sections(course_data)
    start = datetime.datetime.now()
    for i, x in enumerate(permute_schedules(course_data)):
        print(['{} {} {} ({})'.format(y.num, y.c_type, y.section, y.code) for y in itertools.chain.from_iterable(x) if y])
    end = datetime.datetime.now()
    print('generated {} schedules in {}s'.format(i, (end-start).total_seconds()))

if __name__ == "__main__":
    import tornado.web
    class DataHandler(tornado.web.RequestHandler):
        def set_default_headers(self):
            self.set_header("Access-Control-Allow-Origin", "*")
        date_mapping = {'M': 0, 'Tu': 1, 'W': 2, 'Th': 3, 'F': 4}

        def get(self):
            r = redis.StrictRedis()
            d = defaultdict(list)
            course_data = {}
            for c in ['EECS 31L', 'I&C Sci 45C', 'Chinese 1A', 'I&C Sci 6B', 'Math 3D']:
                course_data[c] = pickle.loads(r.get(c))
            course_data = parse_sections(course_data)

            today = datetime.date.today()
            monday = today - datetime.timedelta(days=today.weekday())

            for i, x in enumerate(permute_schedules(course_data), 1):
                for c in itertools.filterfalse(lambda x: x is None, itertools.chain.from_iterable(x)):
                    rand_color = random_color()
                    for days, time in c.time.times.items():
                        for day in days:
                            tdelta = datetime.timedelta(days=self.date_mapping[day])
                            d[i].append({'title': '{} - {} {} ({})'.format(c.num,c.c_type,c.section,c.code),
                                         'start':datetime.datetime.combine(monday+tdelta, time['start']).isoformat(),
                                         'end':datetime.datetime.combine(monday+tdelta, time['end']).isoformat(),
                                         'color':rand_color})
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
# gen('EECS 31L', 'I&C Sci 45C', 'Chinese 1A', 'I&C Sci 6B', 'Math 3D')