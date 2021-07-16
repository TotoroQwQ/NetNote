import cx_Oracle
import pymssql
import uuid

org_db = {'host': '172.31.19.83', 'port': '1521',
          'database': 'GSZJK', 'user': 'sycomk', 'password': 'dreamsoft'}

dest_db = {'host': '172.31.20.49', 'port': '56107',
           'database': 'SAFTOP-S6000', 'user': 'sa', 'password': 'NewVdb@sasaic'}

conn_org = None
conn_dest = None

stationid = ''


def databse_init():
    global org_db, dest_db, conn_org, conn_dest
    conn_org = cx_Oracle.connect(
        org_db['user'], org_db['password'], org_db['host']+':'+org_db['port']+'/'+org_db['database'])
    conn_dest = pymssql.connect(host=dest_db['host'], user=dest_db['user'],
                                password=dest_db['password'], port=dest_db['port'], database=dest_db['database'])
    print("初始化数据库连接成功")

    cursor_dest = conn_dest.cursor()
    sql = ("IF  NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[DeptConvert]') AND type in (N'U'))"
           " BEGIN"
           " CREATE TABLE [dbo].[DeptConvert]("
           " [deptid] [varchar](100) NOT NULL,"
           " [groupid] [uniqueidentifier] NOT NULL,"
           " PRIMARY KEY CLUSTERED "
           " ("
           " [deptid] ASC"
           " )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]"
           " ) ON [PRIMARY]"
           " END")
    # print(sql)
    cursor_dest.execute(sql)

    sql = ("IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[UserConvert]') AND type in (N'U'))"
           " BEGIN"
           " CREATE TABLE [dbo].[UserConvert]("
           " [userid] [varchar](100) NOT NULL,"
           " [uid] [uniqueidentifier] NULL,"
           " PRIMARY KEY CLUSTERED "
           " ("
           " [userid] ASC"
           " )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]"
           " ) ON [PRIMARY]"
           " END")

    cursor_dest.execute(sql)

    sql = ("IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[ClassConvert]') AND type in (N'U'))"
           " BEGIN"
           " CREATE TABLE [dbo].[ClassConvert]("
           " [classid] [varchar](100) NOT NULL,"
           " [gid] [uniqueidentifier] NULL,"
           " PRIMARY KEY CLUSTERED "
           " ("
           " [classid] ASC"
           " )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]"
           " ) ON [PRIMARY]"
           " END")
    cursor_dest.execute(sql)
    cursor_dest.connection.commit()


def database_fini():
    global conn_org, conn_dest
    conn_dest.close()
    conn_org.close()
    print("释放连接成功")


def get(data):
    if data:
        return "'"+str(data)+"'"
    else:
        return 'null'


def getsex(data):
    if data:
        if data == '男':
            return str(1)
        else:
            return str(0)
    else:
        return 'null'


def Insert_Dept(Dpet_Id_List, type):
    # 插入部门数据
    global conn_dest, conn_org, stationid
    if len(Dpet_Id_List) == 0:
        print("无需同步")
        return

    cursor_org = conn_org.cursor()
    cursor_dest = conn_dest.cursor()
    dict_convert = dict.fromkeys(Dpet_Id_List)

    # 转换表
    sql = 'insert into deptconvert values '
    for dept in Dpet_Id_List:
        insert_id = str(uuid.uuid1())
        dict_convert[dept] = insert_id
        sql += "('"+dept+"','"+insert_id+"'),"

    cursor_dest.execute(sql[:-1])

    # 查询部分具体数据
    dept_data_tuple = ()
    sql = 'SELECT groupid,DEPTNAME,GROUPFID FROM sycomk.D_DEPT_ALL where groupid in ('
    for id in Dpet_Id_List:
        sql += "'"+id+"',"

    sql = sql[:-1]+')'
    cursor_org.execute(sql)
    dept_data_tuple = tuple(cursor_org.fetchall())

    # 插入group表
    sql = 'insert into acscon_group (id,stationid,type,name,pid) values '
    for data in dept_data_tuple:
        sql += "('"+dict_convert[data[0]]+"','"+str(stationid)+"'," + \
            str(type)+", '"+data[1]+"', '"+dict_convert[data[2]]+"'),"
    # print(sql[:-1])
    cursor_dest.execute(sql[:-1])
    print('插入成功')
    cursor_dest.connection.commit()


def Insert_User(User_Id_List):
    # 插入人员数据
    global conn_dest, conn_org, stationid
    if len(User_Id_List) == 0:
        print("无需同步")
        return
    cursor_org = conn_org.cursor()
    cursor_dest = conn_dest.cursor()
    dict_convert = dict.fromkeys(User_Id_List)

    # 转换表
    sql = 'insert into userconvert values '
    for user in User_Id_List:
        insert_id = str(uuid.uuid1())
        dict_convert[user] = insert_id
        sql += "('"+user+"','"+insert_id+"'),"

    cursor_dest.execute(sql[:-1])

    # 查询部分具体数据
    user_data_tuple = ()
    sql = 'SELECT groupid,username,logname,password,gender,types,idno,mobile,ryzt,yktsf FROM sycomk.D_USER_ALL where groupid in ('
    for id in User_Id_List:
        sql += "'"+id+"',"

    sql = sql[:-1]+')'
    cursor_org.execute(sql)
    user_data_tuple = tuple(cursor_org.fetchall())

    # 插入group表
    sql = 'insert into acscon_user (id,stationid,name,usercode,pwd,sex,phone,status,type) values '
    for data in user_data_tuple:
        sql += "('"+dict_convert[data[0]]+"','"+str(stationid)+"','"+str(data[1])+"', '"+str(data[2])+"', 'fhWuQ7Ia6cM=',"+getsex(
            data[4])+", "+get(data[7])+", "+str(1)+", "+str(1)+"),"
    # print(sql[:-1])
    cursor_dest.execute(sql[:-1])
    cursor_dest.connection.commit()
    print('插入成功')

    # cursor_dest.connection.commit()


def Insert_Class(Class_Id_List, type, class_pid):
    # 插入班级分组
    global conn_dest, conn_org, stationid
    if len(Class_Id_List) == 0:
        print("无需同步")
        return

    cursor_org = conn_org.cursor()
    cursor_dest = conn_dest.cursor()
    dict_convert = dict.fromkeys(Class_Id_List)

    # 转换表
    sql = 'insert into Classconvert values '
    for cla in Class_Id_List:
        insert_id = str(uuid.uuid1())
        dict_convert[cla] = insert_id
        sql += "('"+cla+"','"+insert_id+"'),"

    cursor_dest.execute(sql[:-1])

    # 查询没有同步过数据
    class_data_tuple = ()
    sql = 'SELECT groupid,CLASSNAME FROM sycomk.D_Class_ALL where groupid in ('
    for id in Class_Id_List:
        sql += "'"+id+"',"

    sql = sql[:-1]+')'
    cursor_org.execute(sql)
    class_data_tuple = tuple(cursor_org.fetchall())

    # 插入group表
    sql = 'insert into acscon_group (id,stationid,type,name,pid) values '
    for data in class_data_tuple:
        sql += "('"+dict_convert[data[0]]+"','"+str(stationid)+"'," + \
            str(type)+", '"+data[1]+"', '"+str(class_pid)+"'),"
    # print(sql[:-1])
    cursor_dest.execute(sql[:-1])
    print('插入成功')
    cursor_dest.connection.commit()


def Insert_Stud(Stud_Id_List):
    # 插入学生数据，和人员类似
    global conn_dest, conn_org, stationid
    if len(Stud_Id_List) == 0:
        print("无需同步")
        return
    cursor_org = conn_org.cursor()
    cursor_dest = conn_dest.cursor()
    dict_convert = dict.fromkeys(Stud_Id_List)

    Stud_Id_List = list(Stud_Id_List)
    Stud_Id_Table = [Stud_Id_List[i:i + 500]
                     for i in range(0, len(Stud_Id_List), 500)]
    for List_student in Stud_Id_Table:
        # 转换表
        sql = 'insert into userconvert values '
        for user in List_student:
            insert_id = str(uuid.uuid1())
            dict_convert[user] = insert_id
            sql += "('"+user+"','"+insert_id+"'),"

        cursor_dest.execute(sql[:-1])

        # 查询部分具体数据
        user_data_tuple = ()
        sql = 'SELECT groupstuid,username,logname,password,gender,types,idno,cellphone,type,cphm FROM sycomk.D_STUDENT_ALL where groupstuid in ('
        for id in List_student:
            sql += "'"+id+"',"

        sql = sql[:-1]+')'
        cursor_org.execute(sql)
        user_data_tuple = tuple(cursor_org.fetchall())

        # 插入group表
        sql = 'insert into acscon_user (id,stationid,name,usercode,pwd,sex,phone,type,status) values '
        for data in user_data_tuple:
            sql += "('"+dict_convert[data[0]]+"','"+str(stationid)+"','"+str(data[1])+"', '"+str(data[2])+"', 'fhWuQ7Ia6cM=',"+getsex(
                data[4])+", "+get(data[7])+", "+str(1)+", "+str(1)+"),"
        # print(sql[:-1])
        cursor_dest.execute(sql[:-1])
    cursor_dest.connection.commit()
    print('插入成功')


def Dept_sync():
    # 同步部门
    global conn_org, conn_dest, stationid
    cursor_org = conn_org.cursor()
    cursor_dest = conn_dest.cursor()

    # 获取站点id
    cursor_dest.execute(
        'select id from acscon_group where pid is null and type = 0')
    result = cursor_dest.fetchone()
    stationid = '' if result is None else result[0]
    if stationid == '':
        print('目标数据库异常，同步部门失败')
        return
    type = 1  # 组织人员的分组类型

    # 获取源数据库部门数据
    # 转化部门id
    Dpet_Id_List = set([])
    cursor_org.execute('select groupid,groupfid from sycomk.d_dept_all')
    for row in cursor_org:
        Dpet_Id_List = Dpet_Id_List | set(row)
    cursor_dest.execute('select deptid from deptconvert')
    result = cursor_dest.fetchall()
    for row in result:
        Dpet_Id_List = Dpet_Id_List-set(row)

    Insert_Dept(Dpet_Id_List, type)  # 同步部门


def User_sync():
    # 同步人员
    global conn_org, conn_dest
    cursor_org = conn_org.cursor()
    cursor_dest = conn_dest.cursor()

    # 获取源数据库人员数据
    # 转化人员id
    User_Id_List = set([])
    cursor_org.execute('select groupid from sycomk.d_user_all')
    for row in cursor_org:
        User_Id_List = User_Id_List | set(row)
    cursor_dest.execute('select userid from userconvert')
    result = cursor_dest.fetchall()
    for row in result:
        User_Id_List = User_Id_List-set(row)

    Insert_User(User_Id_List)


def Dept_user_sync():
    # 同步人员-部门对应关系
    global conn_org, conn_dest
    cursor_org = conn_org.cursor()
    cursor_dest = conn_dest.cursor()

    cursor_org.execute(
        'select groupdeptid,groupuserid from sycomk.d_dept_user_all')
    Data_all = set(cursor_org.fetchall())  # 所有数据
    # print(Data_all)

    cursor_dest.execute(
        'select deptid ,userid from acscon_groupmember gm inner join DeptConvert d on gm.gid=d.groupid inner join userconvert u on gm.uid=u.uid')
    Data_Done = set(cursor_dest.fetchall())  # 已有数据
    # print(Data_Done)

    Data_rest = Data_all-Data_Done  # 剩余需要同步的数据
    # print(Data_rest)
    if len(Data_rest) == 0:
        print('无需同步')
        return
    Data_rest = list(Data_rest)
    Data_rest_table = [Data_rest[i:i+500]
                       for i in range(0, len(Data_rest), 500)]
    for data in Data_rest_table:
        sql = 'insert into acscon_groupmember (uid,gid) values '
        for row in data:
            sql += "(ISNULL((select uid from userconvert where userid = '" + \
                row[1]+"'),NEWID()),ISNULL((select groupid from deptconvert where deptid = '" + \
                row[0]+"'),NEWID())),"
        # print(sql[:-1])

        cursor_dest.execute(sql[:-1])
    cursor_dest.connection.commit()
    print('插入成功')


def Class_sync():
    # 同步班级
    global conn_org, conn_dest, stationid
    cursor_org = conn_org.cursor()
    cursor_dest = conn_dest.cursor()

    type = 1  # 组织人员的分组类型
    class_pid = ''  # 班级的父节点

    # 先在人员分组下建一个班级分组，作为班级的父节点
    cursor_dest.execute(
        "select id from acscon_group where type=1 and name='班级'")
    row = cursor_dest.fetchone()
    if row is None:
        class_pid = str(uuid.uuid1())
        cursor_dest.execute("insert into acscon_group (id,stationid,type,name,pid) values ('" +
                            class_pid+"','"+str(stationid)+"','"+str(1)+"','班级','"+str(stationid)+"')")
        cursor_dest.connection.commit()
    else:
        class_pid = str(row[0])

    # 获取源数据库部门数据
    # 转化部门id
    Class_Id_List = set([])
    cursor_org.execute('select groupid from sycomk.d_class_all')
    for row in cursor_org:
        Class_Id_List = Class_Id_List | set(row)
    cursor_dest.execute('select classid from classconvert')
    result = cursor_dest.fetchall()
    for row in result:
        Class_Id_List = Class_Id_List-set(row)

    Insert_Class(Class_Id_List, type, class_pid)  # 同步部门


def Student_sync():
    # 同步学生
    global conn_org, conn_dest
    cursor_org = conn_org.cursor()
    cursor_dest = conn_dest.cursor()

    # 获取源数据库人员数据
    # 转化人员id
    Stud_Id_List = set([])
    cursor_org.execute('select groupstuid from sycomk.d_student_all')
    for row in cursor_org:
        Stud_Id_List = Stud_Id_List | set(row)
    cursor_dest.execute('select userid from userconvert')
    result = cursor_dest.fetchall()
    for row in result:
        Stud_Id_List = Stud_Id_List-set(row)

    Insert_Stud(Stud_Id_List)
    Class_stu_sync(list(Stud_Id_List))


def Class_stu_sync(Stud_Id_List):
    # 同步学生-班级对应关系
    global conn_org, conn_dest
    cursor_org = conn_org.cursor()
    cursor_dest = conn_dest.cursor()

    if len(Stud_Id_List) == 0:
        print("无需同步")
        return

    # 将未同步列表，分隔成500条一组的二维数组
    Stud_Id_List = [Stud_Id_List[i:i+500]
                    for i in range(0, len(Stud_Id_List), 500)]
    for datalist in Stud_Id_List:
        sql = "select groupstuid,classid from sycomk.d_student_all where groupstuid in ("
        for data in datalist:
            sql += "'"+str(data)+"',"
        sql = sql[:-1]+")"
        cursor_org.execute(sql)

        result = list(cursor_org.fetchall())

        sql = 'insert into acscon_groupmember (uid,gid) values '
        for row in result:
            sql += "(ISNULL((select uid from userconvert where userid = '" + \
                row[0]+"'),NEWID()),ISNULL((select gid from Classconvert where classid = 'A" + \
                str(row[1])+"'),NEWID())),"
        # print(sql[:-1])
        cursor_dest.execute(sql[:-1])
    cursor_dest.connection.commit()
    print('插入成功')


databse_init()
# 人员流程
Dept_sync()
User_sync()
Dept_user_sync()
# 学生流程
Class_sync()
Student_sync()

database_fini()
