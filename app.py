from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length
from werkzeug.security import generate_password_hash, check_password_hash
import re
import requests

app=Flask(__name__)

api_url='https://api.mfapi.in/mf/'

app.secret_key='karan11'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'KIRUBAkaran1234'
app.config['MYSQL_DB'] = 'BANK_API'
mysql = MySQL(app)

details=[]

def isloggedin():
    
    return 'user_name' in session

def is_password_storng(Password):
    if len(Password)<8 :
        return False
    if not re.search(r"[a-z]", Password) or not re.search(r"[A-Z]", Password) or not re.search(r"\d",Password):
        return False
    if not re.search(r"[!@#$%^&*()-+{}|\"<>]?", Password):
        return False
 
    return True

class User:
    def __init__(self, id, username, password):
        self.id=id
        self.username=username
        self.password=password
        
class signup_form(FlaskForm):
    username=StringField("username",validators=[InputRequired(), Length(min=4, max=20)])
    password=PasswordField('password',validators=[InputRequired(), Length(min=8, max=50)])
    submit=SubmitField('signup')
    
class login_form(FlaskForm):
    username=StringField("username",validators=[InputRequired(), Length(min=4, max=20)])
    password=PasswordField('password',validators=[InputRequired(), Length(min=8, max=50)])
    submit=SubmitField('login')

@app.route('/')
def home():

    return render_template('index.html')

@app.route('/dashbord')
def dashbord():
    
    if isloggedin():
        user_id=session['user_name']
        
        cur = mysql.connection.cursor()
        cur.execute('select * from Mutulfund1 where name=%s',(user_id,))
        data=cur.fetchall()
        cur.close()
        
        return render_template('dashbord.html',data=data)
    return render_template('dashbord.html')

@app.route('/signup',methods=['GET','POST'])
def signup():
    
    form=signup_form()
    if form.validate_on_submit():
        username=form.username.data
        password=form.password.data
         
        if not is_password_storng(password):
            flash('password should be must be long')
            
            return redirect(url_for('signup'))
        
        hashed_password=generate_password_hash(password)
        
        cur = mysql.connection.cursor()
        cur.execute('select id from signup where username=%s',(username,))
        old_user=cur.fetchone()
        
        if old_user:
            cur.close()
            flash('username already taken. please choose a different one.','danger')
            
            return render_template('signup.html',form=form)
        
        cur.execute('insert into signup (username,password) values (%s, %s)',(username,hashed_password))
        mysql.connection.commit()
        cur.close()
        flash('signup successful')
        
        return redirect(url_for('login'))
    return render_template('signup.html',form=form)

@app.route('/login',methods=['GET','POST'])
def login():
    
    form=login_form()
    if form.validate_on_submit():
        username=form.username.data
        password=form.password.data
        
        cur = mysql.connection.cursor()
        cur.execute('select id, username, password from signup where username=%s',(username,))
        record=cur.fetchone()
        cur.close()
        
        if record:
            stored_hashed_pass = record[2]
            
            if check_password_hash(stored_hashed_pass,password):
                user=User( id=record[0], username=record[1], password=record[2])
                session['user_name']=user.username
                
                flash('Login successful')
                return redirect(url_for('dashbord'))
        else:
            flash('invalid credential','danger')
         
    return render_template('login.html',form=form)


@app.route('/insert',methods=['GET','POST'])
def add():
    if request.method=='POST':
        
        Fund_code=request.form.get('Fund_code')
        name=request.form.get('Name')
        invested_amt=request.form.get('Invested amount')
        unit_held=request.form.get('Unit held')
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Mutulfund (name, fund_code, invested_amount, unit_held) VALUES (%s,%s,%s,%s)",
                    (name, Fund_code, invested_amt, unit_held,))
        mysql.connection.commit()
        cur.close()
        
        if isloggedin():
            user_id=session['user_name']
            cur = mysql.connection.cursor()
            cur.execute('select fund_code from Mutulfund where name=%s',(user_id,))
            data=cur.fetchall()
            cur.close()
        
        data=requests.get(api_url+str(Fund_code))
        fundname=data.json().get('meta')['fund_house']
        nav=data.json().get('data')[0].get('nav')
        current_value=float(nav) * float(unit_held)
        growth=(current_value) - int(invested_amt)
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Mutulfund1 (name, fund_name, invested_amount, unit_held, nav, current_value, growth) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (name, fundname, invested_amt, unit_held, nav, current_value, growth))
        mysql.connection.commit()
        cur.close()
        
        
        return redirect(url_for('dashbord'))
    return render_template('add.html')

@app.route('/edit/<string:id>',methods=['GET','POST'])
def edit(id):
    
    cur= mysql.connection.cursor()
    cur.execute('select * from Mutulfund where id=%s',(id,))
    data=cur.fetchone()
    mysql.connection.commit()
    cur.close()
    
    if request.method=='POST':
        
        Fund_code=request.form.get('Fund_code')
        
        data=requests.get(api_url+str(Fund_code))
        fundname=data.json().get('meta')['fund_house']
        
        cur=mysql.connection.cursor()
        cur.execute("update Mutulfund1 set fund_name=%s where id=%s",
                    (fundname,id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('dashbord'))
    return render_template('edit.html',data=data)

@app.route('/delete/<string:id>')
def delete(id):
    cur=mysql.connection.cursor()
    cur.execute('delete from Mutulfund1 where id=%s',(id,))
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for('dashbord'))

@app.route('/logout')
def logout():
    session.pop('user',None)
    flash('logged out successful')
    return redirect(url_for('home'))

if __name__=='__main__':
    app.run(debug=True)