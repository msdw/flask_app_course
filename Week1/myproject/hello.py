from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
  return 'hello world'


@app.route('/predict')
def upload():
  return 'Yooo'

# $ export FLASK_APP=hello.py
# $ flask run
#  * Running on http://127.0.0.1:5000/

