#    Sample main.py Tornado file
#    (for Tornado on Heroku)
#
#    Author: Mike Dory | dory.me
#    Created: 11.12.11 | Updated: 06.02.13
#    Contributions by Tedb0t, gregory80
#
# ------------------------------------------

#!/usr/bin/env python
import os.path
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import urlparse
import psycopg2
import psycopg2.extras

# import and define tornado-y things
from tornado.options import define
define("port", default=5000, help="run on the given port", type=int)


# application settings and handle mapping info
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
			(r"/test", TestHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
        )
        urlparse.uses_netloc.append("postgres")
        url = urlparse.urlparse(os.environ.get("DATABASE_URL",'postgresql://haruka@localhost/wm'))
        self.conn = psycopg2.connect(
            database=url.path[1:],
    	    user=url.username,
    		password=url.password,
    		host=url.hostname,
    		port=url.port
    	)
        tornado.web.Application.__init__(self, handlers, **settings)


# the main page
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render(
            "main.html",
        )


# the test page
class TestHandler(tornado.web.RequestHandler):
    def get(self):
        cur = self.application.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from users")
        rows = cur.fetchall()
        self.render(
            "test.html",
            rows=rows
        )

# RAMMING SPEEEEEEED!
def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(tornado.options.options.port)

    # start it up
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
