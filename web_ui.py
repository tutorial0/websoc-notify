from websoc_app import *
from Course import FIELDNAMES
FIELDNAMES = ['last_updated'] + FIELDNAMES
import tornado.ioloop
import tornado.web
import tornado.concurrent
import tornado.httpclient
import sqlite3
import json
import time
    
    
def _execute(query):
    """Function to execute queries against a local sqlite database"""
    dbPath = SQLITE_DIRECTORY + WEBSOC_TERM + '.db'
    connection = sqlite3.connect(dbPath)
    connection.row_factory = sqlite3.Row
    cursorobj = connection.cursor()
    try:
            cursorobj.execute(query)
            result = cursorobj.fetchall()
            connection.commit()
    except Exception:
            raise
    connection.close()
    return result


def load_page(handler, users):
    data = []
    for user in users:
        data.append([user.get_name(), [_execute("SELECT * FROM '{}' ORDER BY last_updated DESC LIMIT 1;".format(x)) for x in user.get_courses()]])

    loader = tornado.template.Loader('templates')
    result = loader.load('main.html').generate(table_headers=FIELDNAMES, data=data)
    handler.write(result)
    
 
class Application(tornado.web.Application):
    def __init__(self):
        self.soc_runner = App()



        handlers = [
            (r"/db", DBListHandler),
            (r"/", MainPageHandler, dict(soc_runner=self.soc_runner)),
            (r"/ap/(.*)", AntplannerFetchHandler, dict(soc_runner=self.soc_runner))
            ]
        super(Application, self).__init__(handlers, debug=True)


class DBListHandler(tornado.web.RequestHandler):    
    def get(self):
        rows = _execute('SELECT name FROM sqlite_master WHERE type = "table"')
        data = []
        for row in rows:
            data.append(_execute("SELECT * FROM '{}'".format(row[0])))
        loader = tornado.template.Loader('templates')
        result = loader.load('db.html').generate(table_headers=FIELDNAMES, data=data)
        self.write(result)

class AntplannerFetchHandler(tornado.web.RequestHandler):
    def initialize(self, soc_runner):
        self.soc_runner = soc_runner
        
        
    @tornado.gen.coroutine    
    def get(self, user):
        http = tornado.httpclient.AsyncHTTPClient()
        request = tornado.httpclient.HTTPRequest('http://antplanner.appspot.com/schedule/load?username=' + user, 'GET')
        response = yield tornado.gen.Task(http.fetch, request)
        response = json.loads(response.body.decode())
        if response['success']:
            course_codes = list(set(int(d['groupId']) for d in json.loads(response['data'])))
            if user in self.soc_runner._users:
                i = self.soc_runner._users.index(user)
                u = self.soc_runner._users[i]
                u.set_courses(course_codes)
            else:
                u = UserData('', user, course_codes)
                self.soc_runner._users.append(u)
            self.soc_runner.loop()
            load_page(self, [u])
        else:
            self.write('invalid user!')


class MainPageHandler(tornado.web.RequestHandler):
    def initialize(self, soc_runner):
        self.soc_runner = soc_runner
        
    def get(self):
        users = self.soc_runner._users
        load_page(self, users)


if __name__ == "__main__":
    app = Application()
    app.listen(5000)
    ioloop = tornado.ioloop.IOLoop.instance()
    def refresh():
        app.soc_runner.loop()
        ioloop.call_later(15, refresh)
    ioloop.spawn_callback(refresh)
    ioloop.start()
