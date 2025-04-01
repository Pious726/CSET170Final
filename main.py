from flask import Flask, render_template, request, url_for, redirect
from sqlalchemy import create_engine, text
 
app = Flask(__name__)
conn_str = "mysql://root:cset155@localhost/bank"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()

@app.route('/')
def loadapp():
    return render_template('base.html')

@app.route('/login.html')
def getlogins():
    return render_template('login.html')

@app.route('/home.html')
def home():
    return render_template('home.html')

@app.route('/account.html', methods=["GET"])
def getAccounts():
    return render_template('account.html')

@app.route('/account.html', methods=["POST"])
def seeAccount():
    return render_template('account.html')

@app.route('/deposit.html')
def deposit():
    return render_template('deposit.html')

@app.route('/transfer.html')
def transfer():
    return render_template('transfer.html')

@app.route('/admin.html')
def authorizeAccounts():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True)