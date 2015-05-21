from websoc_app import *
from Course import FIELDNAMES
FIELDNAMES = ['ts'] + FIELDNAMES
import tornado.ioloop
import tornado.web
import tornado.concurrent
import sqlite3
import json
import time
    
    
def _execute(query):
    """Function to execute queries against a local sqlite database"""
    dbPath = SQLITE_DIRECTORY + WEBSOC_TERM + '.db'
    connection = sqlite3.connect(dbPath)
    cursorobj = connection.cursor()
    try:
            cursorobj.execute(query)
            result = cursorobj.fetchall()
            connection.commit()
    except Exception:
            raise
    connection.close()
    return result
        
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/db", DBListHandler)        ]
        super(Application, self).__init__(handlers, debug=True)
        
        
        
        self.soc_runner = App()


class DBListHandler(tornado.web.RequestHandler):    
    def get(self):
        rows = _execute('SELECT name FROM sqlite_master WHERE type = "table"')
        data = []
        for row in rows:
            data.append(_execute("SELECT * FROM '{}'".format(row[0])))
        loader = tornado.template.Loader('templates')
        result = loader.load('db.html').generate(table_headers=FIELDNAMES, data=data)
        self.write(result)


if __name__ == "__main__":
    app = Application()
    app.listen(5000)
    ioloop = tornado.ioloop.IOLoop.instance()
    def refresh():
        app.soc_runner.loop()
        ioloop.call_later(15, refresh)
    ioloop.spawn_callback(refresh)
    ioloop.start()
