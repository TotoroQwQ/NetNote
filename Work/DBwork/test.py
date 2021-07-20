import traceback
import logging, termcolor
from logging.handlers import TimedRotatingFileHandler

from flask import Flask, g
from flask_restful import reqparse, Api, Resource
import re

app = Flask(__name__)
logger = logging.getLogger('werkzeug')

# 按天切分日志
handler = TimedRotatingFileHandler(filename='web.log', when='midnight', backupCount=7, encoding='utf-8')
handler.suffix = '%Y-%m-%d.log'
handler.extMatch = re.compile(r'^\d{4}-\d{2}-\d{2}.log')
logger.addHandler(handler)

# 重点, Flask 会把终端颜色控制符也写入日志，通过重写 termcolor 的 colored 来解决这个问题，同时不影响其他方法调用 termcolor.colored() 高亮
def colored(text, color=None, on_color=None, attrs=None):
    who_invoked = traceback.extract_stack()[-2][2]  # 函数调用人
    if who_invoked == 'log_request':
        # 如果是来自 Flask/werkzeug 的调用
        return text
    else:
        # 来自其他的调用正常高亮
        COLORS = termcolor.COLORS
        HIGHLIGHTS = termcolor.HIGHLIGHTS
        ATTRIBUTES = termcolor.ATTRIBUTES
        RESET = termcolor.RESET
        if os.getenv('ANSI_COLORS_DISABLED') is None:
            fmt_str = '\033[%dm%s'
            if color is not None:
                text = fmt_str % (COLORS[color], text)
            if on_color is not None:
                text = fmt_str % (HIGHLIGHTS[on_color], text)
            if attrs is not None:
                for attr in attrs:
                    text = fmt_str % (ATTRIBUTES[attr], text)
            text += RESET
        return text
      
termcolor.colored = colored
app.logger.addHandler(handler)


class Todo(Resource):
    def get(self):
        return {}, 200

api=Api(app)
api.add_resource(Todo, "/users")
if __name__ == "__main__":
    app.run(debug=True)