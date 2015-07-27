import redis
import pickle
import schedule
from scrape_websoc import parse_sections
from datetime import datetime
from schedule import permute_schedules
import itertools

def gen(*classes):
    r = redis.StrictRedis()
    course_data = {}
    for c in classes:
        course_data[c] = pickle.loads(r.get(c))
    course_data = parse_sections(course_data)
    start = datetime.now()
    for i, x in enumerate(permute_schedules(course_data)):
        print(['{} {} {} ({})'.format(y.num, y.c_type, y.section, y.code) for y in itertools.chain.from_iterable(x)])
    end = datetime.now()
    print('generated {} schedules in {}s'.format(i, (end-start).total_seconds()))


gen('CSE 31L', 'I&C Sci 45C', 'Chinese 1A', 'I&C Sci 6B', 'Math 3D')