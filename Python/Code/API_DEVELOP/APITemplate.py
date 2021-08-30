"""
descr: APITemplate development using falsk_restful
author: TotoroQwQ
environment: python3
date: 2021/7/17
"""

import json
import re, os
import logging
import requests
import datetime
import functools
from flask import current_app, Flask, request

app = Flask(__name__)

# 解决flask中文乱码的问题，将json数据内的中文正常显示
app.config['JSON_AS_ASCII'] = False
# yaml配置对象
YAMLCONFIG = None


def getTokenAuth():
    """  
    开启token生成
    开启token验证
    支持查看token生成记录
    """
    try:
        from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
        from flask_httpauth import HTTPTokenAuth
        import os
    except ImportError:
        logger.error('开启token需要安装itsdangerous，请使用pip install itsdangerous')
        return

    httpTokenAuth = HTTPTokenAuth(scheme="token")
    __TokenRecords = {"records": []}
    __Users = []
    __Key = 'saftop key'
    __serializer = Serializer(__Key)
    __dir = './data'
    __tokenRecordFile = __dir + '/data.json'

    @httpTokenAuth.verify_token
    def verify_token(token):
        global __Users  # 这里不能global __serializer,引用反而为None，报错，原因暂时未知
        try:
            data = __serializer.loads(token)
        except Exception as e:
            logger.error('token验证失败')
            logger.error(e)
            return False
        if 'user' in data:
            user = data['user']
            if user in __Users:
                return True
            # g.user = data['user']
        return False

    def loadRecords():
        """ 从文件读取以前保存得token数据 """
        global __TokenRecords, __Users
        try:
            if os.path.exists(__tokenRecordFile):
                rfile = open(__tokenRecordFile, "r")
                result = rfile.read()  # 这里必须用变量保存一下，直接json。loads会解析不了，原因未知
                __TokenRecords = json.loads(result)
                __Users = [item['user'] for item in __TokenRecords["records"]]
        except Exception as e:
            logger.error(e)
            logger.error("加载历史token失败,历史token不可用")

    loadRecords()

    @httpTokenAuth.error_handler
    def error_handler():
        return __ReturnErrorMsg(403, "token验证错误")

    def saveTokenRecord(user=None, timeLimit=None):
        """ 将生成Token的记录保存，但不记录Token本身[{'role':user,'timelimit':1}] """
        global __TokenRecords, __Users
        if user is not None and timeLimit is not None:
            tokenRecordItem = {}
            tokenRecordItem['user'] = user
            tokenRecordItem['timelimit'] = timeLimit
            tokenRecordItem['creationtime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            __TokenRecords["records"].append(tokenRecordItem)
            __Users.append(user)

        if not os.path.exists(__dir):
            os.makedirs(__dir)
        rfile = open(__tokenRecordFile, "w")
        rfile.write(str(__TokenRecords).replace("'", '"'))

    @app.route('/gentoken/<username>/<password>')
    def genToken(username, password):
        global __Users, __serializer  # 这里不用引用__key，引用会报错，原因未知
        try:
            if username == 'saftop' and password == 'saftop':
                if 'user' in request.args.keys() and 'timelimit' in request.args.keys():
                    user = request.args['user']  # Token描述，做什么用的，谁用的之类
                    timeLimit = request.args['timelimit']  # Token 时间限制,单位H

                    if user in __Users:
                        return 'please rename user'
                    if timeLimit == 'F':
                        __serializer = Serializer(__Key)

                    else:
                        try:
                            timeLimit = float(timeLimit)
                            timeLimit = int(timeLimit * 60 * 60)
                            __serializer = Serializer(__Key, expires_in=timeLimit)
                        except Exception as e:
                            logger.error(e)
                            return ''
                    token = __serializer.dumps({'user': user})
                    saveTokenRecord(user, timeLimit)
                    return token
        except Exception as e:
            logger.error('生成Token失败，参数错误')
            logger.error(e)
            return '生成Token失败，参数错误'
        return ''

    @app.route('/show_user')
    def showUser():
        global __Users
        return str(__Users)

    @app.route('/show_userdetail')
    def showUserDetail():
        global __TokenRecords
        return __TokenRecords

    @app.route('/deluser/<user>')
    def delUser(user):
        global __Users, __TokenRecords
        try:
            if user in __Users:
                __Users.remove(user)
                for item in __TokenRecords["records"]:
                    if item['user'] == str(user):
                        __TokenRecords["records"].remove(item)
                        break
                saveTokenRecord()
                return 'success'
            return 'false'
        except Exception as e:
            logger.error(e)
            return 'false'

    return httpTokenAuth


# region 日志相关
logger = logging.getLogger('invoke_api')  # 名称自定义就行，生成日志对象实例
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter('%(asctime)s -- %(levelname)s -- [%(filename)s->%(funcName)s->%(lineno)d] -- %(message)s'))
logger.addHandler(handler)


def openLogger(level=None, log_name=None, flask_log_level=None, size=None):
    """
    开启日志，使用了多进程安全的concurrent_log_handler.ConcurrentRotatingFileHandler
    替代了logging.TimeRotatingFileHandler,缺点是无法进行时间片分割。
        @level:APITemplate的日志打印级别,默认logging.ERROR
        @log_name:保存的日志文件称,默认invoke_api.log
        @flask_log_level:flask内部的日志级别，默认logging.INFO
        @size: 每个日志的大小
    """
    try:
        from concurrent_log_handler import ConcurrentRotatingFileHandler
    except ImportError:
        logger.error('开启日志需要安装concurrent_log_handler,请使用 pip install concurrent_log_handler')
        return
    if level is None:
        level = 'error'
    if log_name is None:
        log_name = 'invoke_api.log'
    if flask_log_level is None:
        flask_log_level = logging.INFO
    if size is None:
        size = 10 * 1024 * 1024  # 10M
    try:
        # 找到flask内部日志，这个的设置不用动了
        flask_logger = logging.getLogger('werkzeug')
        flask_handler = ConcurrentRotatingFileHandler(filename=log_name, maxBytes=size, backupCount=1024, encoding='utf-8')
        flask_logger.addHandler(flask_handler)
        flask_logger.setLevel(flask_log_level)

        # 设置本地日志的格式
        if level.lower() == 'debug':
            logger.setLevel(logging.DEBUG)
        if level.lower() == 'info':
            logger.setLevel(logging.INFO)
        if level.lower() == 'error':
            logger.setLevel(logging.ERROR)

        local_handler = ConcurrentRotatingFileHandler(filename=log_name, maxBytes=size, backupCount=1024, encoding='utf-8')
        local_handler.setFormatter(
            logging.Formatter('%(asctime)s -- %(levelname)s -- [%(filename)s->%(funcName)s->%(lineno)d] -- %(message)s'))
        logger.addHandler(local_handler)
    except Exception as e:
        logger.error('日志开启失败:')
        logger.error(e)


# endregion

# region 蓝图及文档相关


class Dic2Ob(dict):
    """ 将字典转成对象 """
    def __getattr__(self, key):
        value = self.get(key)
        return Dic2Ob(value) if isinstance(value, dict) else value

    def __setattr__(self, key, value):
        self[key] = value


def readConfigFromYaml(path='config.yml'):
    """ 从yaml里面读取配置 """
    global YAMLCONFIG
    try:
        import yaml
    except ImportError as e:
        logger.error(e)
        logger.error("读取yaml文件需要安装pyyaml插件,请使用pip install pyyaml")
        return
    if os.path.exists(path):
        doc = open(path, 'r', encoding='utf-8')
        doc_dict = yaml.load(doc)
        YAMLCONFIG = Dic2Ob(doc_dict)
    else:
        logger.error("读取yaml文件失败，请检查文件路径")


def registerBlueprint(bluePrintList, ApiDoc=None):
    """ 
    flask配置文档成员，并注册蓝图 
        @app: flask对象
        @bluePrintList：可以将蓝图对象放到list/tuple里面进行注册。也支持通过dict类型重命名Flask_Docs文档里面的树节点：{BluePrint_Object:"rename"}
    """
    nameList = []
    if type(bluePrintList) in (list, tuple):
        for item in bluePrintList:
            app.register_blueprint(item, url_prefix="/{}".format(item.name))
            nameList.append(item.name)
        app.config["API_DOC_MEMBER"] = nameList
    elif type(bluePrintList) == dict:
        app.config.setdefault("API_DOC_MEMBER_RENAME", [])
        for key, value in bluePrintList.items():
            app.register_blueprint(key, url_prefix="/{}".format(key.name))
            nameList.append(key.name)
            app.config["API_DOC_MEMBER_RENAME"].append(value)
        app.config["API_DOC_MEMBER"] = nameList
        if ApiDoc is not None:
            ApiDoc.get_api_data = get_api_data
    else:
        logger.error('registerBlueprint调用失败，参数类型不支持')


# endregion


# region 401,402,403,404等异常处理
def handlerError():
    try:
        from werkzeug import exceptions
    except ImportError as e:
        logger.error(e)
        return
    try:

        @app.errorhandler(Exception)
        def errorhandler(e):
            logger.error(e)
            if isinstance(e, exceptions.HTTPException):
                return __ReturnErrorMsg(e.code, e.description)
            else:
                return __ReturnErrorMsg()
    except Exception as e:
        logger.error(e)
        return __ReturnErrorMsg()


def __ReturnErrorMsg(code=None, errorMsg=None):
    if code is None:
        code = 500
    if errorMsg is None:
        errorMsg = "访问错误"
    api = APITemplate()
    api.setError(retcode=code, msg=errorMsg)
    return api.formatJson()


# endregion

redispool = None


# 模板类，主要是封装了一些数据库的连接，结果集的解析
class APITemplate:
    """ API模板类 """
    def __init__(self):
        self.code = 0
        self.msg = "success"
        self.data = {}
        # namelist只做存储和转化json使用
        # 不一定用得上，现在所有连接都默认使用脚本查询的内部字段
        self.nameList = []
        # 各种数据库的连接，形成统一格式
        self.conn_ms = None
        self.conn_es = None
        self.conn_my = None
        self.conn_influx = None
        self.conn_redis = None

    def setMSConn(self, host, user, password, database):
        """
        统一的数据库连接：设置MSSQL数据库连接：
            @host:   ip+port
            @user:   username
            @password:  password
            @database:  database
        """
        try:
            import pymssql
        except ImportError:
            logger.error("使用MSSQL需要安装pymssql,请使用命令'pip install pymssql'")
        else:
            try:
                self.conn_ms = pymssql.connect(host=host, user=user, password=password, database=database)
            except ConnectionError:
                logger.error("MSSQL连接失败")

    def setMySqlConn(self, host, user, password, database):
        """
        统一的数据库连接：设置MySQL数据库连接：
            @host:   ip+port
            @user:   username
            @password:  password
            @database:  database
        """
        try:
            import pymysql
        except ImportError:
            logger.error("使用MySQL需要安装pymysql,请使用命令'pip install pymysql'")
        else:
            try:
                iplist = host.split(':')
                self.conn_my = pymysql.connect(host=iplist[0],
                                               port=int(iplist[1]),
                                               user=user,
                                               password=password,
                                               database=database)
            except ConnectionError:
                logger.error("MSSQL连接失败")

    def setESConn(self, host, user, password):
        """
        统一的数据库连接：设置ES数据库连接：
            @host:   ip+port
            @user:   username
            @password:  password
        """
        try:
            from elasticsearch import Elasticsearch
        except ImportError:
            logger.error("使用ES需要安装elasticsearch,请使用命令'pip install elasticsearch'")
        else:
            try:
                self.conn_es = Elasticsearch(hosts=host, http_auth=(user, password))
            except ConnectionError:
                logger.error("ES连接失败")

    def setRedisConn(self, host, user=None, password=None):
        """
        统一的数据库连接：设置Redis数据库连接：
            @host:   ip+port
            @user:   username
            @password:  password
        """
        global redispool
        try:
            import redis
        except ImportError:
            logger.error("使用redis需要安装redis库,请使用命令'pip install redis'")
        else:
            try:
                if redispool is None:
                    iplist = host.split(':')
                    redispool = redis.ConnectionPool(host=iplist[0], port=iplist[1], password=password)
                self.conn_redis = redis.Redis(connection_pool=redispool)
            except ConnectionError:
                logger.error("Redis连接失败")

    def setInfluxdbConn(self, host, user=None, password=None, database=None):
        """
        统一的数据库连接：设置influxdb数据库连接：
            @host:   ip+port
            @user:   暂时没有用上，不用传
            @password:  暂时没有用上，不用传
            @database:  指定查询得数据库
        """
        if database is None:
            logger.error('influxdb查询没有指定数据库')
            return
        self.conn_influx = 'http://{}/query?db={}'.format(host, database)
        logger.debug(self.conn_influx)

    def setError(self, retcode=None, msg=None):
        """ 
        定义错误类型 
            @retcode: 返回码
            @msg: 返回信息
        """
        if retcode is None or msg is None:
            retcode = 500
            msg = 'setError方法调用错误'
        else:
            self.code = retcode
            self.msg = msg
        self.data = {}

    def formatJson(self):
        """ 以一个标准的网络API格式返回json """
        return {"code": self.code, "msg": self.msg, "data": self.data}

    def queryFromMSSQL(self, sql, conn=None, title=None):
        """
        使用sqlserver做查询
        参数 ：
            @conn：数据库连接；
            @sql：脚本内容；
            @title：多行数据的一个总名称
        """
        try:
            if self.conn_ms is None:
                self.conn_ms = conn
            # 使用MSSQLi查询脚本sql
            ms = self.conn_ms.cursor()
            ms.execute(sql)
            result = ms.fetchall()

            # 如果没有重命名，默认按照脚本语句里面的名称
            if len(self.nameList) == 0:
                col = ms.description
                for i in range(len(col)):
                    self.nameList.append(col[i][0])

            ms.close()
            self.parseToJsonObject(result, title)
        except Exception as e:
            logger.error("查询错误：可能是脚本错误或连接错误，导致查询失败")
            logger.error(e)
            self.setError(11, "查询错误")
        # return self.data

    def queryFromMySQL(self, sql, conn=None, title=None):
        """
        使用sqlserver做查询
        参数 ：
            @conn：数据库连接；
            @sql：脚本内容；
            @title：多行数据的一个总名称
        """
        try:
            if self.conn_my is None:
                self.conn_my = conn
            # 使用MSSQLi查询脚本sql
            my = self.conn_my.cursor()
            my.execute(sql)
            result = my.fetchall()

            # 如果没有重命名，默认按照脚本语句里面的名称
            if len(self.nameList) == 0:
                col = my.description
                for i in range(len(col)):
                    self.nameList.append(col[i][0])

            my.close()
            self.parseToJsonObject(result, title)
        except Exception as e:
            logger.error("查询错误：可能是脚本错误或连接错误，导致查询失败")
            logger.error(e)
            self.setError(11, "查询错误")

    def queryFromInfluxDB(self, sql, posturl=None, title=None):
        """
        使用influxdb做查询
        参数 ：
            @posturl：数据库连接；
            @sql：脚本内容；
            @title：多行数据的一个总名称
        """
        try:
            # 使用influxdb查询脚本sql
            logger.debug(posturl)
            if posturl is not None:
                self.conn_influx = posturl
            if self.conn_influx is None:
                logger.error('查询失败，连接到influxdb失败')
                return
            logger.debug(self.conn_influx)
            response = json.loads(requests.post(self.conn_influx, data=sql).content)
            data = response['results'][0]['series'][0]
            self.nameList = data['columns']
            values = data['values']
            self.parseToJsonObject(values, title)
        except Exception as e:
            logger.error("查询错误：可能是脚本错误或连接错误，导致查询失败")
            logger.error(e)
            self.setError(11, "查询错误")

    def queryFromES(self, body=None, conn=None, title=None, index=None, doc_type=None, params=None, headers=None):
        """
        使用es做查询
        参数 ：
            @body:  查询条件
            @conn： es的连接，也可以通过setESConn后不传该值
            @title: 多行数据的一个总标题
            @index：需要查询的es的index
            @doc_type: 需要查询的es的doc_type
            @param: es查询的默认参数
            @headers: es查询的默认参数
        """
        try:
            if self.conn_es is None:
                self.conn_es = conn
            response = self.conn_es.search(index=index, body=body, doc_type=doc_type, params=params, headers=headers)
            data = response['hits']['hits']

            if len(data) > 1 and title is None:
                logger.error("内部调用错误：查询结果有多行数据，但是没有设置标题，请检查执行方法")
                self.setError(12, "内部调用错误")
                return

            results = []
            for item in data:
                results.append(item['_source'])
            jsonStr = json.dumps(results, ensure_ascii=False)
            if title is not None:
                jsonStr = "{" + "\"{0}\":{1}".format(title, jsonStr) + "}"
            else:
                jsonStr = jsonStr[1:len(jsonStr) - 1]
            self.addJson(json.loads(jsonStr))

        except Exception as e:
            logger.error("查询错误：可能是脚本错误或连接错误，导致查询失败")
            logger.error(e)
            self.setError(11, "查询错误")

    def queryFromRedis(self, keys, conn=None, title=None):
        """
        请求redis数据库：
        参数：
            @keys: [key1,key2]形式，list格式，传一个或多个key值
            @conn: redis连接，建议使用setRedisConn，忽略这个参数
            @title: 如果有list，结果是一个json数组形式，没有list，结果是一个json对象形式
        """
        try:
            vlist = self.conn_redis.mget(keys)
            if self.nameList is None or len(self.nameList) == 0 or len(self.nameList != len(vlist)):
                self.nameList = keys

            if title is None:
                result = {}
                for index in range(len(vlist)):
                    result[self.nameList[index]] = int(vlist[index]) if type(vlist[index]) == bytes else vlist[index]
                self.addJson(json.loads(str(result).replace("'", '"')))
            else:
                pvalue = []
                for index in range(len(vlist)):
                    value = {}
                    value[self.nameList[index]] = int(vlist[index]) if type(vlist[index]) == bytes else vlist[index]
                    pvalue.append(value)
                self.addProperty(title, pvalue)
        except Exception as e:
            self.setError(11, '查询错误')
            logger.error('查询失败')
            logger.error(e)

    def parseToJsonObject(self, queryResult, title):
        """
        内部方法，将数据库执行后的数据转成json对象
            @queryResult:一个[[],[]]结构的数据;
            @title:多行数据的一个总名称;
        """

        if len(queryResult) == 0:
            for item in self.nameList:
                self.data[item] = ""
        else:
            # 多行无标题，定义错误4
            if len(queryResult) > 1 and title is None:
                logger.error("内部调用错误：查询结果有多行数据，但是没有设置标题，请检查执行方法")
                self.setError(12, "内部调用错误")
                return

            try:
                jsonArray = []
                for row in queryResult:
                    if len(row) != len(self.nameList):
                        logger.error("内部调用错误：nameList和查询列数需要一致")
                        self.setError(12, "内部调用错误")
                        return
                    result = {}
                    for i in range(len(row)):
                        if (type(row[i]) in (int, float)):
                            result[self.nameList[i]] = row[i]
                        else:
                            result[self.nameList[i]] = str(row[i])
                    jsonArray.append(result)

                jsonStr = json.dumps(jsonArray, ensure_ascii=False)
                if title is not None:
                    jsonStr = "{" + "\"{0}\":{1}".format(title, jsonStr) + "}"
                else:
                    jsonStr = jsonStr[1:len(jsonStr) - 1]
                self.addJson(json.loads(jsonStr))
            except Exception as e:
                logger.error("APITmplate包异常：json格式化错误")
                logger.error(e)
                self.setError(13, "APITmplate包异常")

    def addProperty(self, propName, propValue):
        """
        在当前json字符串基础上新增属性
        """
        if self.code != 0:
            return
        self.data[propName] = propValue

    def addJson(self, jsonObject):
        """
        向APITemplate.data里面合并另一个json
        """
        if (self.code != 0):
            return
        for key in jsonObject:
            self.data[key] = jsonObject[key]

    def delProperty(self, propName):
        del self.data[propName]


###############################  方法重构 ##############################
############# 一些引用的包不符合需求，自己重构的代码列在下面 ###############
""" 
ps: 文档页面的测试url无法修改的问题，在index.js里面搜索readonly:i.readonly,将第一个删除即可
"""


def get_api_data(self):
    """
    重构flask_docs里面的对应方法，支持重命名树节点
    """

    from flask_docs import logger as apidocs_log, PROJECT_NAME
    data_dict = {}

    for rule in current_app.url_map.iter_rules():
        f = str(rule).split("/")[1]
        if f not in current_app.config["API_DOC_MEMBER"]:
            continue

        # f_capitalize = f.capitalize()
        index = current_app.config["API_DOC_MEMBER"].index(f)
        f_capitalize = app.config["API_DOC_MEMBER_RENAME"][index]
        if f_capitalize not in data_dict:
            data_dict[f_capitalize] = {"children": []}

        api = {
            "name": "",
            "name_extra": "",
            "url": "",
            "method": "",
            "doc": "",
            "doc_md": "",
            "router": f_capitalize,
            "api_type": "api",
        }

        try:
            func = current_app.view_functions[rule.endpoint]

            name = self.get_api_name(func)
            url = str(rule)
            method = " ".join([r for r in rule.methods if r in self.methods_list])
            if method:
                url = "{}\t[{}]".format(url, "\t".join(method.split(" ")))

            result = filter(
                lambda x: x["name"] == name,
                data_dict[f_capitalize]["children"],
            )
            result_list = list(result)
            if len(result_list) > 0:
                result_list[0]["url"] = result_list[0]["url"] + " " + url
                result_list[0]["url"] = " ".join(list(set(result_list[0]["url"].split(" "))))
                result_list[0]["method"] = result_list[0]["method"] + \
                    " " + method
                result_list[0]["method"] = " ".join(list(set(result_list[0]["method"].split(" "))))
                raise RuntimeError

            api["url"] = url
            api["method"] = method

            doc = self.get_api_doc(func)

            (
                api["doc"],
                api["name_extra"],
                api["doc_md"],
            ) = self.get_doc_name_extra_doc_md(doc)

            if api["name_extra"] == '':
                api["name"] = name
            else:
                api["name"] = api["name_extra"]
                api["name_extra"] = name

        except Exception as e:
            apidocs_log.exception("{} error - {}".format(PROJECT_NAME, e))
        else:
            data_dict[f_capitalize]["children"].append(api)

        if data_dict[f_capitalize]["children"] == []:
            data_dict.pop(f_capitalize)
        else:
            data_dict[f_capitalize]["children"].sort(key=lambda x: x["name"])

    return data_dict


# @staticmethod
def create_doc_form_yaml(name=None):
    """ 
    通过yaml的配置自动生成api文档
        @name: yaml中method下面配置的名称，默认为方法名称
    """
    methodname = name
    # global YAMLCONFIG
    def decorator(func):
        global methodname
        # try:
        apidoc = YAMLCONFIG.apidoc
        logger.debug(apidoc)

        commargs = apidoc.args
        if methodname is None:
            methodname = func.__name__
        func_config = Dic2Ob(apidoc.method[methodname.lower()])
        logger.debug(func_config)
        if func_config is None:
            return
        apidesc = '-' if func_config.descr is None else func_config.descr
        args = '' if func_config.ownargs is None else func_config.ownargs
        for item in func_config.args:
            args += commargs[item]
        req = '' if func_config.req is None else func_config.req
        resp = 'null' if func_config.resp is None else func_config.resp
        extradescr = apidoc.extradescr if func_config.extradescr != False else ''
        doc = func.__doc__
        doc += apidoc.content.format(apidesc, args, req, resp, extradescr)

        func.__doc__ = doc
        logger.debug(func.__doc__)
        # except Exception as ex:
            # logger.error(ex)

        @functools.wraps(func)
        def decorated_function(*args, **kw):
            return func(*args, **kw)

        return decorated_function

    return decorator

