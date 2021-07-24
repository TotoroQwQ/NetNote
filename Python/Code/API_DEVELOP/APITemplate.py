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
from logging.handlers import TimedRotatingFileHandler

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
handler=logging.StreamHandler()
handler.setFormatter(logging.Formatter(
        '%(asctime)s -- %(levelname)s -- [%(filename)s->%(funcName)s->%(lineno)d] -- %(message)s'))
logger.addHandler(handler)


def openLogger(level=None,log_name=None,flask_log_level=None):
    """ 
    开启日志 
        @level:APITemplate的日志打印级别,默认logging.ERROR
        @log_name:保存的日志文件称,默认invoke_api.log
        @flask_log_level:flask内部的日志级别，默认logging.INFO
    """
    if level is None:
        level=logging.ERROR
    if log_name is None:
        log_name='invoke_api.log'
    if flask_log_level is None:
        flask_log_level=logging.INFO
    try:
        # 解决两个日志在启动时，如果有同名旧日志，修改文件名称时出现的进程冲突bug
        import os
        if os.path.exists(log_name):
            log = open(log_name,"a")
            log.write('************init****************\n')

        # 找到flask内部日志，这个的设置不用动了
        flask_logger = logging.getLogger('werkzeug')
        flask_handler = TimedRotatingFileHandler(
            filename='invoke_api.log', when='midnight',
            backupCount=365, encoding='utf-8')  # 设置log名称以及新log生成时间，backcount表示保留个数
        flask_handler.suffix = '%Y-%m-%d.log'  # 过期日志的后缀
        flask_handler.extMatch = re.compile(r'^\d{4}-\d{2}-\d{2}.log')
        flask_logger.addHandler(flask_handler)

        # 设置本地日志的格式
        logger.setLevel(logging.ERROR)
        loacl_handler = TimedRotatingFileHandler(
            filename='invoke_api.log', when='midnight',
            backupCount=365, encoding='utf-8')  # 设置log名称以及新log生成时间，backcount表示保留个数
        loacl_handler.suffix = '%Y-%m-%d.log'  # 过期日志的后缀
        loacl_handler.extMatch = re.compile(r'^\d{4}-\d{2}-\d{2}.log')
        loacl_handler.setFormatter(logging.Formatter(
            '%(asctime)s -- %(levelname)s -- [%(filename)s->%(funcName)s->%(lineno)d] -- %(message)s'))
        logger.addHandler(loacl_handler)
    except Exception as e:
        logger.error('日志开启失败:')
        logger.error(e)


# setLogger()


class APITemplate:
    """ API模板类 """

    def __init__(self):
        self.code = 0
        self.msg = "success"
        self.data = {}
        # namelist只做存储和转化json使用
        # 不一定用得上，现在所有连接都默认使用脚本查询的内部字段
        self.nameList = []
        self.conn_ms = None
        self.conn_es = None

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
                logger.error("MSSQL连接失败")

    def setInfluxdbConn(self, host, user, password, database):
        """ 未实现,暂勿使用，influxdb直接使用请求 """
        pass

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

    def queryFromInfluxDB(self, sql, posturl,  title=None):
        """
        使用influxdb做查询
        参数 ：
            @posturl：数据库连接；
            @sql：脚本内容；
            @title：多行数据的一个总名称
        """
        try:
            # 使用MSSQLi查询脚本sql
            response = json.loads(requests.post(posturl, data=sql).content)
            data = response['results'][0]['series'][0]
            self.nameList = data['columns']
            values = data['values']
            self.parseToJsonObject(values, title)
        except Exception as e:
            logger.error("查询错误：可能是脚本错误或连接错误，导致查询失败")
            logger.error(e)
            self.setError(11, "查询错误")

    def queryFromES(self, body=None, conn=None, title=None, index=None, doc_type=None, params=None, headers=None):
        try:
            if self.conn_es is None:
                self.conn_es = conn
            result = self.conn_es.search(
                index=index, body=body, doc_type=doc_type, params=params, headers=headers)
        except Exception as e:
            logger.error("查询错误：可能是脚本错误或连接错误，导致查询失败")
            logger.error(e)
            self.setError(11, "查询错误")

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
