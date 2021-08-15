from flask import Flask
# from werkzeug import exceptions

app=Flask(__name__)

@app.route('/a')
def a():
    return 'a'

@app.errorhandler(Exception)
def error(e):
    if isinstance(e,exceptions.HTTPException):
        return e.description,e.code
    return 'Error'

if __name__=="__main__":
    app.run()