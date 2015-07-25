from Course import *
import itertools
from scrape_websoc import *

def permute_schedules(courses: {str: {Course: [Course]}}):
    d = []
    for x in courses.values():
        group = set()
        for lec, children in x.items():
            for c in children:
                group.add((lec,c))
            if not children:
                group.add((lec,lec))
        d.append(group)
    return exclude_duplicates(itertools.product(*d))

hm = 0
def exclude_duplicates(cs: iter):
    for i in cs:
        global hm
        hm += 1
        valid = True
#         print('==============================')
#         print([x.code for x in itertools.chain.from_iterable(i)])
#         print('------------------------------')
        for (a1,a2),(b1,b2) in itertools.combinations(i, 2):
#             print(a1.code,a2.code,b1.code,b2.code)
            if a1.conflicts_with(b1) or a1.conflicts_with(b2) or a2.conflicts_with(b1) or a2.conflicts_with(b2):
                valid = False
                break
        if valid:
            yield i

if __name__ == '__main__':
    courses = get_department('MATH')
    d = parse_sections(courses)
    sub = {k: d[k] for k in ('Math 2A', 'Math 2B', 'Math 2D', 'Math 2E')}

    i = 0
    start = datetime.now()
    for x in permute_schedules(sub):
        i += 1
        print(['{} {} {} ({})'.format(y.num, y.c_type, y.section, y.code) for y in itertools.chain.from_iterable(x)])
    end = datetime.now()
    print('generated {} schedules (discarded {} due to conflicts) in {}s'.format(i, hm-i, (end-start).total_seconds()))