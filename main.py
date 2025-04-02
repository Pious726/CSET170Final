from flask import Flask, render_template, request, url_for, redirect
from sqlalchemy import create_engine, text
 
app = Flask(__name__)
conn_str = "mysql://root:cset155@localhost/bank"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()

@app.route('/', methods=["GET"])
def loadapp():
    return render_template('index.html')

@app.route('/', methods=["POST"])
def signup():
    try:
        conn.execute(text('insert into users(Username, Fname, Lname, SSN, Address, PhoneNum, UserPassword) values(:Username, :Fname, :Lname, :SSN, :Address, :PhoneNum, :UserPassword)'), request.form)
        conn.commit()
        return render_template('login.html', success="Account Created! Pending Admin Review...", error=None)
    except:
        return render_template('index.html', error = "Failed", success = None)

@app.route('/login.html', methods=["GET"])
def getlogins():
    conn.execute(text('update users set IsLoggedIn = 0 where IsLoggedIn = 1'))
    conn.commit()
    return render_template('login.html')

@app.route('/login.html', methods=["POST"])
def login():
    try:
        username = request.form.get("Username")
        password = request.form.get("UserPassword")
        login_query = conn.execute(text('select Userpassword from users where Username = :username'), {'username': username}).scalar()
        is_valid_account = conn.execute(text('select ApprovedStatus from users where Username = :username'), {'username': username}).scalar()
        print(username)
        print(password)
        print(login_query)
        print(is_valid_account)
        
        if is_valid_account == 1:
            if login_query == password:
                conn.execute(text("update users set IsLoggedIn = 1 where Username = :username"), {"username": username})
                conn.commit()
                return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Not valid account.', success=None)
    except:
        return render_template('login.html', error='Incorrect username or password.', success=None)

@app.route('/logout')
def logout():
    conn.execute(text('update users set IsLoggedIn = 0 where IsLoggedIn = 1'))
    conn.commit()
    return redirect('/login.html')

@app.route('/admin.html')
def authorizeAccounts():
    return render_template('admin.html')

@app.route('/home.html')
def home():
    username = conn.execute(text('select Username from users where IsLoggedIn = 1')).scalar()
    return render_template('home.html', username=username)

@app.route('/account.html')
def seeAccount():
    account = conn.execute(text("select * from users where IsLoggedIn = 1")).fetchone()
    print(account)
    return render_template('account.html', account=account)

@app.route('/deposit.html')
def deposit():
    return render_template('deposit.html')

@app.route('/transfer.html')
def transfer():
    return render_template('transfer.html')

if __name__ == '__main__':
    app.run(debug=True)

