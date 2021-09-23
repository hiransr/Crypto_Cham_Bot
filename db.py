import psycopg2
import confi
#connect
conn = psycopg2.connect(
    host="localhost",
    database="postgres",
    user="postgres",
    password=confi.dbpass)
cur = conn.cursor()
#insert new row
def insertdata(data, field, table):
  sql = f"INSERT INTO {table} ({field}) VALUES (%s)"
  val = (data,)
  cur.execute(sql, val)
  conn.commit()
#update the same row
def updatedata(cid, cname, data, table):
  sql = f"UPDATE {table} SET {cname}=(%s) where chatid=(%s);" #%s=data,%s=cid
  val = (data, cid)# converting into tuple for sql injection
  cur.execute(sql, val)
  conn.commit()
#Verify the data
def checkdata(data, field):
  uval = (data,) #to convert it into tuple becoz one data is not considered as tuple
  sql = f"select * from signup where {field}=%s" #%s=data
  cur.execute(sql, uval) 
  data = cur.fetchall()
  if(len(data) == 0):
    return 0
  return 1
# display field if already exist
def getfield(data,field):
  sql=f"select {field} from signup where chatid={data}"
  cur.execute(sql)
  data = cur.fetchall()
  return data[0][0]