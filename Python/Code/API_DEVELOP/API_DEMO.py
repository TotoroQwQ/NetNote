from flask import Flask, request, Blueprint
from flask_restful import Api, Resource
import pymssql
import requests
import APITemplate as API
from flask_docs import ApiDoc

# Flask相关变量声明
app = Flask(__name__)
flask_restful = Api(app)
apidemo = Blueprint('apidemo', __name__)

# 数据库初始化
conn_ms = pymssql.connect(host='127.0.0.1', user='sa',
                          password='saftop', port='1433', database='171219')

posturl = 'http://20.0.0.201:8086/query?db=dataB'


class msSQL_Demo(Resource):
    """
    一个MSSQL接口实现的样例：

    获取报警数据:
    curl http://127.0.0.1:5000/mssqldemo -X GET -H "Authorization:token fejiasdfhu"
    """
    # 添加认证
    decorators = [API.httpTokenAuth.login_required]

    def get(self):
        query = API.APITemplate()
        # 查询语句
        sql = 'select top(5) addr,evt_no,evt_type,evt_level,evt_value, id from acscon_alarmactive'
        # 执行语句
        query.queryFromMSSQL(sql, conn_ms, "")
        query.queryFromMSSQL(sql, conn_ms, "title1")
        # 添加其他属性字段
        query.addProperty('id', 1)
        # 添加另一个json
        data = {"name": "aaa", "age": 17,
                "ulist": [{"人数": 12, "user": "asasj"}]}
        query.addJson(data)

        # 返回需要的json和状态码
        return query.formatJson(), 200


@app.route('/influxdemo')
# @API.httpTokenAuth.login_required
def get():
    print(request.method)
    sql = {}
    if 'limit' in request.args.keys():
        limit = request.args['limit']
        sql = {'q': ('select * from tableB limit {}').format(limit)}
    else:
        sql = {'q': 'select * from tableB limit 10'}
    query = API.APITemplate()
    query.queryFromInfluxDB(sql, posturl, "")
    return query.formatJson()


@app.route('/curldemo')
def curl():
    url = 'http://20.0.0.252:13000/mock/26/param/all'
    response = requests.get(url)
    return response.content.decode('utf-8')


@apidemo.route('/esdemo')
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
    query = API.APITemplate()
    query.setESConn('20.0.0.252:9200', 'elastic', 'saftop9854')
    body = {
        'query': {
            'match': {
                'title': '中国领事馆'
            }
        }
    }
    query.queryFromES(body=body, title='news', index='test')
    return query.formatJson()


@app.route('/esdemo2')
def EsSearch2():
    limit = request.args['limit']

    query = API.APITemplate()
    query.setESConn('20.0.0.252:9200', 'elastic', 'saftop9854')
    body = {
        'query': {
            'match': {
                'title': '中国领事馆',
                'limit': limit
            }
        }
    }
    query.queryFromES(body=body, title='news', index='test')
    return query.formatJson()


# 设置路由
flask_restful.add_resource(msSQL_Demo, "/mssqldemo")
# api.add_resource(influxDB_Demo, "/influxdemo")

if __name__ == "__main__":
    # 解决flask中文乱码的问题，将json数据内的中文正常显示
    app.config['JSON_AS_ASCII'] = False
    # 解决flask_restful中文乱码问题
    app.config.update(RESTFUL_JSON=dict(ensure_ascii=False))
    # 开启日志
    API.openLogger()
    # 配置API文档
    # 访问路径 127.0.0.1:5000/docs/api
    app.config["API_DOC_MEMBER"] = ["apidemo", "platform"]
    ApiDoc(app, title="Sample App", version="1.0.0")
    app.register_blueprint(apidemo, url_prefix="/apidemo")

    app.run(debug=True)
