import cx_Oracle                                                #引用模块cx_Oracle
import pymssql
conn_ms=pymssql.connect(host='127.0.0.1',user='sa',password='saftop',port='1433',database='171219')
ms=conn_ms.cursor()
ms.execute('select top(1)* from acscon_alarmactive')
for row in ms:
    print(row)
ms.close()
conn_ms.close()

conn_orcl=cx_Oracle.connect('ykt','yktpass','127.0.0.1:1521/orcl')    #连接数据库
print("连接oracle成功")
c=conn_orcl.cursor()                                                 #获取cursor
c.execute('select username from SYCOMK.D_USER_ALL')                         #使用cursor进行各种操作
a=list()
for row in c:
    a.append(list(row));
    print(row)
c.execute("select username from SYCOMK.D_USER_ALL where username='田思'") 
b=list()
for row in c:
    b=list(row);
print(b)
for _ in a:
    if b == _:
        print(True)
print(a)
c.close()                                                       #关闭cursor
conn_orcl.close()                                                    #关闭连接
