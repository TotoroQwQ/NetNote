""" 
依赖安装：
pip install flask
pip install flask_docs
pip install logging
pip install concurrent_log_handler
pip install requests

如果开启了tokenauth
pip install flask_httpauth
pip install itsdangerous

如果使用yaml
pip install pyyaml

数据库依赖选装：
pip install pymysql
pip install pymssql
pip install elasticsearch
pip install redis
"""

import time
import json
import datetime
import random as mock
from flask import Flask, request, Blueprint
import requests
import APITemplate as API
from APITemplate import app, logger, YAMLCONFIG as config
from flask_docs import ApiDoc

API.handlerError()  # 处理404等错误
tokenAuth = API.getTokenAuth()  # token

# 开启api在线文档，地址/docs/api
ApiDoc(app, title="联想丝路数据对接", version="1.0.0")
API.readConfigFromYaml()
# 定义蓝图
Panaroma = Blueprint('Panaroma', __name__)  # 外观全景
BuildDevice = Blueprint('BuildDevice', __name__)  # 楼宇设备
Security = Blueprint('Security', __name__)  # 综合安防
InfoDevice = Blueprint('InfoDevice', __name__)  # 信息设施
Comm = Blueprint('Comm', __name__)  # 信息设施

###################### 全局配置 ############################

yun_saftop_url = 'https://yun.saftop.cn'
yun_saftop_user = {'username': "saftop", 'password': "b0757079adfef9d20bee2d570ea9c1a1"}
yun_saftop_token_time_lag = 30  # token 刷新时间间隔 min

time_format = "%Y-%m-%d %H:%M:%S"

##################### 内部方法调用 ############################

# region 连接云平台

last_refresh_token_time = 0  # 上次刷新token的时间
yun_saftop_token = ''  # 云平台的token
yun_saftop_isLogin = False


def getTokenFromYunSaftop():
    global yun_saftop_isLogin, last_refresh_token_time, yun_saftop_token
    response = None

    if time.time() - last_refresh_token_time > yun_saftop_token_time_lag * 60:
        if yun_saftop_isLogin:
            url = yun_saftop_url + '/jwt/refresh'
            response = requests.post(url, json={'access-token:{}'.format(yun_saftop_token)})

        else:
            url = yun_saftop_url + '/jwt/token'
            response = requests.post(url, json=yun_saftop_user)

        content = json.loads(response.text)
        if content['code'] == 0:
            yun_saftop_token = content['data']['token']
            yun_saftop_isLogin = True
            last_refresh_token_time = time.time()
        else:
            yun_saftop_token = ''
            yun_saftop_isLogin = False
    return yun_saftop_token


# endregion

# region Mock Data

profs = ['外观全景', '楼宇设备', '综合安防', '信息设施']
subProfs = ['专业1', '专业2', '专业3', '专业4', '专业5', '专业6']
areas = ['A楼', 'B楼', '商业裙楼']
systems = ['系统1', '系统2', '系统3', '系统4', '系统5']


def checkMapid(mapid):
    """ 检查地图id参数是否正确 """
    if mapid not in (None, ''):
        return True
    else:
        return False


def analyseMapMock():
    """ 模拟地图信息数据 """
    professionNum = mock.randint(1, 20)
    equipmentNum = mock.randint(professionNum * 2, professionNum * 4)
    data = {"professionNum": professionNum, "equipmentNum": equipmentNum, "aCellNum": mock.randint(1, 40), "bCellNum": mock.randint(1, 24), "shopCellNum": mock.randint(1, 20)}
    return data


def lastMonthVisitor():
    """ 近一个月的客流量统计 """
    todayNum = 0
    dataList = []
    delta = datetime.timedelta(1)
    day = datetime.datetime.now()
    dayDiff = 30
    while (dayDiff > 0):
        visitorNum = mock.randint(800, 1300)
        if day.weekday() in (0, 6):  # 如果是周末，数据减400
            visitorNum -= 400
        if dayDiff == 30:
            todayNum = visitorNum
        data = {"x": day.strftime('%m-%d'), "y": visitorNum}
        day -= delta
        dayDiff -= 1
        dataList.append(data)
    return [dataList, todayNum]


def visitorMock():
    """ 客流量分析数据 """
    dataList = lastMonthVisitor()
    data = {"today": dataList[1], "temporary": mock.randint(0, dataList[1]), "failure": mock.randint(0, dataList[1]), "start_time": "8:40", "end_time": "9:30", "list": dataList[0]}
    return data


def inoutMock():
    result = {"turnoverlist": [], "accesslist": []}
    for index in range(25):
        data1 = {'x': index, 'y1': mock.randint(30, 100), 'y2': mock.randint(30, 100)}
        data2 = {'x': index, 'y1': mock.randint(30, 100), 'y2': mock.randint(30, 100)}
        result['turnoverlist'].append(data1)
        result['accesslist'].append(data2)
    return result


def carportMock():
    """ 停车位数据模拟 """
    total = 2000
    empty_carport = mock.randint(0, total)
    data = {"total_carport": total, "empty_carport": empty_carport, "occupy_carport": total - empty_carport}
    return data


def energyMock():
    """ 能源统计模拟数据 """
    total_water = 0
    total_elec = 0
    day = datetime.datetime.now()
    monthList = []
    for month in range(1, day.month + 1):
        water = mock.randint(2000, 5000)
        elec = mock.randint(3000, 8000)
        total_elec += elec
        total_water += water
        monthData = {"x": month, "y1": water, "y2": elec}
        monthList.append(monthData)
    data = {"water_total": total_water, "electricity_total": total_elec, "list": monthList}
    return data


def sysEnergyMock():
    day = datetime.datetime.now()
    waterList = []
    elecList = []
    for month in range(1, day.month + 1):
        for sys in systems:
            water = {'x': month, 'type': sys, 'y': mock.randint(200, 400)}
            elec = {'x': month, 'type': sys, 'y': mock.randint(200, 400)}
            waterList.append(water)
            elecList.append(elec)

    result = {"waterList": waterList, "electricList": elecList}
    return result


def topSysEnergyDetailMock():
    dataList = []
    begin = datetime.date(2021, 1, 1)
    end = datetime.date(2021, datetime.datetime.now().month, datetime.datetime.now().day)
    d = begin
    delta = datetime.timedelta(days=1)
    while d <= end:
        for sys in systems:
            data = {'x': d.strftime("%m-%d"), 'type': sys, 'y1': mock.randint(200, 600), 'y2': mock.randint(200, 600)}
            dataList.append(data)
        d += delta
    result = {'list': dataList}
    return result


def getLiveAlarm(pageindex=1, pagesize=20, prof=None, area=None):
    """ 获取实时报警数据 
        @pageIndex: 数据页数
        @pageSize: 数量
        @prof: 专业
        @area: 区域
    """
    token = getTokenFromYunSaftop()
    if token == '':
        return -1
    else:
        url = yun_saftop_url + '/api/alarm?page={0}&&limit={1}'.format(pageindex, pagesize)
        url += '' if prof is None else ''


def getLiveAlarmMock(pageindex=1, pagesize=20, prof=None, area=None):
    """ 获取实时报警数据 
        @pageIndex: 数据页数
        @pageSize: 数量
        @prof: 专业
        @area: 区域
    """
    start = time.time() - 24 * 60 * 60
    end = time.time()
    levelDesc = ['一级', '二级', '三级', '四级', '五级', '六级', '七级', '八级']
    equi = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    dataList = []
    for index in range(pagesize):
        data = {
            "level": mock.choice(levelDesc),
            "equipmentName": "设备" + mock.choice(equi),
            "title": "这里是轮播报警信息，这里是轮播",
            "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mock.uniform(start, end)))
        }
        dataList.append(data)
    return dataList


def listMock(profs):
    dataList = []
    total = 0
    for item in profs:
        randomNum = mock.randint(0, 100)
        total += randomNum
        data = {"x": item, "y": randomNum}
        dataList.append(data)

    return dataList, total


def getAlarmMock(prof=None, area=None):
    """ 获取实时报警数据 
        @prof: 专业
        @area: 区域
    """

    data = {}
    if prof is None:
        data = listMock(profs)
    elif prof in profs:
        data = listMock(subProfs)
    else:
        API.__ReturnErrorMsg(-1, '参数错误')
    result = {"warning_total": data[1], "untreated_total": mock.randint(0, data[1]), "list": data[0]}
    return result


def getDevstat(area=None, isdetail=True):
    """ 获取设备状态 
        @area: 区域
    """
    data = {}
    datalist = listMock(profs)
    normal = mock.randint(0, datalist[1])
    alarm = mock.randint(0, datalist[1] - normal)
    offline = mock.randint(0, datalist[1] - normal - alarm)
    if isdetail:
        data = {"total": datalist[1], "normal": normal, "offline": offline, "alarm": alarm, "list": datalist[0]}
    else:
        data = {"total": datalist[1], "normal": normal, "offline": offline, "alarm": alarm}
    return data


def getOrderMock():
    """ 近一个月的工单统计 """
    todayNum = 0
    areaOrderList = {}

    dataList = []
    delta = datetime.timedelta(1)
    day = datetime.datetime.now()
    dayDiff = 30
    while (dayDiff > 0):
        for area in areas:
            if area not in areaOrderList.keys():
                areaOrderList[area] = 0

            orderNum = mock.randint(50, 200)
            areaOrderList[area] += orderNum
            if day.weekday() in (0, 6):  # 如果是周末，数据减400
                orderNum -= 30
            if dayDiff == 30:
                todayNum += orderNum
            data = {"x": day.strftime('%m-%d'), "y": orderNum, 's': area}
            dataList.append(data)
        day -= delta
        dayDiff -= 1
    result = {"today": todayNum, "accomplishRate": mock.randint(50, 90), "aWrokerNum": areaOrderList['A楼'], "bWrokerNum": areaOrderList['B楼'], "shopWrokerNum": areaOrderList['商业裙楼'], "list": dataList}
    return result


def getPatrolMock():
    total = mock.randint(500, 1000)
    untreated = mock.randint(0, total)
    data = {"total": total, "untreated": untreated, "processed": total - untreated}
    return data


def getPBXStatMock():
    total = 100
    online = mock.randint(0, total)
    normal = mock.randint(0, online)
    data = {
        "onlineStatis": {
            "online": online,
            "offline": total - online,
            "onlineRate": online,
        },
        "interchangerStatis": {
            "normal": normal,
            "break": total - normal,
            "normalRate": normal,
        }
    }
    return data


def getPBXRunStatMock():
    total = 100
    cpuNum = mock.randint(0, total)
    memoNum = mock.randint(0, total)
    data = {
        "cpuNum": cpuNum,
        "cpuRate": cpuNum,
        "memoNum": memoNum,
        "memoRate": memoNum,
    }
    return data


def getServerStatMock():
    total = 100
    onlineNum = mock.randint(0, total)
    cpuNum = mock.randint(0, onlineNum)
    memoNum = mock.randint(0, onlineNum)
    data = {
        "cpuNum": cpuNum,
        "memoNum": memoNum,
        "offlineNum": total - onlineNum,
    }
    return data


def getUPSStatMock():
    data = {"alist": '数据a', "blist": '数据b', "shoplist": '数据c'}
    # devs = ['数据a', '数据b', '数据c']
    for item in data.keys():
        # for dev in devs:
        dev=data[item]
        data[item] = {
            'name': dev,
            'workPattern': dev,
            'inputVolt': dev,
            'outputVolt': dev,
            'battery': dev,
            'remainTime': dev,
        }

    return data


def getVideoPlayStatMock():
    data = {"alist": [], "blist": [], "shoplist": []}
    total = 100
    for item in data.keys():
        online = mock.randint(0, total)

        data[item] = {
            "online": online,
            "offline": total - online,
            "onlineRate": online,
        }

    return data


# endregion

####################对外接口###################################

# region 全局变量
PageSize = 50  # 默认的每页数量
PageIndex = 1  # 默认的页数
# endregion

# region Comm 通用接口


@Comm.route('/mapinfo/<string:mapid>')
@API.create_doc_form_yaml('mapinfo')
# @ApiDoc.change_doc({})
def mapInfo(mapid):
    """ 1. 地图信息"""

    mapinfo = API.APITemplate()
    if checkMapid(mapid):
        mapinfo.data = analyseMapMock()
        return mapinfo.formatJson()
    else:
        API.__ReturnErrorMsg(-1, "参数错误")


@Comm.route('/visitorstatistics')
@API.create_doc_form_yaml()
def visitorStats():
    """ 2. 当日客流量统计"""
    visApi = API.APITemplate()
    visApi.data = visitorMock()
    return visApi.formatJson()


@Comm.route('/carport')
@API.create_doc_form_yaml()
def carPort():
    """ 3. 停车位占用情况 """
    carPortApi = API.APITemplate()
    carPortApi.data = carportMock()
    return carPortApi.formatJson()


@Comm.route('/energystatistics')
@API.create_doc_form_yaml()
def energyStatistics():
    """ 4. 近一年能耗统计
    """
    energyapi = API.APITemplate()
    energyapi.data = energyMock()
    return energyapi.formatJson()


@Comm.route('/livealarms')
@API.create_doc_form_yaml()
def liveAlarms():
    """ 5. 设备实时告警列表
    """
    livealarmApi = API.APITemplate()
    livealarmApi.data = getLiveAlarmMock(1, 20)
    return livealarmApi.formatJson()



@Comm.route('/alarms')
@API.create_doc_form_yaml()
def alarms():
    """ 6. 告警统计
    """
    alarmApi = API.APITemplate()
    alarmApi.data = getAlarmMock()
    return alarmApi.formatJson()


@Comm.route('/devicestate')
@API.create_doc_form_yaml()
def deviceState():
    """ 7. 设备状态统计
    """
    devApi = API.APITemplate()
    devApi.data = getDevstat()
    return devApi.formatJson()

#endregion

# region Panaroma 外观全景

@Panaroma.route('/workorder')
@API.create_doc_form_yaml()
def workOrder():
    """ 1. 工单统计
    """
    orderApi = API.APITemplate()
    orderApi.data = getOrderMock()
    return orderApi.formatJson()


# endregion

# region BuildDevice 楼宇设备

@BuildDevice.route('/sysenergy')
@API.create_doc_form_yaml()
def sysEnergyStatistics():
    """ 1. 近一年能耗占比
    """
    sysenergyapi = API.APITemplate()
    sysenergyapi.data = sysEnergyMock()
    return sysenergyapi.formatJson()


@BuildDevice.route('/topsysenergy')
@API.create_doc_form_yaml()
def topSysEnergyDetail():
    """ 2. 近一年占比最高的两个专业系统能耗趋势
    """
    topapi = API.APITemplate()
    topapi.data = topSysEnergyDetailMock()
    return topapi.formatJson()


@BuildDevice.route('/devicelivestate')
@API.create_doc_form_yaml()
def deviceLiveState():
    """ 3. 设备实时状态统计
    """
    devApi = API.APITemplate()
    devApi.data = getDevstat(isdetail=False)
    return devApi.formatJson()

# endregion

# region Security 综合安防

@Security.route('/inout')
@API.create_doc_form_yaml()
def inout(area=None):
    """ 1. 24小时人流量分析
    """
    inoutApi = API.APITemplate()
    inoutApi.data = inoutMock()
    return inoutApi.formatJson()


@Security.route('/patrolsys')
@API.create_doc_form_yaml()
def patrolSys():
    """ 2. 巡更情况统计
    """
    patrolApi = API.APITemplate()
    patrolApi.data = getPatrolMock()
    return patrolApi.formatJson()


# endregion

# region InfoDevice 信息设施


@InfoDevice.route('/PBXstat')
@API.create_doc_form_yaml()
# @ApiDoc.change_doc({'_req': FormatReq.format('/InfoDevice/PBXstat'), '_resp': FormatResp, '_args': FormatArgs.format(ArgsNone)})
def PBXStat():
    """ 1. 交换机在离线统计
    """
    PBX = API.APITemplate()
    PBX.data = getPBXStatMock()
    return PBX.formatJson()


@InfoDevice.route('/PBXrunstat')
@API.create_doc_form_yaml()
# @ApiDoc.change_doc({'_req': FormatReq.format('/InfoDevice/PBXrunstat'), '_resp': FormatResp, '_args': FormatArgs.format(ArgsNone)})
def PBXRunStat():
    """ 2. 交换机状态统计
    """
    PBX = API.APITemplate()
    PBX.data = getPBXRunStatMock()
    return PBX.formatJson()


@InfoDevice.route('/serverstat')
@API.create_doc_form_yaml()
# @ApiDoc.change_doc({'_req': FormatReq.format('/InfoDevice/serverstat'), '_resp': FormatResp, '_args': FormatArgs.format(ArgsNone)})
def serverStat():
    """ 3. 服务器状态统计
    """
    server = API.APITemplate()
    server.data = getServerStatMock()
    return server.formatJson()


@InfoDevice.route('/upsstat')
@API.create_doc_form_yaml()
# @ApiDoc.change_doc({'_req': FormatReq.format('/InfoDevice/upsstat'), '_resp': FormatResp, '_args': FormatArgs.format(ArgsNone)})
def UPSStat():
    """ 4. UPS实时状态
    """
    UPS = API.APITemplate()
    UPS.data = getUPSStatMock()
    return UPS.formatJson()


@InfoDevice.route('/videoplay')
@API.create_doc_form_yaml()
# @ApiDoc.change_doc({'_req': FormatReq.format('/InfoDevice/videoplay'), '_resp': FormatResp, '_args': FormatArgs.format(ArgsNone)})
def videoPlayStat():
    """ 5. 播放器在离线统计
    """
    videoPlay = API.APITemplate()
    videoPlay.data = getVideoPlayStatMock()
    return videoPlay.formatJson()


# endregion

if __name__ == "__main__":
    # 解决flask中文乱码的问题，将json数据内的中文正常显示
    app.config['JSON_AS_ASCII'] = False
    # 开启日志
    API.openLogger('debug')
    # 注册蓝图
    # API.registerBlueprint([Panaroma, BuildDevice, InfoDevice], ApiDoc)
    API.registerBlueprint({Panaroma: "2. 外观全景", BuildDevice: "3. 楼宇设施", Security: "4. 综合安防", InfoDevice: "5. 信息设施", Comm: '1. 通用接口'}, ApiDoc)
    app.run(debug=True)
