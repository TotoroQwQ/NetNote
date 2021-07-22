from flask import Flask,jsonify
import json
app = Flask(__name__)
#解决中文乱码的问题，将json数据内的中文正常显示
#开启debug模式
app.config['DEBUG'] = True
 
#使用jsonify模块来让网页直接显示json数据
@app.route('/json')
def re_json():
    #定义数据格式
    json_dict={'id':10,'title':'flask的应用','content':'flask的json'}
    #使用jsonify来讲定义好的数据转换成json格式，并且返回给前端
    # return json.dumps(json_dict,ensure_ascii=False)
    return jsonify(json_dict)
 
if __name__ == "__main__":
    app.config['JSON_AS_ASCII'] = False
    app.run()