""" 
依赖安装：
pip install flask
pip install flask_docs
pip install logging
pip install concurrent_log_handler

如果开启了tokenauth
pip install flask_httpauth
pip install itsdangerous

数据库依赖选装：
pip install pymysql
pip install pymssql
pip install elasticsearch
pip install redis
"""

from flask import Flask, request, Blueprint
import requests
import APITemplate as API
from APITemplate import app
from flask_docs import ApiDoc

# Flask相关变量声明
# app = Flask(__name__)

API.handlerError() #后续可能设置到默认开启
# 获取tokenauth
tokenAuth = API.getTokenAuth()

# 开启api在线文档，需配合蓝图使用,地址127.0.0.1:5000/docs/api
ApiDoc(app, title="Sample App", version="1.0.0")
# 定义蓝图
relationDB_demo = Blueprint('relationDB_demo', __name__)
nonrelationDB_demo = Blueprint('nonrelationDB_demo', __name__)
others = Blueprint('others', __name__)


@app.route('/mssqldemo')
# 直接用flask路由，不使用蓝图，不会出现在在线文档里面，但可以get请求结果
# 开启token验证，token目前是定义的一个列表，后面可以加一个自动生成
@tokenAuth.login_required
def msSQLDemo():
    """
    一个MSSQL接口实现的样例：
        获取报警数据:
        curl http://127.0.0.1:5000/mssqldemo -X GET -H "Authorization:token fejiasdfhu"
    """
    msApi = API.APITemplate()
    # 连接mssql，包装了一下
    msApi.setMSConn(host='127.0.0.1:1433', user='sa',
                    password='saftop', database='171219')
    # 查询语句
    sql = 'select top(5) addr,evt_no,evt_type,evt_level,evt_value, id from acscon_alarmactive'
    # 执行语句,如果前面没有setMSConn,这里可以传一个mssql的连接对象
    msApi.queryFromMSSQL(sql=sql, title="title")
    # 返回需要的json和状态码
    return msApi.formatJson(), 200


@relationDB_demo.route('/mysqldemo/<int:id>')
@tokenAuth.login_required
def mySQLDemo(id):
    """
    一个MySQL接口实现的样例:
    curl http://127.0.0.1:5000/relationDB_demo/mysqldemo/33 -X GET -H "Authorization:token fejiasdfhu"
    """
    myApi = API.APITemplate()
    # 连接mysql，包装了一下
    myApi.setMySqlConn(host='20.0.0.252:3306', user='root',
                       password='root', database='st_device')
    # 查询语句
    sql = 'select * from dev_machine where id = {}'.format(id)
    # 执行语句,如果前面没有setMySqlConn,这里可以传一个mysql的连接对象
    myApi.queryFromMySQL(sql=sql, title="title")
    # 返回需要的json和状态码
    return myApi.formatJson(), 200


@nonrelationDB_demo.route('/influxdemo')
# 使用蓝图添加路由，会出现在在线api文档里面，默认method='get'
# 为了方便测试，不加token验证
# @API.httpTokenAuth.login_required
def influxDemo():
    """  

    一个InfluxDB接口实现的样例
    """
    sql = {}
    # 解析get里面的参数字段 (如果是post，使用request.from.keys():)
    if 'limit' in request.args.keys():
        limit = request.args['limit']
        sql = {'q': ('select * from tableB limit {}').format(limit)}
    else:
        sql = {'q': 'select * from tableB limit 10'}
    # influxdb只用一个url即可获取数据
    infulxApi = API.APITemplate()
    infulxApi.setInfluxdbConn('20.0.0.201:8086', database='dataB')
    infulxApi.queryFromInfluxDB(sql, title="title")
    return infulxApi.formatJson()


@others.route('/curldemo')
def curl():
    """ 
    访问其他的API转成自己的格式demo
    """
    url = 'http://20.0.0.252:13000/mock/26/param/all'
    # 使用get协议访问url
    response = requests.get(url)
    # 直接放回内容，如果需要再解析，按自己需要做解析
    return response.content.decode('utf-8')


@nonrelationDB_demo.route('/esdemo')
# 使用@@@注释声明，表示内容为markdown格式，如果有注释重复使用，可以使用装饰器 @ApiDoc.change_doc
def EsSearch():
    """ ESDEMO:这是说明
    @@@
    ### args
    | args | nullable | request type | type |  remarks |
    |-------|----------|--------------|------|----------|
    | area  |  true    |    body      | str  | 统计的区域 |
    | device |  true   |    body      | str  | 统计的设备 |
    | page  |  true    |    body      | str  | 数据页数 |
    | pageSize |  true   |    body      | str  | 每页数量 |

    ### request
    ```json
    {"area": "xxx", "device": "xxx", page: 1, pageSize: 20}
    ```

    ### return
    ```json
    {"code": xxxx, "msg": "xxx", "data": null}
    ```
    @@@

    """

    esApi = API.APITemplate()
    esApi.setESConn('20.0.0.252:9200', 'elastic', 'saftop9854')
    body = {
        'query': {
            'match': {
                'title': '中国领事馆'
            }
        }
    }
    esApi.queryFromES(body=body, title='title', index='test')
    return esApi.formatJson()


@nonrelationDB_demo.route('/redisdemo')
def redisDemo():
    redisApi = API.APITemplate()
    redisApi.setRedisConn(host='20.0.0.23:6379', password='saftop123456')
    redisApi.queryFromRedis(
        ['dev_stat:100-7', 'dev_stat:100-7#0'], title='title')
    return redisApi.formatJson()


@others.route('/mergeJson')
def mergeDemo():
    """ 
    一些可能用到的json整合功能demo
    """
    api = API.APITemplate()
    api.data = {'a': 'b'}
    # 添加其他属性字段
    api.addProperty('id', 1)
    # 添加另一个json
    data = {"name": "aaa", "age": 17,
            "ulist": [{"人数": 12, "user": "asasj"}]}
    api.addJson(data)
    return api.formatJson(), 200


# 复用的注释
reUseExegesis = '{"code": xxxx, "msg": "xxx", "data": null}'


@others.route("/reuse", methods=["POST"])
@ApiDoc.change_doc({"return_json": reUseExegesis})
def reUsedemo():
    """复用注释的demo
    @@@
    ### return
    ```json
    return_json
    ```
    @@@
    """
    return {'api': 'reusedemo'}


if __name__ == "__main__":
    # 开启日志
    API.openLogger('debug')
    # 注册蓝图
    API.registerBlueprint({relationDB_demo: "关系型数据库样例",
                          nonrelationDB_demo: "非关系型数据库样例", others: "其他"}, ApiDoc)
    app.run(debug=True)
