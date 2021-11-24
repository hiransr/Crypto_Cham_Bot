import psycopg2
import confi
#connect
conn = psycopg2.connect(
    host="ec2-3-231-112-124.compute-1.amazonaws.com",
    database="d6ufld22v8kd0p",
    user="xdlrmbvicmvqzl",
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
  val = (data,cid)# converting into tuple for sql injection
  print(sql,cid,cname,data,table)
  cur.execute(sql, val)
  conn.commit()
#Verify the data
def checkdata(data, field,table):
  uval = (data,) #to convert it into tuple becoz one data is not considered as tuple
  sql = f"select * from {table} where {field}=%s" #%s=data
  cur.execute(sql,uval) 
  data = cur.fetchall()
  if(len(data) == 0):
    return 0
  return 1
# display field if already exist
def getfield(data,field,table):
  sql=f"select {field} from {table} where chatid={data}"
  cur.execute(sql)
  data = cur.fetchall()
  return data[0][0]
def gettotp(data):
  sql=f"select totp from signup where username='{data}'"
  cur.execute(sql)
  data = cur.fetchall()
  return data[0][0]
def deleterow(row,data,table):
  sql=f"delete from {table} where {row}=(%s)"
  val=(data,)
  cur.execute(sql,val)
  conn.commit()
def ShowMore(cid,pgno,cname):
  val =(cid,pgno,cname)
  sql=f"INSERT INTO showmore VALUES (%s,%s,%s)"
  cur.execute(sql,val)
  conn.commit()
def getfav(data):
  sql=f"select coinlist from fav where username='{data}'"
  cur.execute(sql)
  data = cur.fetchall()
  return data[0][0]
def updatefav(coinlist,username):
  sql = f"UPDATE fav SET coinlist=(%s) where username=(%s);" #%s=data,%s=cid
  val = (coinlist,username)# converting into tuple for sql injection
  cur.execute(sql, val)
  conn.commit()