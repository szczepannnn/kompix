import mysql.connector


def connection():
    conn = mysql.connector.connect(host="localhost", user='admin', password="admin", database='kompix')
    c = conn.cursor(buffered=True)

    return c, conn
