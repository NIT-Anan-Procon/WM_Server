# -*- coding: utf-8 -*-

from tornado.options import define, options
from datetime import datetime
from datetime import timedelta
import logging
import psycopg2
import os.path
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import urlparse
import psycopg2
import psycopg2.extras
import random 


define("port", default=5000, type=int)
define("username", default="user")
define("password", default="pass")



class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r'/', MainHandler),
            (r'/auth/login', AuthLoginHandler),
            (r'/auth/logout', AuthLogoutHandler),
            (r'/auth/signup', SignUpHandler),
            (r'/home/([1-9]+)',HomeHandler),
            (r'/home',MainHandler),
            (r'/message/([1-9]+)',MessageHandler),
            (r'/practice/([1-9]+)',PracticeHandler),
            (r'/form',FormHandler),
            (r'/pracform',PracFormHandler),
            (r'/review',ReviewHandler),
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
        self.redirect("/auth/login")

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
        try:
          if rows[0] != None:
            if password == rows[0][1]:
              self.set_current_user(username)
              self.redirect("/home/1")
        except:
            self.redirect('/auth/login')


class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_current_user()
        self.redirect('/home/1')



#######################################################################

class HomeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self,page_number):
        admin = False
        c_user = self.get_current_user()
        conn = self.application.conn 
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from users where mail = '%s';" % c_user)
        rows = cur.fetchall()
        try:
          my_data = rows[0]       ##### (1)
        except:
          self.redirect('/auth/login')
        school = my_data[3]
        if my_data[4] == "admin":
          admin = True
        logging.debug(my_data[4])
        n = 6
        x = (int(page_number)-1) * n
        if admin:
          cur.execute("SELECT A1.writer_id,A1.reader_id,A1.title,A1.good,A1.advice,A1.parameter,A1.date,A1.name,users.name,users.school FROM (SELECT reviews.writer_id,reviews.reader_id,reviews.title,reviews.good,reviews.advice,reviews.parameter,reviews.date,users.name FROM reviews INNER JOIN users ON reviews.writer_id = users.mail)AS A1 INNER JOIN users ON A1.reader_id = users.mail where users.school = '%s' ORDER BY date DESC LIMIT %s OFFSET %s;" % (school, n, x))
          review_data = cur.fetchall()       ##### (2)
          cur.execute("SELECT A1.writer_id,A1.reader_id,A1.title,A1.good,A1.advice,A1.parameter,A1.date,A1.name,users.name,users.school FROM (SELECT reviews.writer_id,reviews.reader_id,reviews.title,reviews.good,reviews.advice,reviews.parameter,reviews.date,users.name FROM reviews INNER JOIN users ON reviews.writer_id = users.mail)AS A1 INNER JOIN users ON A1.reader_id = users.mail where users.school = '%s';" % school)
          page_amount = len(cur.fetchall()) / n + 1
        else:
          cur.execute("SELECT A1.writer_id,A1.reader_id,A1.title,A1.good,A1.advice,A1.parameter,A1.date,A1.name,users.name,users.school FROM (SELECT reviews.writer_id,reviews.reader_id,reviews.title,reviews.good,reviews.advice,reviews.parameter,reviews.date,users.name FROM reviews INNER JOIN users ON reviews.writer_id = users.mail)AS A1 INNER JOIN users ON A1.reader_id = users.mail where A1.reader_id = '%s' ORDER BY date DESC LIMIT %s OFFSET %s;" % (c_user, n, x))
          review_data = cur.fetchall()       ##### (2)
          cur.execute("SELECT A1.writer_id,A1.reader_id,A1.title,A1.good,A1.advice,A1.parameter,A1.date,A1.name,users.name,users.school FROM (SELECT reviews.writer_id,reviews.reader_id,reviews.title,reviews.good,reviews.advice,reviews.parameter,reviews.date,users.name FROM reviews INNER JOIN users ON reviews.writer_id = users.mail)AS A1 INNER JOIN users ON A1.reader_id = users.mail where A1.reader_id = '%s';" % c_user)
          page_amount = len(cur.fetchall()) / n + 1

        pic_src = "image/manager/" + str(my_data[6]) + ".png"
        param_result = ""
        if not admin:
          cur.execute("SELECT parameter FROM reviews where reader_id = '%s' ORDER BY date DESC LIMIT 30;"%c_user)
          param_data = cur.fetchall()
          if param_data:
            param_dict = {}
            for pd in param_data:
              tmp1 = pd[0].split(",")
              for t1 in tmp1:
                tmp2 = t1.split(":")
                if tmp2[0] in param_dict:
                  param_dict[tmp2[0]][0] = param_dict[tmp2[0]][0] + int(tmp2[1])
                  param_dict[tmp2[0]][1] = param_dict[tmp2[0]][1] + 1
                else:
                  param_dict[tmp2[0]] = [int(tmp2[1]),1]
            cur.execute("SELECT names FROM status WHERE school = '%s';"%school)
            param_names = cur.fetchall()[0][0].split(",")
            param_result = ""
            for pn in param_names:
              num = round(float(param_dict[pn][0]) / param_dict[pn][1],1)
              param_result = param_result + pn + ":" + str(num) + ","
            param_result = param_result[:-1]
            logging.debug(param_result)

        cur.execute("SELECT A1.advice FROM (SELECT * FROM reviews INNER JOIN users ON reviews.writer_id = users.mail WHERE reviews.reader_id = '%s')AS A1 WHERE A1.lank = 'admin' ORDER BY A1.date;"%c_user)
        rows = cur.fetchall()
        manager_advice = "頑張れ！！"
        if rows:
          if rows[0]:
            manager_advice = rows[0][0]
        logging.debug(manager_advice)
        self.render("home.html",
                    u_data = my_data,
                    reviews = review_data,
		                page_amount = page_amount,
		                current_page = int(page_number),
                    pic_src = pic_src,
                    admin = admin,
                    param = param_result,
                    advice = manager_advice
                    )

class MessageHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self,page_number):
        c_user = self.get_current_user()
        try:
          if self.get_current_user():
            logging.debug("Login now")
        except:
          self.redirect('/auth/login')
        conn = self.application.conn 
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from users where mail = '%s'" % c_user)
        rows = cur.fetchall()
        try:
          my_data = rows[0]       ##### (1)
        except:
          self.redirect('/auth/login')
        school = rows[0][3]
        cur.execute("select * from users where school = '%s' and not mail = '%s';" % (school,c_user))
        members = cur.fetchall()
        admin = False
        if my_data[4] == "admin":
          admin = True
        n = 6
        x = (int(page_number)-1) * n
        if admin:
          cur.execute("SELECT A1.writer_id,A1.reader_id,A1.title,A1.text,A1.date,A1.name,users.name,users.school FROM (SELECT messages.writer_id,messages.reader_id,messages.title,messages.text,messages.date,users.name FROM messages INNER JOIN users ON messages.writer_id = users.mail)AS A1 INNER JOIN users ON A1.reader_id = users.mail where users.school = '%s' ORDER BY date DESC LIMIT %s OFFSET %s;" % (school, n, x))
          rows = cur.fetchall()
          msg_data = []
          for r in rows:
            if r[0] != None:
              msg_data.append(r)
          cur.execute("SELECT A1.writer_id,A1.reader_id,A1.title,A1.text,A1.date,A1.name,users.name,users.school FROM (SELECT messages.writer_id,messages.reader_id,messages.title,messages.text,messages.date,users.name FROM messages INNER JOIN users ON messages.writer_id = users.mail)AS A1 INNER JOIN users ON A1.reader_id = users.mail where users.school = '%s';" % school)
          page_amount = len(cur.fetchall()) / n + 1
        else:
          cur.execute("SELECT A1.writer_id,A1.reader_id,A1.title,A1.text,A1.date,A1.name,users.name,users.school FROM (SELECT messages.writer_id,messages.reader_id,messages.title,messages.text,messages.date,users.name FROM messages INNER JOIN users ON messages.writer_id = users.mail)AS A1 INNER JOIN users ON A1.reader_id = users.mail where A1.reader_id = '%s' ORDER BY date DESC LIMIT %s OFFSET %s;" % (c_user, n, x))
          msg_data = cur.fetchall()
          cur.execute("SELECT * FROM messages where reader_id = '%s';" % c_user)
          page_amount = len(cur.fetchall()) / n + 1

        self.render("message.html",
                    users_name = members,
                    messages = msg_data,
                    page_amount = page_amount,
                    current_page = int(page_number),
                    u_data = my_data,
                    admin = admin
                    )

class FormHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        d = datetime.now()
        m_writer = self.get_current_user()
        m_reader = self.get_argument("reader")
        m_title = self.get_argument("title")
        m_text = self.get_argument("text")
        m_date = str(d + timedelta(hours=9))
        logging.debug("\n" + m_writer + "\n" + m_reader + "\n" + m_title + "\n" + m_text + "\n" + m_date)
        conn = self.application.conn
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        sql = """insert into messages values('%s','%s','%s','%s','%s');"""
        cur.execute(sql % (m_writer, m_reader, m_title, m_text, m_date))
        conn.commit()
        logging.debug("INSERT END!!")
        self.redirect('/message/1')


class PracticeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self,page_number):
        c_user = self.get_current_user()
        try:
          if c_user:
            logging.debug("Login now")
        except:
          self.redirect('/auth/login')
        conn = self.application.conn 
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from users where mail = '%s'" % c_user)
        rows = cur.fetchall()
        my_data = rows[0]       ##### (1)
        school = rows[0][3]
        n = 6
        x = (int(page_number)-1) * n
        cur.execute("SELECT * FROM practices INNER JOIN users ON practices.writer_id = users.mail where users.school = '%s' ORDER BY date DESC LIMIT %s OFFSET %s;" % (school, n, x))
        rows = cur.fetchall()
        prac_data = []
        for r in rows:
          if r[0] != None:
            prac_data.append(r)
        cur.execute("SELECT * FROM practices RIGHT JOIN users ON practices.writer_id = users.mail where users.school = '%s';" % school)
        page_amount = len(cur.fetchall()) / n + 1
        cur.execute("SELECT names FROM status WHERE school = '%s';"%school)
        param_names = cur.fetchall()[0][0].split(",")
        self.render("practice.html",
                    messages = prac_data,
                    page_amount = page_amount,
                    current_page = int(page_number),
                    u_data = my_data,
                    param_names = param_names
                    )


class PracFormHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        c_user = self.get_current_user()
        try:
          if c_user:
            logging.debug("Login now")
        except:
          self.redirect('/auth/login')
        conn = self.application.conn 
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from users where mail = '%s'" % c_user)
        rows = cur.fetchall()
        my_data = rows[0]       ##### (1)
        school = rows[0][3]
        d = datetime.now()
        m_writer = c_user
        m_title = self.get_argument("title")
        m_text = self.get_argument("text")
        m_date = str(d + timedelta(hours=9))
        logging.debug("\n" + m_writer + "\n" + m_title + "\n" + m_text + "\n" + m_date)
        conn = self.application.conn
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        sql = """insert into practices values('%s','%s','%s','%s');"""
        cur.execute(sql % (m_writer, m_title, m_text, m_date))
        conn.commit()
        logging.debug("INSERT END!!")
        self.redirect('/practice/1')



class ReviewHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        c_user = self.get_current_user()
        try:
          if c_user:
            logging.debug("Login now")
        except:
          self.redirect('/auth/login')
        conn = self.application.conn 
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from users where mail = '%s'" % c_user)
        rows = cur.fetchall()
        school = rows[0][3]
        cur.execute("select * from users where school = '%s' and not mail = '%s'" % (school,c_user))
        members = cur.fetchall()
        cur.execute("select names from status where school = '%s'" % school)
        param_names = cur.fetchall()[0][0].split(",")
        self.render("review.html",
                    users_name = members,
                    param_names = param_names
                    )

    def post(self):
        c_user = self.get_current_user()
        try:
          if c_user:
            logging.debug("Login now")
        except:
          self.redirect('/auth/login')
        d = datetime.now()
        r_writer = self.get_current_user().encode('utf-8')
        r_reader = self.get_argument("reader").encode('utf-8')
        r_title = self.get_argument("title").encode('utf-8')
        r_good = self.get_argument("good").encode('utf-8')
        r_advice = self.get_argument("advice").encode('utf-8')
        r_date = str(d + timedelta(hours=9)).encode('utf-8')
        param_len = int(self.get_argument("param_len"))
        r_parameter = ""
        for i in range(0,param_len):
          arg = "param_" + str(i)
          r_parameter = r_parameter + self.get_argument(arg) + ","
        r_parameter = r_parameter[:-1].encode('utf-8')
        print(type(r_parameter))

        logging.debug("\n" + r_writer + "\n" + r_reader + "\n" + r_title + "\n" + r_good + "\n" + r_advice + "\n" + r_parameter + "\n" + r_date)
        
        conn = self.application.conn
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        sql = """insert into reviews values('%s','%s','%s','%s','%s','%s','%s');"""
        cur.execute(sql % (r_writer, r_reader, r_title, r_good, r_advice, r_parameter, r_date))
        conn.commit()
        logging.debug("INSERT END!!")
        self.redirect('/review')



class SignUpHandler(BaseHandler):
    def get(self):
        self.render("sign_up.html",
                    )

    def post(self): 
        u_name = self.get_argument("name")
        u_mail = self.get_argument("mail")
        u_password = self.get_argument("password")
        u_school = self.get_argument("school")
        u_pos = self.get_argument("pos")
        u_manager = random.randint(0,5)

        conn = self.application.conn
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        sql = """insert into users values('%s','%s','%s','%s','%s','','%s',0);"""
        cur.execute(sql % (u_mail, u_password, u_name, u_school, u_pos, u_manager))
        conn.commit()
        
        cur.execute("select school from status where school = '%s';" % u_school)
        rows = cur.fetchall()
        logging.debug(rows)
        param_names = u"シュート,アシスト,パスカット,ディフェンス,スタミナ"
        if rows == []:
          cur.execute("INSERT INTO status VALUES('%s','%s');" % (u_school,param_names))
          conn.commit()
        logging.debug("INSERT END!!")
        self.redirect('/auth/login')


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


