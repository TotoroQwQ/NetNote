#coding=utf-8
import sys
import time
import datetime
import pymysql
import pymssql
'''
用于安冠门禁系统与云平台考勤系统对接
2019-08-26
使用说明:
python版本： python3
依赖库安装:
pip install pymysql
pip install pymssql
参数说明:
参数1：租户ID
参数2：门禁库地址
参数3：门禁库IP,默认为1433
参数4：门禁库登录账号
参数5：门禁库登录密码
参数6：门禁数据库名称
参数7：云平台uaa数据库地址
参数8：云平台uaa数据库端口默认为3306
参数9：uaa库登录账号
参数10：uaa库登录密码
参数11：uaa数据库名称
参数12：考勤系统数据库名称
参数13：同步模式:0:同步所有数据，1:只同步考勤记录
参数14：考勤记录同步开始时间,为空，默认为前一天
参数15：考勤记录同步结束时间，为空，默认为后一天
参数示例:
python -W ignore sync_saftop_2_yun.py "c91b576f671b4875b43ad1899afe9593" "20.0.0.66" "1433" "sa" "sa" "whxdl" "20.0.0.252" "3306" "root" "root" "st_admin2" "st_attendance_gs" "0" "" ""

'''
# 租户ID
tid = ''
# 源数据库
org_conn = None
# 目标数据库
dest_conn = None
# 目标考勤库
att_conn = None
# 同步类型 0:同步所有数据，1:只同步考勤记录
sync_type = 0
# 考勤同步时间范围 格式：年-月-日 2019-08-13
sync_time_beg=''
sync_time_end=''

'''
    凭证类型映射
    组态系统：0：卡 1：指纹 2:身份证 3:车牌 4:掌纹 5：人脸 8:二维码
    云平台: 1：卡 2：指纹 3：人脸
'''
certi_type={0:1,1:2,2:1,3:1,4:1,5:3,8:1}
# 同步计数，用于日志记录
sync_count=0


#初始化数据库连接
def init():
    print(sys.argv)
    if len(sys.argv) < 16:
        print("请输入合法参数.\r\n")
        return

    global org_conn,dest_conn,att_conn,tid,sync_type,sync_time_beg,sync_time_end
    #租户ID
    tid=sys.argv[1] # '123456'
    # 组态数据库连接参数
    org_db_host=sys.argv[2] #'20.0.0.216'
    org_db_port=sys.argv[3] #'1433'
    org_db_user=sys.argv[4] #'sa'
    org_db_pwd=sys.argv[5]  #'888888'
    org_db_database=sys.argv[6] #'sz'
    # 目标考勤系统数据库连接参数
    dest_db_host=sys.argv[7] #'20.0.0.252'
    dest_db_port=sys.argv[8] #'3306'
    dest_db_user=sys.argv[9] #'root'
    dest_db_pwd=sys.argv[10]  #'root'
    dest_db_database=sys.argv[11] #'st_admin2'
    dest_att_db_database=sys.argv[12] #'st_attendance'
    # 同步类型
    sync_type=sys.argv[13] #'0'
    # 同步时间
    sync_time_beg = sys.argv[14]
    sync_time_end = sys.argv[15]

    if not tid.strip():
         print("租户ID不能为空.\r\n")
         return

    if not org_db_host.strip():
         print("数据库地址不能为空.\r\n")
         return

    if not org_db_user.strip():
         print("数据库用户名不能为空.\r\n")
         return
    if not org_db_database.strip():
         print("数据库名不能为空.\r\n")
         return

    org_conn = pymssql.connect(host=org_db_host,user=org_db_user,port=int(org_db_port),
                        password=org_db_pwd,database=org_db_database,
                        charset="utf8")

    dest_conn = pymysql.connect(host=dest_db_host,port=int(dest_db_port),
                        user=dest_db_user,passwd=dest_db_pwd,database=dest_db_database,
                        charset="utf8mb4")
    
    att_conn = pymysql.connect(host=dest_db_host,port=int(dest_db_port),
                        user=dest_db_user,passwd=dest_db_pwd,database=dest_att_db_database,
                        charset="utf8mb4")

    #查看连接是否成功
    print("初始化数据库连接成功\r\n")

# 释放数据库连接资源
def fini():
    global org_conn,dest_conn,att_conn,tid
    org_conn.close()
    dest_conn.close()
    att_conn.close()
    print("释放数据库连接成功\r\n")

# 同步部门数据
def sync_department():
    global org_conn,dest_conn,tid
    org_cursor = org_conn.cursor()
    dest_cursor = dest_conn.cursor()
    # 检查租户是否存在
    sql='select `password` from base_user where tenant_id=\''+tid+'\' and type=2'
    dest_cursor.execute(sql)
    row = dest_cursor.fetchone()
    if row is None:
        print("租户不存在，请检查配置.\r\n")
        return

    # 查找该租户的用户分组根ID
    sql='select id from base_data_group FORCE INDEX(i_tid_pid) where parent_id = -1 and grp_type=1 and tenant_id=\''+tid+'\''
    dest_cursor.execute(sql)
    row = dest_cursor.fetchone()
    if row is None:
        print("添加租户管理员的时候，没有添加默认分组，或检查租户ID是否正确.\r\n")
        return    
    # 分组根ID
    rootID = row[0]

    # 获取门禁系统部门
    sql='select top 1 id,name from acscon_group where type=0'
    org_cursor.execute(sql)
    row = org_cursor.fetchone()
    if row is None:
        print("待导入数据无部门信息.\r\n")
        return

    org_dep_id = str(row[0])
    org_dep_name = row[1]
    # 在云平台找查找是否存在该部门
    sql='select id from base_data_group FORCE INDEX(i_tid_name) where grp_type=1 and name =\''+org_dep_name+'\' and tenant_id=\''+tid+'\''
    dest_cursor.execute(sql)
    row = dest_cursor.fetchone()
    last_id=0
    if row is None:
        sql='insert into base_data_group(name,parent_id,grp_type,tenant_id) values(\'{0}\',{1},{2},\'{3}\')'.format(org_dep_name,rootID,1,tid)
        dest_cursor.execute(sql)
        last_id = dest_conn.insert_id()
        dest_conn.commit()
    else:
        last_id = row[0]
    # 新增分组数据
    addDataGrp(org_dep_id,last_id,1)
    print('新增/更新 部门： {0}\r\n'.format(sync_count))

# 检查部门是否存在
def checkDataGrpExist(code,pid):
    global dest_conn,tid
    dest_cursor = dest_conn.cursor()
    # 在云平台找查找是否存在该部门
    sql='select id,name from base_data_group FORCE INDEX(i_tid_name) where grp_type=1  and tenant_id=\''+tid+'\' and parent_id='+str(pid)+' and code = \''+str(code)+'\''
    dest_cursor.execute(sql)
    row = dest_cursor.fetchone()
    return row

# 新增分组数据
def addDataGrp(orgpid,destPid,grpType):
    global org_conn,dest_conn,tid,sync_count
    org_cursor = org_conn.cursor()
    dest_cursor = dest_conn.cursor()
    sql= 'select id,name from acscon_group where type=1 and pid=\''+str(orgpid)+'\''
    org_cursor.execute(sql)
    id = 0;
    # 一次性获取所有数据
    rows = org_cursor.fetchall()
    for row in rows:
        n = checkDataGrpExist(row[0],destPid)
        if n is None:
            sql='insert into base_data_group(code,name,parent_id,grp_type,tenant_id) values(\'{0}\',\'{1}\',{2},{3},\'{4}\')'.format(row[0],row[1],destPid,1,tid)
            dest_cursor.execute(sql)
            id = dest_conn.insert_id()
            dest_conn.commit()
            # 统计计数递增
            sync_count = sync_count +1
        else:
            # 存在，且部门名称不一样，更新部门名称
            id = n[0]
            if n[1] != row[1]:
                sql='update base_data_group set name = \'{0}\' where id={1}'.format(row[1],id)
                dest_cursor.execute(sql)
                dest_conn.commit()
                sync_count = sync_count +1
        addDataGrp(row[0],id,1)
        row=org_cursor.fetchone()

# 检查用户是否存在
def checkUserExist(ucode):
    global dest_conn,tid
    dest_cursor = dest_conn.cursor()
    sql='select id,name from base_user where username = \''+ucode+'\' and tenant_id = \''+tid+'\''
    dest_cursor.execute(sql)
    row = dest_cursor.fetchone()
    return row

# 检查用户部门是否有变动
def checkUserDepChange(ucode):
    global org_conn,dest_conn
    org_cursor = org_conn.cursor()
    dest_cursor = dest_conn.cursor()
    # 门禁系统中的用户部门关系
    sql='select t1.id from acscon_group t1 inner join acscon_groupmember t2 on t1.id=t2.gid inner join acscon_user t3 on t3.id=t2.uid where t3.usercode=\'{0}\''.format(ucode)
    org_cursor.execute(sql)
    org_deps = org_cursor.fetchall()
    # 云平台中的用户部门关系
    sql='SELECT t2.`code` FROM base_department_data_group t1 JOIN base_data_group t2 ON t1.data_group_id = t2.id JOIN base_user t3 ON t3.id = t1.user_id WHERE t3.username = \'{0}\''.format(ucode)
    dest_cursor.execute(sql)
    dest_deps = dest_cursor.fetchall()
    if len(org_deps) != len(dest_deps):
        return True
    same = False
    for d1 in dest_deps:
        same = False
        for d2 in org_deps:
            if str(d1[0]) == str(d2[0]):
                same = True
                break
        # 没有找到
        if same == False:
            return True
            
    return False

# 检查用户卡是否有变动
def checkUseCardChange(ucode):
    global org_conn,dest_conn
    org_cursor = org_conn.cursor()
    dest_cursor = dest_conn.cursor()
    # 门禁系统中的用户卡关系
    sql='select t1.cardno from acscon_card t1 inner join acscon_usercard t2 on t1.id=t2.cardid inner join acscon_user t3 on t3.id=t2.uid where t3.usercode=\'{0}\''.format(ucode)
    org_cursor.execute(sql)
    org_cards = org_cursor.fetchall()
    # 云平台中的用户卡关系
    sql='select t1.certi_data from base_user_certification t1 join base_user t2 on t1.user_id = t2.id WHERE t2.username = \'{0}\''.format(ucode)
    dest_cursor.execute(sql)
    dest_cards = dest_cursor.fetchall()
    if len(org_cards) != len(dest_cards):
        return True
    same = False
    for d1 in dest_cards:
        same = False
        for d2 in org_cards:
            if str(d1[0]) == str(d2[0]):
                same = True
                break
        # 没有找到
        if same == False:
            return True
            
    return False

# 同步人员
def sync_user():
    # 默认密码
    password=''
    global org_conn,dest_conn,tid,certi_type,sync_count
    sync_count=0
    org_cursor = org_conn.cursor()
    dest_cursor = dest_conn.cursor()
    
    # 只同步非管理员数据
    # sql='select id,usercode,name,sex from acscon_user where type != 0'
    sql = 'select id,usercode,name,sex from acscon_user where type != 0 and  name not like \'XZXY-%\' and usercode like \'XZXY-%\''
    org_cursor.execute(sql)
    # 一次性获取所有数据
    rows = org_cursor.fetchall()
    uid=0
    isUpdate=False
    for row in rows:
        u =checkUserExist(row[1])
        if u is None:
            # 新增用户
            sql='insert into base_user(tenant_id,username,password,name,sex,type) values(\'{0}\',\'{1}\',\'{2}\',\'{3}\',\'{4}\',{5})'.format(tid,row[1],password,row[2],'男' if (row[3]==1) else '女',3)
            dest_cursor.execute(sql)
            uid = dest_conn.insert_id()
            dest_conn.commit()
            sync_count = sync_count + 1
            isUpdate = False
        else:
            uid=u[0]
            # 用户存在，且名称不一样，更新
            if u[1] != row[2] or checkUserDepChange(row[1]):
                sql='update base_user set name = \'{0}\' where id={1}'.format(row[2],uid)
                dest_cursor.execute(sql)
                dest_conn.commit()
                sync_count = sync_count + 1
                isUpdate = True
    
        # 如果是更新的用户，清空该用户以前的旧数据(部门，凭证)
        if isUpdate == True:
            # 删除部门关系
            sql='delete from base_department_data_group where  user_id={0} and tenant_id=\'{1}\''.format(uid,tid)
            dest_cursor.execute(sql)
            dest_conn.commit()
            # 删除凭证
            sql='delete from base_user_certification where user_id={0} and tenant_id=\'{1}\''.format(uid,tid)
            dest_cursor.execute(sql)
            dest_conn.commit()

        # 新增用户与部门的关系
        sql='select t1.name,t1.id from acscon_group t1 inner join acscon_groupmember t2 on t1.id=t2.gid inner join acscon_user t3 on t3.id=t2.uid where t3.usercode=\'{0}\''.format(row[1])
        org_cursor.execute(sql)
        deps = org_cursor.fetchall()
        # 可能存在多个部门
        for dep in deps:
            #先查找部门ID
            sql='select id from base_data_group FORCE INDEX(i_tid_name) where name=\'{0}\' and code = \'{1}\' and grp_type=1 and tenant_id=\'{2}\''.format(dep[0],dep[1],tid)
            dest_cursor.execute(sql)
            d = dest_cursor.fetchone()
            # 部门ID找不到?不可能，除非异常
            if d is None:
                continue
            
            # 人与部门的关系处理
            sql='select id from base_department_data_group where data_group_id={0} and user_id={1} and tenant_id=\'{2}\''.format(d[0],uid,tid)
            dest_cursor.execute(sql)
            du = dest_cursor.fetchone()
            if du is None:
                # 新的部门关系
                sql='insert into base_department_data_group(data_group_id,user_id,tenant_id) values({0},{1},\'{2}\')'.format(d[0],uid,tid)
                dest_cursor.execute(sql)
                dest_conn.commit()
        
        # 新增用户凭证
        sql='select t1.cardno,t1.idtype from acscon_card t1 inner join acscon_usercard t2 on t1.id=t2.cardid inner join acscon_user t3 on t3.id=t2.uid where t3.usercode=\'{0}\''.format(row[1])
        org_cursor.execute(sql)
        cards = org_cursor.fetchall()
        # 可能存在多个凭证
        for c in cards:
            # 是否已经添加过
            sql='select id from base_user_certification where certi_type_id={0} and certi_data=\'{1}\' and tenant_id=\'{2}\''.format(certi_type[c[1]],c[0],tid)
            dest_cursor.execute(sql)
            cu = dest_cursor.fetchone()
            if cu is None:
                # 默认全部当永久类型
                sql='insert into base_user_certification(user_id,certi_type_id,certi_data,certi_validity_type,tenant_id) values({0},{1},\'{2}\',1,\'{3}\')'.format(uid,certi_type[c[1]],c[0],tid)
                dest_cursor.execute(sql)
                dest_conn.commit()

    print('新增/更新 用户:{}\r\n'.format(sync_count))

# 检查考勤点是否存在
def checkAttPointExist(addr):
    global att_conn,tid
    att_cursor = att_conn.cursor()
    sql='select id,address,name,tenant_id from att_node where address = \''+addr+'\' and tenant_id = \''+tid+'\''
    att_cursor.execute(sql)
    row = att_cursor.fetchone()
    return row

# 同步考勤点
def sync_point():
    global org_conn,att_conn,tid,sync_count
    sync_count = 0
    org_cursor = org_conn.cursor()
    att_cursor = att_conn.cursor()
    # 获取门禁系统考勤点数据
    sql='select name,addr from acscon_realnode where iotypeid in (select id from acscon_iotype where descr like \'%DR\' or descr like \'%RD\')'
    org_cursor.execute(sql)
    # 一次性获取所有数据
    rows = org_cursor.fetchall()
    id=0
    for row in rows:
        p =checkAttPointExist(row[1])
        if p is None:
            # 新增考勤点
            sql='insert into att_node(name,address,tenant_id) values(\'{0}\',\'{1}\',\'{2}\')'.format(row[0],row[1],tid)
            att_cursor.execute(sql)
            id = att_conn.insert_id()
            att_conn.commit()
            sync_count = sync_count +1
        else:
            id=p[0]
    print('新增考勤点:{0}\r\n'.format(sync_count))


# 字符串时间格式转unix时间戳
def time2unix(t):
    # 转换为毫秒
     return int(time.mktime(t.timetuple()))*1000

# 检查考勤记录是否已经同步过
def checkAttExist(certificate_type,certificate_data,address,clock_time,tenant_id,create_time):
    global att_conn
    t = create_time.strftime("%Y-%m-%d %H:%M:%S")
    att_cursor = att_conn.cursor()
    sql='select id from att_sync where tenant_id=\'{0}\' and certificate_type={1} and certificate_data=\'{2}\' and address=\'{3}\' and clock_time={4} and create_time=\'{5}\''.format(tid,certificate_type,certificate_data,address,clock_time,t)
    att_cursor.execute(sql)
    row = att_cursor.fetchone()
    return row

# 同步考勤记录
def sync_att_data():
    global org_conn,att_conn,tid,sync_time_beg,sync_time_end,certi_type,sync_count
    sync_count = 0
    org_cursor = org_conn.cursor()
    att_cursor = att_conn.cursor()
    # 当前月份
    cur_month=0

    # 默认给空的时间范围，取前一天的记录
    cur_date_beg=datetime.datetime.now()+datetime.timedelta(days=-1)
    cur_date_end=datetime.datetime.now()+datetime.timedelta(days=+1)
    # 如果有指定的开始时间,就使用指定日期
    if len(sync_time_beg.strip())!=0:
        cur_date_beg=datetime.datetime.strptime(sync_time_beg,'%Y-%m-%d')
    
    sync_time_beg=cur_date_beg.strftime("%Y-%m-%d")
    cur_month=cur_date_beg.month

    if len(sync_time_end.strip())!=0:
        cur_date_end=datetime.datetime.strptime(sync_time_end,'%Y-%m-%d')
    
    sync_time_end=cur_date_end.strftime("%Y-%m-%d")

    if cur_date_end <= cur_date_beg:
        print("同步结束时间必须大于开始时间\r\n")
        return
    
    print("开始同步考勤记录 当前月份:{0} 时间:{1} --> {2}\r\n".format(cur_month,sync_time_beg,sync_time_end))
    pgindex=1
    pgsize=1000

    while True:
        sql='''
        SELECT u.name as username,u.usercode,lg.cardno,ie.descr,rn.name,rn.addr,rn.sname,lg.eventtype,lg.time,lg.creationtime FROM 
			(select * from
			(select m.id,m.eventtype,m.time,m.creationtime,m.addr,m.eventno,m.triggerid,c.cardno,ROW_NUMBER() OVER(ORDER BY m.id) AS RowNo from acscon_ioeventlog_m{0} m
			INNER JOIN acscon_card c ON c.cardno = m.eventvalue  where m.time>\'{1}\' and m.time <=\'{2}\') as record
			where  RowNo >= {3} and RowNo<= {4}) as lg
			INNER JOIN acscon_realnode rn on rn.addr=lg.addr
			INNER JOIN acscon_ioevent ie on  rn.iotypeid = ie.iotypeid AND ie.eventno=lg.eventno
			left JOIN acscon_user u ON Convert(varchar(36),u.id) = lg.triggerid
        '''.format(cur_month,sync_time_beg,sync_time_end,(pgindex-1)*pgsize+1,pgindex*pgsize)
        org_cursor.execute(sql)
        # 一次性获取所有数据
        rows = org_cursor.fetchall()
        if len(rows) ==0:
            break
        for row in rows:
            # 凭证类型映射转换
            t = 0
            if row[3]=='指纹开门':
                t=1
            elif row[3]=='人脸开门':
                t=5
            # 判断是否已经插入过
            r = checkAttExist(certi_type[t],row[2],row[5],time2unix(row[8]),tid,row[9])
            if  r is not None:
                continue
            # 新增记录
            create_time = row[9].strftime("%Y-%m-%d %H:%M:%S")
            sql='insert into att_sync(certificate_type,certificate_data,address,clock_time,tenant_id,create_time) values({0},\'{1}\',\'{2}\',{3},\'{4}\',\'{5}\')'.format(certi_type[t],row[2],row[5],time2unix(row[8]),tid,create_time)
            att_cursor.execute(sql)
            att_conn.commit()
            sync_count = sync_count +1
        #继续取下一批数据
        pgindex = pgindex+1
    print('新增考勤记录:{0}\r\n'.format(sync_count))



if __name__ == "__main__":
    init()
    # 是否同步人员部门考勤点数据
    if sync_type=="0":
        sync_department()
        sync_user()
        sync_point()
    # 同步考勤记录
    sync_att_data()
    fini()

