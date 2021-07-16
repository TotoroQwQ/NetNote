import pymssql
import uuid
import math


dblink = {'host': '20.0.0.200', 'port': '1433',
          'database': '171219', 'user': 'sa', 'password': 'saftop'}

conn_db = None

stationid = ''


def delioevent(month):
    global conn_db
    cursor_db = conn_db.cursor()
    sql = (
        "select COUNT(*) from acscon_ioeventlog_m{0} a inner join acscon_realnode b on a.addr=b.addr where b.iotypeid='E7AB162E-4712-E411-976E-7427EA38CA2A' and eventno in (1,3)".format(month))
    # print(sql)
    cursor_db.execute(sql)
    count = cursor_db.fetchone()[0]
    if count > 0:
        count = math.ceil(count/10000)
        while(count > 0):
            sql = "delete top(10000) from acscon_ioeventlog_m{0}\
            where addr in (select addr from acscon_realnode where  iotypeid='E7AB162E-4712-E411-976E-7427EA38CA2A') and eventno in (1,3)".format(month)
            cursor_db.execute(sql)
            cursor_db.connection.commit()
            count -= 1
    print(str(month)+"月数据删除成功")

def databse_init():
    global dblink, conn_db

    conn_db = pymssql.connect(host=dblink['host'], user=dblink['user'],
                              password=dblink['password'], port=dblink['port'], database=dblink['database'])
    print("初始化数据库连接成功")

    cursor_db = conn_db.cursor()
    sql = ("select COUNT(*) from acscon_alarmactive a inner join acscon_realnode b on a.addr=b.addr where b.iotypeid='E7AB162E-4712-E411-976E-7427EA38CA2A' and evt_no in (1,3)")
    # print(sql)
    cursor_db.execute(sql)
    count = cursor_db.fetchone()[0]
    if count > 0:
        count = math.ceil(count/10000)
        while(count > 0):
            sql = "delete top(10000) from acscon_alarmactive\
            where addr in (select addr from acscon_realnode where  iotypeid='E7AB162E-4712-E411-976E-7427EA38CA2A') and evt_no in (1,3)"
            cursor_db.execute(sql)
            cursor_db.connection.commit()
            count -= 1
    print("报警数据删除功能")
    month = 12
    while(month > 0):
        delioevent(month)
        month -= 1


def database_fini():
    conn_db.close()
    print("释放连接成功")


databse_init()

database_fini()
