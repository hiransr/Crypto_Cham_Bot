import psycopg2
import confi
conn = psycopg2.connect(
    host="localhost",
    database="postgres",
    user="postgres",
    password=confi.dbpass)
cur = conn.cursor()
def insertdata(data, field, table):
  sql = f"INSERT INTO {table} ({field}) VALUES (%s)"
  val = (data,)
  cur.execute(sql, val)
  conn.commit()
def updatedata(cid, cname, data, table):
  sql = f"UPDATE {table} SET {cname}=(%s) where chatid=(%s);"
  val = (data, cid)
  cur.execute(sql, val)
  conn.commit()