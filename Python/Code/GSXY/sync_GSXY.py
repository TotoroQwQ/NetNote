import cx_Oracle
import pymssql
import uuid

'''
org_db = {'host': '172.31.19.83', 'port': '1521',
          'database': 'GSZJK', 'user': 'sycomk', 'password': 'dreamsoft'}

dest_db = {'host': '172.31.20.49', 'port': '56107',
           'database': 'SAFTOP-S6000', 'user': 'sa', 'password': 'NewVdb@sasaic'}
'''
org_db = {'host': '127.0.0.1', 'port': '1521',
          'database': 'orcl', 'user': 'sycomk', 'password': 'dreamsoft'}

dest_db = {'host': '127.0.0.1', 'port': '1433',
           'database': '171219', 'user': 'sa', 'password': 'saftop'}

conn_org = None
conn_dest = None

stationid = ''

def databse_init():
    global org_db, dest_db, conn_org, conn_dest,stationid
    conn_org = cx_Oracle.connect(
        org_db['user'], org_db['password'], org_db['host']+':'+org_db['port']+'/'+org_db['database'])
    conn_dest = pymssql.connect(host=dest_db['host'], user=dest_db['user'],
                                password=dest_db['password'], port=dest_db['port'], database=dest_db['database'])
    print("初始化数据库连接成功")
    cursor_dest = conn_dest.cursor()

    sql = ("IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[StudentConvert]') AND type in (N'U'))"
           " BEGIN"
           " CREATE TABLE [dbo].[StudentConvert]("
           " [stuid] [varchar](100) NOT NULL,"
           " [name] [varchar](100),"
           " [cardcode] [varchar](100),"
           " [roomno] [varchar](100),"
           " [gender] [varchar](10),"
           " [classid] int,"
           " PRIMARY KEY CLUSTERED "
           " ("
           " [stuid] ASC"
           " )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]"
           " ) ON [PRIMARY]"
           " END")
    cursor_dest.execute(sql)
    sql = ("IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[ClassConvert]') AND type in (N'U'))"
           " BEGIN"
           " CREATE TABLE [dbo].[ClassConvert]("
           " [classid] [varchar](100) NOT NULL,"
           " [classname] [varchar](100) NOT NULL,"
           " [local] [varchar](100) NOT NULL,"
           " [starttime] [datetime] NOT NULL,"
           " [endtime] [datetime] NOT NULL,"
           " [gid] [uniqueidentifier] NULL,"
           " PRIMARY KEY CLUSTERED "
           " ("
           " [classid] ASC"
           " )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]"
           " ) ON [PRIMARY]"
           " ALTER TABLE [dbo].[ClassConvert] ADD CONSTRAINT [CLASSID_GID]  DEFAULT (newsequentialid()) FOR [Gid]"
           " END")
    cursor_dest.execute(sql)
    cursor_dest.connection.commit()
    # 获取站点id
    cursor_dest.execute('select id from acscon_group where pid is null and type = 0')
    result = cursor_dest.fetchone()
    stationid = '' if result is None else result[0]
    if stationid == '':
        print('目标数据库异常，初始化失败')
        return False
    return True

def database_fini():
    global conn_org, conn_dest
    conn_dest.close()
    conn_org.close()
    print("释放连接成功")


def sync_class():
    #同步班级,将对方的班级中间表全部加到映射表中
    global conn_org, conn_dest ,stationid
    cursor_org = conn_org.cursor()
    cursor_dest = conn_dest.cursor()

    # 先在人员分组下建一个班级分组，作为班级的父节点
    sql='IF NOT EXISTS (SELECT ID FROM ACSCON_GROUP WHERE TYPE = \'{1}\' AND NAME = \'{2}\')\
        BEGIN\
        insert into acscon_group (stationid,type,name,pid) values (\'{0}\',\'{1}\',\'{2}\',\'{0}\')\
        END'.format(stationid,1,'班级')
    cursor_dest.execute(sql)
    cursor_dest.connection.commit()

    #获取需要更新的班级数据
    Class_Id_List = set([])
    cursor_org.execute('select SUBSTR(groupid, 2, LENGTH(groupid)-1) from sycomk.d_class_all')
    for row in cursor_org:
        Class_Id_List = Class_Id_List | set(row)
    cursor_dest.execute('select classid from classconvert')
    result = cursor_dest.fetchall()
    for row in result:
        Class_Id_List = Class_Id_List-set(row)
    
    if len(Class_Id_List) == 0:
        print("班级无需同步")
        return
    #查询需要同步的具体数据
    sql = 'SELECT SUBSTR(groupid, 2, LENGTH(groupid)-1),CLASSNAME,FCRNUMBER,STARTTIME,ENDTIME FROM sycomk.D_Class_ALL where groupid in ('
    for id in Class_Id_List:
        sql += "'"+id+"',"
    #sql = sql[:-1]+')'
    cursor_org.execute(sql[:-1]+')')
    class_data_tuple = tuple(cursor_org.fetchall())

    # 插入到中间表
    sql = 'insert into CLASSCONVERT (CLASSID,CLASSNAME,LOCAL,STARTTIME,ENDTIME) values '
    for data in class_data_tuple:
        sql += '(\'{0}\',\'{1}\',\'{2}\',\'{3}\',\'{4}\'),'.format(data[0],data[1],data[2],data[3],data[4])
    # print(sql[:-1])
    cursor_dest.execute(sql[:-1])
    print('班级成功同步:',len(class_data_tuple),'条记录')
    cursor_dest.connection.commit()
    
def sync_student():
    #同步学生，将对方中间表的学生全部加到我们的映射表中
    global conn_org, conn_dest, stationid
    cursor_org = conn_org.cursor()
    cursor_dest = conn_dest.cursor()

    #查询所有人员数据
    stu_data_tuple = ()
    sql = 'SELECT GROUPSTUID,USERNAME,KH,FH,GENDER,CLASSID FROM sycomk.D_STUDENT_ALL WHERE CLASSID IN ( \
            SELECT SUBSTR(GROUPID, 2, LENGTH(GROUPID)-1) FROM SYCOMK.D_CLASS_ALL WHERE (SELECT SYSDATE FROM DUAL) BETWEEN STARTTIME AND ENDTIME)'
    cursor_org.execute(sql)
    stu_data_tuple = tuple(cursor_org.fetchall())

    for stu in stu_data_tuple:
        sql='\
        IF NOT EXISTS (SELECT STUID FROM STUDENTCONVERT WHERE STUID = \'{0}\')\
        BEGIN\
            INSERT INTO STUDENTCONVERT (STUID,NAME,CARDCODE,ROOMNO,GENDER,CLASSID) VALUES (\'{0}\',\'{1}\',\'{2}\',\'{3}\',\'{4}\',\'{5}\')\
        END\
        ELSE\
        BEGIN\
            UPDATE STUDENTCONVERT SET NAME=\'{1}\',CARDCODE=\'{2}\',ROOMNO=\'{3}\',GENDER=\'{4}\',CLASSID=\'{5}\' WHERE STUID=\'{0}\'\
        END'.format(stu[0],stu[1],stu[2],stu[3],stu[4],stu[5])
        #print(sql)
        cursor_dest.execute(sql)
        cursor_dest.connection.commit()
    print('成功同步学生:',len(stu_data_tuple),'条记录')


def update_student_class():
    #将映射表中的数据写入人员表和分组表。
    global conn_dest,stationid
    cursor_dest = conn_dest.cursor()

    #更新班级数据
    sql='SELECT CLASSNAME,GID FROM CLASSCONVERT WHERE GID NOT IN (SELECT ID FROM ACSCON_GROUP) AND GETDATE() BETWEEN STARTTIME AND ENDTIME '
    cursor_dest.execute(sql)
    newclass_list=tuple(cursor_dest.fetchall())
    if len(newclass_list)==0:
        print("班级无需更新")
    else:
        for cla in newclass_list:
            sql='insert into acscon_group (ID,stationid,type,name,pid) values (\'{0}\',\'{1}\',\'{2}\',\'{3}\',{4})'.format(cla[1],stationid,1,cla[0],'(select id from acscon_group where name=\'班级\')')
            cursor_dest.execute(sql)
        print('班级更新成功:',len(newclass_list),'条记录')
        cursor_dest.connection.commit()
    
    #更新人员数据
    sql='select cardcode,name,gender,classid from studentconvert \
        where classid in (select classid from ClassConvert where GETDATE() between starttime and endtime) \
        and cardcode <>\'None\''
    cursor_dest.execute(sql)
    stud_list=tuple(cursor_dest.fetchall())
    if len(stud_list)==0:
        print('暂无上课人员')
    else:
        for stu in stud_list:
            sql='if not exists (select usercode from acscon_user where usercode=\'{0}\')\
                begin\
                    insert into acscon_user (stationid,usercode,name,sex,type,pwd,status) values (\'{6}\',\'{0}\',\'{1}\',\'{2}\',\'{3}\',\'{4}\',\'{5}\')\
                    insert into acscon_groupmember (uid,gid) values ((select id from acscon_user where usercode=\'{0}\'),(select gid from classconvert where classid=\'{7}\'))\
                end\
                else\
                begin\
                    update acscon_user set name=\'{1}\',sex=\'{2}\' where usercode=\'{0}\'\
                    update acscon_groupmember set gid=(select gid from ClassConvert where classid=\'{7}\') where uid=(select id from acscon_user where usercode=\'{0}\')\
                end'.format(stu[0],stu[1],stu[2],1,'pwd',1,stationid,stu[3])
            cursor_dest.execute(sql)
        print('人员更新成功:',len(stud_list),'条记录')
        cursor_dest.connection.commit()


if __name__ == "__main__":
    if(databse_init()):
        #先同步所有有效数据
        sync_class()
        sync_student()
        #将映射表中的数据写入人员表和分组表。
        update_student_class()
        database_fini()