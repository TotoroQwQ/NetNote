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
from flask_docs import ApiDoc

app = Flask(__name__)
API.handlerError(app) # 处理404等错误
tokenAuth=API.getTokenAuth(app,request) # token

# 开启api在线文档，地址/docs/api
ApiDoc(app, title="联想丝路数据对接", version="1.0.0")
# 定义蓝图
Panaroma = Blueprint('panorama1', __name__) #外观全景
BuildDevice = Blueprint('BuildDrvice', __name__) # 楼宇设备
Security = Blueprint('Security', __name__) # 综合安防
InfoDevice = Blueprint('InfoDevice',__name__) # 信息设施

################################################内部方法调用###################################################






###################################################对外接口###################################################


# Panaroma 外观全景

@Panaroma.route('/mapinfo')
def mapInfo():
    """ 地图信息
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
    pass

@Panaroma.route('/visitorstatistics')
def visitorStats():
    pass

@Panaroma.route('/carport')
def carPort():
    pass

@Panaroma.route('/energystatistics')
def energyStatistics():
    pass

@Panaroma.route('/alarms')
def alarms():
    pass

@Panaroma.route('/devicestate')
def deviceState():
    pass

@Panaroma.route('/workorder')
def workOrder():
    pass

# BuildDevice 楼宇设备


# Security 综合安防


# InfoDevice 信息设施




if __name__ == "__main__":
    # 解决flask中文乱码的问题，将json数据内的中文正常显示
    app.config['JSON_AS_ASCII'] = False
    # 开启日志
    API.openLogger('debug')
    # 注册蓝图
    API.registerBlueprint(app, [Panaroma, BuildDevice, InfoDevice])
    app.run(debug=True)
