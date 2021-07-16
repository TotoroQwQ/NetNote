import pymssql
import json
from flask import Flask, g
from flask_restful import reqparse, Api, Resource
from flask_httpauth import HTTPTokenAuth

# Flask相关变量声明
app = Flask(__name__)
api = Api(app)

# 数据库初始化
conn_ms = pymssql.connect(host='127.0.0.1', user='sa',
                          password='saftop', port='1433', database='171219')


def addProperty(jsonStr, propName, propValue):
    # 在当前json字符串基础上新增部分属性
    jsonObject = json.loads(jsonStr)
    jsonObject[propName] = propValue
    return json.dumps(jsonObject)


class APITemplate:
    def __init__(self):
        self.retcode = 0
        self.msg = "成功"
        self.data = {}
        self.nameList = []

    def setError(self, errorType):
        self.retcode = errorType
        if errorType == 1:
            self.msg = "查询数据时发生错误"
            self.data = {}
        elif errorType == 2:
            self.msg = "key-value数量对应不上"
            self.data = {}
        elif errorType == 3:
            self.msg = "json格式不对"
            self.data = {}

    def parseJson(self):
        return {"retcode": self.retcode, "msg": self.msg, "data": self.data}

    def queryFromMSSQL(self, sql, conn, title=""):
        try:
            # 使用MSSQLi查询脚本sql
            ms = conn.cursor()
            ms.execute(sql)
            result = ms.fetchall()
            ms.close()
            self.parseToJsonObject(result, title)
        except Exception as e:
            print(e)
            self.setError(1)
        # return self.data

    def parseToJsonObject(self, queryResult, title):
        # 将table类型的数据data转化成json格式，nameList为标题
        # 如果有多行数据，需要传一个大标题title
        try:
            jsonArray = []
            for row in queryResult:
                if len(row) != len(self.nameList):
                    self.setError(2)
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
            self.data = json.loads(jsonStr)

        except Exception as e:
            print(e)
            self.setError(3)


# 操作（put / get / delete）单一资源
class Todo(Resource):
    # # 获取报警数据: curl http://127.0.0.1:5000/data -X GET -H "Authorization:
    def get(self):
        query1 = APITemplate()

        # 名称列表
        query1.nameList = ['addr', 'evtno', 'evttype', 'level',
                           'value', 'id']

        # 查询语句
        sql = 'select top(1) addr,evt_no,evt_type,evt_level,evt_value, id from acscon_alarmactive'
        # 执行语句
        # query1.queryFromMSSQL(sql,conn_ms,"title")
        query1.queryFromMSSQL(sql, conn_ms)

        # 添加其他属性字段
        # query1.data = addProperty(jsonData, 'id', 1)
        # # 返回需要的json和状态码

        return query1.parseJson(), 200


# 设置路由
api.add_resource(Todo, "/data")


if __name__ == "__main__":
    app.run(debug=True)
