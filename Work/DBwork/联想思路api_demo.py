"""
descr: APITemplate development using falsk_restful
author: chenshi
environment: python3
date: 2021/7/17
"""

import pymssql
import json
import logging
from flask import Flask, g
from flask_restful import reqparse, Api, Resource
from flask_httpauth import HTTPTokenAuth
from logging.handlers import TimedRotatingFileHandler

# Flask相关变量声明
app = Flask(__name__)
api = Api(app)

# 认证相关
auth = HTTPTokenAuth(scheme="token")
TOKENS = {
    "fejiasdfhu",
    "fejiuufjeh"
}


@auth.verify_token
def verify_token(token):
    if token in TOKENS:
        g.current_user = token
        return True
    return False


# 日志相关

logger = logging.getLogger('werkzeug')  # 从werkzeug里面拦截日志
handler = TimedRotatingFileHandler(
    filename='invoke_api.log', when='midnight', backupCount=365, encoding='utf-8')  # 设置log名称以及新log生成时间，backcount表示保留个数
handler.suffix = '%Y-%m-%d.log'  # 过期日志的后缀
handler.extMatch = re.compile(r'^\d{4}-\d{2}-\d{2}.log')
logger.addHandler(handler)


# 数据库初始化
conn_ms = pymssql.connect(host='127.0.0.1', user='sa',
                          password='chenshi', port='1433', database='171219')


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

    def queryFromMSSQL(self, sql, conn, title=""):
        """
        使用sqlserver做查询
        参数 ：
            sql：脚本内容；
            conn：数据库连接；
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
            print(e)
            self.setError(11, "查询错误：可能是脚本错误或连接错误，导致查询失败")
        # return self.data

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
                self.setError(12, "内部调用错误：查询结果有多行数据，但是没有设置标题，请检查执行方法")
                return

            try:
                jsonArray = []
                for row in queryResult:
                    if len(row) != len(self.nameList):
                        self.setError(12, "内部调用错误：nameList和查询列数需要一致")
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
                print(e)
                self.setError(13, "APITmplate包异常：json格式化错误")

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


# 操作（put / get / delete）单一资源
class Demo(Resource):
    """
    一个接口实现的样例：
    获取报警数据: curl http://127.0.0.1:5000/data -X GET -H "Authorization:token fejiasdfhu"
    """
    # 添加认证
    decorators = [auth.login_required]

    # 调用记录
    # 待完成

    def get(self):
        query1 = APITemplate()
        # 名称列表
        query1.nameList = ['addr', 'evtno', 'evttype', 'level', 'value', 'id']
        # 查询语句
        sql = 'select top(5) addr,evt_no,evt_type,evt_level,evt_value, id from acscon_alarmactive'
        # 执行语句
        query1.queryFromMSSQL(sql, conn_ms, "title")
        query1.queryFromMSSQL(sql, conn_ms, "title1")
        # 添加其他属性字段
        query1.addProperty('id', 1)
        # 添加另一个json
        data = {"name": "aaa", "age": 17,
                "ulist": [{"人数": 12, "user": "asasj"}]}
        query1.addJson(data)

        # 返回需要的json和状态码
        return query1.formatJson(), 200


# 设置路由
api.add_resource(Demo, "/data")

if __name__ == "__main__":
    # app.logger.addHandler(handler)
    app.run(debug=True)
