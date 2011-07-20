from flask import Flask
from flask import render_template

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run('82.130.102.52')
