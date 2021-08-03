from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address,   # 根据访问者的IP记录访问次数
    default_limits=["200 per day", "50 per hour"]  # 默认限制，一天最多访问200次，一小时最多访问50次
)
@app.route("/slow")
@limiter.limit("1 per day") 
def slow():
    return "24"

@app.route("/fast")        # 默认访问速率
def fast():
    return "42"

@app.route("/ping")
@limiter.exempt      # 无访问速率限制
def ping():
    return "PONG"