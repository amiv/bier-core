from flask import Flask, jsonify, render_template, request
import sys

app = Flask(__name__)
getBeer = 1
@app.route('/')
def index():
    return 'Index Page'

@app.route('/beer/')
@app.route('/beer/<beer>')
def beer(beer=None):
    return render_template('beer.html', beer=beer)

@app.route('/valid')
def valid():
    return render_template('valid.html')
    
@app.route('/ajax')
def ajax():
    return render_template('ajax.html')
    
@app.route('/hello')
def hello():
    return render_template('hello.html')

@app.route('/_checkLegi', methods=['POST','GET'])
def checkLegi():

    global getBeer
    getBeer = request.form.get('getBeer', 0, type=int)
    print >>sys.stderr,getBeer
    return ""

@app.route('/_updateLegi')
def updateLegi():
    global getBeer
    if (getBeer > 0):
        releaseBeer = getBeer
    else:
        releaseBeer = getBeer
    return jsonify(result=releaseBeer)


if __name__ == '__main__':
    app.run('127.0.0.1',debug=True)
