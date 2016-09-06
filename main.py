# -*- coding: utf-8 -*-

from tornado.options import define, options
from datetime import datetime
import logging
import psycopg2
import urlparse2 as urlparse
#import db
import os.path
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import urlparse
import psycopg2
import psycopg2.extras



define("port", default=5000, type=int)
define("username", default="user")
define("password", default="pass")



class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r'/', MainHandler),
            (r'/auth/login', AuthLoginHandler),
            (r'/auth/logout', AuthLogoutHandler),
            (r'/home',HomeHandler),
            (r'/form',FormHandler),

        ]
        settings = dict(
            cookie_secret='gaofjawpoer940r34823842398429afadfi4iias',
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            login_url="/auth/login",
            xsrf_cookies=True,
            autoescape="xhtml_escape",
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


class BaseHandler(tornado.web.RequestHandler):

    cookie_username = "username"

    def get_current_user(self):
        username = self.get_secure_cookie(self.cookie_username)
        logging.debug('BaseHandler - username: %s' % username)
        if not username: return None
        return tornado.escape.utf8(username)

    def set_current_user(self, username):
        self.set_secure_cookie(self.cookie_username, tornado.escape.utf8(username))

    def clear_current_user(self):
        self.clear_cookie(self.cookie_username)


class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.write("Hello, <b>" + self.get_current_user() + "</b> <br> <a href=/auth/logout>Logout</a>")


class AuthLoginHandler(BaseHandler):
    def get(self):
        self.render("login.html")

    def post(self):
        logging.debug("xsrf_cookie:" + self.get_argument("_xsrf", None))

        self.check_xsrf_cookie()

        username = self.get_argument("username")  #emailアドレス
        password = self.get_argument("password")
       
        conn = self.application.conn 
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from users where mail = '%s'" % username)
        rows = cur.fetchall()
        print(rows[0])

        if rows[0] != None:
          if password == rows[0][1]:
            self.set_current_user(username)
            self.redirect("/")
        else:
            self.write_error(403)


class AuthLogoutHandler(BaseHandler):

    def get(self):
        self.clear_current_user()
        self.redirect('/')



#######################################################################

class HomeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        c_user = self.get_current_user()
        conn = self.application.conn 
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from users where mail = '%s'" % c_user)
        rows = cur.fetchall()
        print(rows[0])
        my_data = rows[0]       ##### (1)
        cur.execute("select * from messages where reader_id = '%s'" % c_user)
        msg_data = cur.fetchall()       ##### (2)

        self.render("home.html",
                    u_data = my_data,
                    messages = msg_data
                    )

class FormHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        c_user = self.get_current_user()
        conn = self.application.conn 
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from users where mail = '%s'" % c_user)
        rows = cur.fetchall()
        school = rows[0][3]
        cur.execute("select * from users where school = '%s'" % school)
        members = cur.fetchall()

        self.render("form.html",
                    users_name = members
                    )

    def post(self):
        m_writer = self.get_current_user()
        m_reader = self.get_argument("reader")
        m_title = self.get_argument("title")
        m_text = self.get_argument("text")
        m_date = str(datetime.now())
        logging.debug("\n" + m_writer + "\n" + m_reader + "\n" + m_title + "\n" + m_text + "\n" + m_date)
        
        conn = self.application.conn
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        sql = """insert into messages values('%s','%s','%s','%s','%s');"""
        cur.execute(sql % (m_writer, m_reader, m_title, m_text, m_date))
        conn.commit()
        logging.debug("INSERT END!!")
        self.redirect('/form')


#######################################################################


def main():
    tornado.options.parse_config_file(os.path.join(os.path.dirname(__file__), 'server.conf'))
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    logging.debug('run on port %d in %s mode' % (options.port, options.logging))
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()


