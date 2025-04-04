from flask import Flask, render_template, request, url_for, redirect
from sqlalchemy import create_engine, text
import random
import bcrypt
 
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
        signupData = dict(request.form)
        hashed_password = bcrypt.hashpw(signupData["UserPassword"].encode('utf-8'), bcrypt.gensalt())
        signupData["UserPassword"] = hashed_password

        conn.execute(text('insert into users(Username, Fname, Lname, SSN, Address, PhoneNum, UserPassword) values(:Username, :Fname, :Lname, :SSN, :Address, :PhoneNum, :UserPassword)'), signupData)
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
        password = request.form.get("UserPassword").encode('utf-8')
        print(password)

        login_query = conn.execute(text('select UserPassword from users where Username = :username'), {'username': username}).scalar()

        is_valid_account = conn.execute(text('select ApprovedStatus from users where Username = :username'), {'username': username}).scalar()
        
        if is_valid_account == 1 and login_query:
            stored_hash = login_query.encode('utf-8')

            if bcrypt.checkpw(password, stored_hash):
                conn.execute(text("update users set IsLoggedIn = 1 where Username = :username"), {"username": username})
                conn.commit()
                return redirect(url_for('home'))
            else:
                return render_template('login.html', error='Incorrect username or password.', success=None)
        else:
            return render_template('login.html', error='Not valid account.', success=None)
    except:
        return render_template('login.html', error='Login Error.', success=None)

@app.route('/logout')
def logout():
    conn.execute(text('update users set IsLoggedIn = 0 where IsLoggedIn = 1'))
    conn.commit()
    return redirect('/login.html')

@app.route('/admin.html')
def authorizeAccounts():
    with engine.connect() as conn:
        accounts = conn.execute(
            text('SELECT UserID, Username, Fname, Lname, SSN, Address FROM users WHERE ApprovedStatus = 0')
        ).fetchall()
    
    return render_template('admin.html', accounts=accounts)

@app.route('/admin_action', methods=['POST'])
def admin_action():
    user_id = request.form.get('user_id')
    action = request.form.get('action')

    with engine.connect() as conn:
        try:
            if action == 'approve':
    
                conn.execute(
                    text('UPDATE users SET ApprovedStatus = 1 WHERE UserID = :user_id'),
                    {"user_id": user_id}
                )

                bank_id = random.randint(100000, 999999)
                while conn.execute(
                    text('SELECT 1 FROM bankAccounts WHERE accountNum = :id'),
                    {"id": bank_id}
                ).scalar():
                    bank_id = random.randint(100000, 999999)
                
                conn.execute(
                    text('INSERT INTO bankAccounts (userID, accountNum) '
                         'VALUES (:user_id, :bank_id)'),
                    {"user_id": user_id, "bank_id": bank_id}
                )
                
            elif action == 'deny':
                conn.execute(
                    text('DELETE FROM users WHERE UserID = :user_id'),
                    {"user_id": user_id}
                )
            
            conn.commit()
            
        except:
            conn.rollback()
    
    return redirect(url_for('authorizeAccounts'))

@app.route('/home.html')
def home():
    username = conn.execute(text('select Username from users where IsLoggedIn = 1')).scalar()
    IsAdmin = conn.execute(text('select IsAdmin from users where IsLoggedIn = 1')).scalar()
    return render_template('home.html', username=username, IsAdmin=IsAdmin)

@app.route('/account.html')
def seeAccount():
    account = conn.execute(text("select * from users where IsLoggedIn = 1")).fetchone()
    userID = conn.execute(text('select userID from users where IsLoggedIn = 1')).scalar()
    bankAccount = conn.execute(text('select * from bankAccounts where userID = :userID'), {"userID": userID}).fetchone()
    return render_template('account.html', account=account, bankAccount = bankAccount)

@app.route('/deposit.html', methods=["GET"])
def getDeposit():
    return render_template('deposit.html')

@app.route('/deposit.html', methods=["POST"])
def deposit():
    try:
        userID = conn.execute(text('select userID from users where IsLoggedIn = 1')).scalar()
        accountNum = conn.execute(text(f'select accountNum from bankAccounts where userID = :userID'), {"userID": userID}).scalar()
        amount = request.form.get("amount")

        conn.execute(text('update bankAccounts set balance = balance + :amount where accountNum = :accountNum'), {"accountNum": accountNum, "amount": amount})
        conn.commit()

        return render_template('deposit.html', error = None, success = "Successfully deposited into your account!")
    except:
        return render_template('deposit.html', error = "Failed to deposit.", success = None)
    
@app.route('/transfers.html', methods=["GET", "POST"])
def transfers():
    if request.method == "GET":
        return render_template('transfers.html')
    
    try:
        userID = conn.execute(text('SELECT userID FROM users WHERE IsLoggedIn = 1')).scalar()
        sender_account, sender_balance = conn.execute(
            text('SELECT accountNum, balance FROM bankAccounts WHERE userID = :userID'),
            {"userID": userID}
        ).fetchone()

        recipient = request.form.get("recipient_account")
        amount = float(request.form.get("amount"))

        if sender_balance < amount:
            return render_template('transfers.html', error="Not enough funds")
        if not conn.execute(text('SELECT 1 FROM bankAccounts WHERE accountNum = :acc'), 
                         {"acc": recipient}).scalar():
            return render_template('transfers.html', error="Account doesn't exist")

        conn.execute(
            text('UPDATE bankAccounts SET balance = balance - :amt WHERE accountNum = :acc'),
            {"amt": amount, "acc": sender_account}
        )
        conn.execute(
            text('UPDATE bankAccounts SET balance = balance + :amt WHERE accountNum = :acc'),
            {"amt": amount, "acc": recipient}
        )
        conn.commit()

        return render_template('transfers.html', success="Money sent!")
    
    except:
        conn.rollback()
        return render_template('transfers.html', error="Transfer failed")
    
if __name__ == '__main__':
    app.run(debug=True)