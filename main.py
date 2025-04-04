from flask import Flask, render_template, request, url_for, redirect
from sqlalchemy import create_engine, text
import random
 
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
    return render_template('home.html', username=username)

@app.route('/account.html')
def seeAccount():
    account = conn.execute(text("select * from users where IsLoggedIn = 1")).fetchone()
    print(account)
    return render_template('account.html', account=account)

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

@app.route('/transfer.html')
def transfer():
    try:
        userID = conn.execute(text('Select userID From users Where IsLoggedIn = 1')).scalar()
        sender = conn.execute(text('Select accountNum balance From bankAccounts Where userID = :userID'),{"userID": userID}).fetchone()

        recipient = request.form.get("recipient_account")
        amount = float(request.form.get("amount"))

        if sender.balance < amount:
            return render_template('transfer.html', error="You broke cuz, you don't got the funds for that")
        if not conn.execute(text('Select 1 From bankAccounts where accountNum = :acc'),{"acc": recipient}).scalar():
            return render_template('transfer.html', error = "Account not found")
        
        conn.execute(text('Update bankAccounts Set balance = balance - :amt Where accontNum = :acc'),{"amt": amount, "acc": sender.accountNum})

        conn.execute(text('Update bankAccounts Set balance = balance + :amt Where accountNum = :acc'),{"amt": amount, "acc": recipient})
        conn.commit()

        return render_template('transfer.html', success="transfer succesful!")

    except:
        conn.rollback()
        return render_template('transfer.html', error="Transfer failed")


if __name__ == '__main__':
    app.run(debug=True)