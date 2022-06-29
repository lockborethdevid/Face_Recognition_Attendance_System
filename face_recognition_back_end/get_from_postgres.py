import psycopg2

#Connect to postgreSQL
def get_connection():
    connection = psycopg2.connect(user="postgres", password="Keen_face_recognition", host="192.168.0.47", port="5433",
                                  database="postgres")
    return connection

#Cursor to bring data from Postgre to our program
def get_cursor(connection):
    cursor = connection.cursor()
    return cursor
def get_students(cursor):
    cursor.execute("""select * from students""")
    return cursor.fetchall()

def get_sessions(cursor):
    cursor.execute("""select * from sessions""")
    return cursor.fetchall()
def get_batchs(cursor):
    cursor.execute("""select * from batchs""")
    return cursor.fetchall()
def get_sections(cursor):
    cursor.execute("""select * from sections""")
    return cursor.fetchall()
