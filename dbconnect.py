import mysql.connector

def connection():
    conn = mysql.connector.connect(host="localhost",
                           user="admin",
                           password="admin",
                           db="kompix")
    c = conn.cursor()

    return c, conn