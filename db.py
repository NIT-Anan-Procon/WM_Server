import psycopg2
import psycopg2.extras

def check_user(conn,mail):
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    select_sql = """SELECT * FROM users WHERE mail = '1111111@gmail.com';"""
    print("\n"+select_sql)
    print(c.execute(select_sql))

    conn.close()


def select_user(mail):
    conn = connect()
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    select_sql = """select * from users WHERE mail = '%s';"""
    return list(c.execute(select_sql,(mail)))[0]

    conn.close()


def msg_insrt(m_writer, m_reader, m_title, m_text, m_date):
    conn = connect()

    sql = """insert into messages values('%s','%s','%s','%s','%s');"""
    conn.execute(sql,(m_writer, m_reader, m_title, m_text, m_date))
    conn.commit()
    conn.close()


def usersBySchool(school):
    conn = connect()
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    select_sql = """select * from users WHERE school = '%s';"""
    return list(c.execute(select_sql,(school)))

    conn.close()

def getMessages(mail):
    conn = connect()
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    select_sql = """select * from messages WHERE reader_id = '%s';"""
    return list(c.execute(select_sql,(mail)))

    conn.close()


