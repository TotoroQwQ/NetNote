"""
descr: APITemplate development using falsk_restful
author: TotoroQwQ
environment: python3
date: 2021/7/17
"""

import json
import re
import logging
import requests
from flask_httpauth import HTTPTokenAuth
from concurrent_log_handler import ConcurrentRotatingFileHandler

# 认证相关

""" httptoken验证 """
httpTokenAuth = HTTPTokenAuth(scheme="token")
""" 后续可以用其他方式生成 """
TOKENS = {
    "fejiasdfhu",
    "fejiuufjeh"
}


@httpTokenAuth.verify_token
def verify_token(token):
    if token in TOKENS:
        # g.current_user = token
        return True
    return False


# 日志相关
logger = logging.getLogger('invoke_api')  # 名称自定义就行，生成日志对象实例
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s -- %(levelname)s -- [%(filename)s->%(funcName)s->%(lineno)d] -- %(message)s'))
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
    if level is None:
        level = 'error'
    if log_name is None:
        log_name = 'invoke_api.log'
    if flask_log_level is None:
        flask_log_level = logging.INFO
    if size is None:
        size = 10*1024*1024  # 10M
    try:
        # 找到flask内部日志，这个的设置不用动了
        flask_logger = logging.getLogger('werkzeug')
        flask_handler = ConcurrentRotatingFileHandler(
            filename=log_name,  maxBytes=size, backupCount=1024, encoding='utf-8')
        flask_logger.addHandler(flask_handler)
        flask_logger.setLevel(flask_log_level)

        # 设置本地日志的格式
        if level.lower() == 'debug':
            logger.setLevel(logging.DEBUG)
        if level.lower() == 'info':
            logger.setLevel(logging.INFO)
        if level.lower() == 'error':
            logger.setLevel(logging.ERROR)

        local_handler = ConcurrentRotatingFileHandler(
            filename=log_name, maxBytes=size, backupCount=1024, encoding='utf-8')
        local_handler.setFormatter(logging.Formatter(
            '%(asctime)s -- %(levelname)s -- [%(filename)s->%(funcName)s->%(lineno)d] -- %(message)s'))
        logger.addHandler(local_handler)
    except Exception as e:
        logger.error('日志开启失败:')
        logger.error(e)


# API文档相关

def registerBlueprint(app, bluePrintList):
    """ flask配置文档成员，并注册蓝图 """
    nameList = []
    for item in bluePrintList:
        app.register_blueprint(item, url_prefix="/{}".format(item.name))
        nameList.append(item.name)
    app.config["API_DOC_MEMBER"] = nameList


redispool = None


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
                self.conn_ms = pymssql.connect(host=host, user=user,
                                               password=password, database=database)
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
                self.conn_my = pymysql.connect(host=iplist[0], port=int(iplist[1]), user=user,
                                               password=password, database=database)
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
            logger.error(
                "使用ES需要安装elasticsearch,请使用命令'pip install elasticsearch'")
        else:
            try:
                self.conn_es = Elasticsearch(
                    hosts=host, http_auth=(user, password))
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
            logger.error(
                "使用redis需要安装redis库,请使用命令'pip install redis'")
        else:
            try:
                if redispool is None:
                    iplist = host.split(':')
                    redispool = redis.ConnectionPool(
                        host=iplist[0], port=iplist[1], password=password)
                self.conn_redis = redis.Redis(connection_pool=redispool)
            except ConnectionError:
                logger.error("Redis连接失败")

    def setInfluxdbConn(self, host, user=None, password=None, database=None):
        """ 未实现,暂勿使用，influxdb直接使用请求 """
        if database is None:
            logger.error('influxdb查询没有指定数据库')
            return
        self.conn_influx = 'http://{}/query?db={}'.format(host, database)
        logger.debug(self.conn_influx)

    def setError(self, retcode=None, msg=None):
        """ 定义错误类型 """
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

    def queryFromInfluxDB(self, sql, posturl=None,  title=None):
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
            response = json.loads(requests.post(
                self.conn_influx, data=sql).content)
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
            response = self.conn_es.search(
                index=index, body=body, doc_type=doc_type, params=params, headers=headers)
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
                jsonStr = "{"+"\"{0}\":{1}".format(title, jsonStr)+"}"
            else:
                jsonStr = jsonStr[1:len(jsonStr)-1]
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
        """
        try:
            vlist = self.conn_redis.mget(keys)
            if self.nameList is None or len(self.nameList) == 0 or len(self.nameList != len(vlist)):
                self.nameList = keys

            if title is None:
                result = {}
                for index in range(len(vlist)):
                    result[self.nameList[index]] = int(vlist[index]) if type(
                        vlist[index]) == bytes else vlist[index]
                self.addJson(json.loads(str(result).replace("'", '"')))
            else:
                pvalue = []
                for index in range(len(vlist)):
                    value={}
                    value[self.nameList[index]] = int(vlist[index]) if type(
                        vlist[index]) == bytes else vlist[index]
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
                        if(type(row[i]) in (int, float)):
                            result[self.nameList[i]] = row[i]
                        else:
                            result[self.nameList[i]] = str(row[i])
                    jsonArray.append(result)

                jsonStr = json.dumps(jsonArray, ensure_ascii=False)
                if title is not None:
                    jsonStr = "{"+"\"{0}\":{1}".format(title, jsonStr)+"}"
                else:
                    jsonStr = jsonStr[1:len(jsonStr)-1]
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
        if(self.code != 0):
            return
        for key in jsonObject:
            self.data[key] = jsonObject[key]

    def delProperty(self, propName):
        del self.data[propName]
