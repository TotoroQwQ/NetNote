"""
descr: APITemplate development using falsk_restful
author: chenshi
environment: python3
date: 2021/7/17
"""

import json
import re
import logging
import requests
import typing as t
import werkzeug
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

def setLogger():
    """ 设置日志格式 """
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


setLogger()


class APITemplate:
    """ API模板类 """

    def __init__(self):
        self.retcode = 0
        self.msg = "success"
        self.data = {}
        # namelist只做存储和转化json使用
        self.nameList = []

    def setError(self, retcode, msg):
        """ 定义错误类型 """
        self.retcode = retcode
        self.data = {}
        self.msg = msg

    def formatJson(self):
        """ 以一个标准的网络API格式返回json """
        return {"retcode": self.retcode, "msg": self.msg, "data": self.data}

    def queryFromMSSQL(self, conn, sql, title=""):
        """
        使用sqlserver做查询
        参数 ：
            conn：数据库连接；
            sql：脚本内容；
            title：单行数据，如{a:1,b:2}，title不传, 多行数据：[{a:1,b:2},{a:2,b:3}],需要title
        """
        try:
            # 使用MSSQLi查询脚本sql
            ms = conn.cursor()
            ms.execute(sql)
            result = ms.fetchall()
            ms.close()
            self.parseToJsonObject(result, title)
        except Exception as e:
            logger.error("查询错误：可能是脚本错误或连接错误，导致查询失败")
            logger.error(e)
            self.setError(11, "查询错误")
        # return self.data

    def queryFromInfluxDB(self, posturl, sql, title=""):
        """
        使用influxdb做查询
        参数 ：
            posturl：数据库连接；
            sql：脚本内容；
            title：单行数据，如{a:1,b:2}，title不传, 多行数据：[{a:1,b:2},{a:2,b:3}],需要title
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

    def parseToJsonObject(self, queryResult, title):
        """
        内部方法，将数据库执行后的数据转成json对象
        """

        if len(queryResult) == 0:
            for item in self.nameList:
                self.data[item] = ""
        else:
            # 多行无标题，定义错误4
            if len(queryResult) > 1 and title == "":
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
                if(title != ""):
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
        if self.retcode != 0:
            return
        self.data[propName] = propValue

    def addJson(self, jsonObject):
        """
        向APITemplate.data里面合并另一个json
        """
        if(self.retcode != 0):
            return
        for key in jsonObject:
            self.data[key] = jsonObject[key]

    def delProperty(self, propName):
        del self.data[propName]
