#coding:utf-8
import datetime
import os
from base64 import b64decode
from urllib.parse import parse_qsl, urlparse
 
from flask import Flask, Response, abort, request, render_template
from flask_sqlalchemy import SQLAlchemy
 
 
app = Flask(__name__)
 
# 1 pixel GIF, base64-encoded.
app.config['BEACON'] = b64decode('R0lGODlhAQABAIAAANvf7wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==')
 
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@127.0.0.1:3306/database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['DOMAIN'] = 'http://127.0.0.1:5000'  # TODO: change me.
 
# Simple JavaScript which will be included and executed on the client-side.
app.config['JAVASCRIPT'] = """(function(){
    var d=document,i=new Image,e=encodeURIComponent;
    i.src='%s/a.gif?url='+e(d.location.href)+'&ref='+e(d.referrer)+'&t='+e(d.title);
    })()""".replace('\n', '')
 
# Flask application settings.
app.config['DEBUG'] = bool(os.environ.get('DEBUG'))
app.config['SECRET_KEY'] = 'secret - change me'  # TODO: change me.
 
db = SQLAlchemy(app)
 
 
class PageView(db.Model):
    __tablename__ = 'page_views'
 
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255))
    url = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    title = db.Column(db.String(255), default='')
    ip = db.Column(db.String(255), default='')
    referrer = db.Column(db.String(255), default='')
    user_agent = db.Column(db.String(255), default='')
    headers = db.Column(db.JSON)
    params = db.Column(db.JSON)
 
    def __repr__(self):
        return "<Model PageView `{}`>".format(self.domain)
 
    @classmethod
    def create_from_request(cls):
        page_view = PageView()
 
        parsed = urlparse(request.args['url'])
        params = dict(parse_qsl(parsed.query))
        print(request.user_agent.browser)
 
        page_view.domain = parsed.netloc,
        page_view.url = parsed.path,
        page_view.title = request.args.get('t') or '',
        page_view.ip = request.headers.get('X-Forwarded-For', request.remote_addr),
        page_view.referrer = request.args.get('ref') or '',
        page_view.headers = dict(request.headers),
        page_view.user_agent = request.user_agent.browser,
        page_view.params = params
 
        db.session.add(page_view)
        db.session.commit()
 
 
@app.route('/')
def index():
    return render_template('index.html')
 
 
@app.route('/a.gif')
def analyze():
    if not request.args.get('url'):
        abort(404)
 
    PageView.create_from_request()
 
    response = Response(app.config['BEACON'], mimetype='image/gif')
    response.headers['Cache-Control'] = 'private, no-cache'
    return response
 
 
@app.route('/a.js')
def script():
    return Response(
        app.config['JAVASCRIPT'] % (app.config['DOMAIN']),
        mimetype='text/javascript')
 
 
@app.errorhandler(404)
def not_found(e):
    return Response('Not found.')
 
 
if __name__ == '__main__':
    app.run()