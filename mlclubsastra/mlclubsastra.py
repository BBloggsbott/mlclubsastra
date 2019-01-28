import os
import sqlite3
import time
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

app = Flask(__name__) 
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'mlclubsastra.db'),
    SECRET_KEY='96341257',
    USERNAME='admin',
    PASSWORD='password'
))
app.config.from_envvar('mlclubsastra_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

def get_tasks(n = 1):
    db = get_db()
    cur = db.execute('select * from tasks order by ts limit {}'.format(n))
    return cur.fetchall()

def reset_db():
    db = get_db()
    db.execute('delete * from members')
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

@app.cli.command('resetdb')
def resetdb_command():
    reset_db()
    print('DB reset')

@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('select * from members order by score desc')
    members = cur.fetchall()
    cur = db.execute('select * from tasks order by ts limit 1')
    tasks = cur.fetchall()
    if(len(tasks)==0):
        return render_template('show_leaderboard.html', members=members, currenttask = None)
    return render_template('show_leaderboard.html', members=members, currenttask = tasks[0])

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        db = get_db()
        users = db.execute('select * from members where regno='+str(request.form['username']))
        for user in users:
            if int(request.form['username']) != int(user['regno']):
                error = 'Invalid username'
            elif str(request.form['password']) != str(user['password']):
                error = 'Invalid password'
            else:
                session['logged_in'] = True
                session['regno'] = int(request.form['username'])
                flash('You were logged in')
                return redirect(url_for('show_entries'))
        if(error==None):
            error = 'User des not exist'
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    success = None
    if request.method == 'POST':
        try:
            db = get_db()
            users = db.execute('select * from members where regno='+str(request.form['regno']))
            for user in users:
                error = 'User exists'
                return render_template('register.html', error=error)
            db.execute("insert into members (regno, name, password, kaggle) values ({}, '{}', '{}', '{}')".format(request.form['regno'], request.form['name'], request.form['password'], request.form['kaggle']))
            db.commit()
            success="User added"
            return render_template('register.html', success=success)
        except Exception:
            error = 'Incorrect entry'
            return render_template('register.html', error=error)
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('regno', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error=None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid Username'
            return render_template('admin_login.html', error=error)
        if request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid Password'
            return render_template('admin_login.html', error=error)
        session['admin'] = True
        return render_template('admin_controls.html', error=error)
    return render_template('admin_login.html')

@app.route('/adminlogout')
def adminlogout():
    session.pop('admin', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

@app.route('/admincontrols', methods=['GET', 'POST'])
def admincontrols():
    try:
        if not session['admin']:
            return render_template('show_leaderboard.html', error='Not admin')
    except:
        return render_template('show_leaderboard.html', error='Not admin')
    if request.method == 'POST':
        message = None
        db = get_db()
        """print(int(request.form['member'])==120003366)
        print(int(request.form['points'])==45)
        print(request.form['password']=='')"""
        if(request.form['password']!=''):
            db.execute("update members set password='{}' where regno={}".format(request.form['password'], request.form['member']))
            db.commit()
            message='Password updated'
            return render_template('admin_controls.html', success=message)
        db.execute("update members set score=score+{} where regno = {}".format(request.form['points'], request.form['member']))
        db.commit()
        message='Points updated'
        return render_template('admin_controls.html', success=message)
    return render_template('admin_controls.html')        

@app.route('/addtask', methods=['GET', 'POST'])
def addtask():
    try:
        if not session['admin']:
            return render_template('show_leaderboard.html', error='Not admin')
    except:
        return render_template('show_leaderboard.html', error='Not admin')
    error = None
    success = None
    if request.method == 'POST':
        db = get_db()
        db.execute("insert into tasks (task) values ('{}')".format(request.form['task']))
        db.commit()
        success="Task added"
        return render_template('addtask.html', success=success)
    return render_template('addtask.html')

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    error = None
    success = None
    if request.method == 'POST':
        db = get_db()
        task = get_tasks()[0]
        db.execute("insert into submissions (regno, sublink, task) values ({},'{}','{}')".format(session['regno'], request.form['sublink'], task))
        db.commit()
        success="Submitted"
        return render_template('submit.html', success=success)
    return render_template('submit.html')

@app.route('/viewsubmissions')
def viewsubmissions():
    try:
        if not session['admin']:
            return render_template('show_leaderboard.html', error='Not admin')
    except:
        return render_template('show_leaderboard.html', error='Not admin')
    db = get_db()
    cur = db.execute("select * from submissions where task='{}' order by ts".format(session['task']))
    subs = cur.fetchall()
    task = get_tasks()[0]
    return render_template('viewsubmissions.html', subs = subs, task = task['task'])

@app.route('/viewallsubs', methods=['GET', 'POST'])
def viewallsubs():
    try:
        if not session['admin']:
            return render_template('show_leaderboard.html', error='Not admin')
    except:
        return render_template('show_leaderboard.html', error='Not admin')
    db = get_db()
    cur = db.execute("select * from submissions order by ts")
    subs = cur.fetchall()
    return render_template('viewallsubs.html', subs = subs)

@app.route('/removeuser', methods=['GET', 'POST'])
def removeuser():
    try:
        if not session['admin']:
            return render_template('show_leaderboard.html', error='Not admin')
    except:
        return render_template('show_leaderboard.html', error='Not admin')
    if request.method == 'POST':
        db = get_db()
        db.execute("delete from members where regno={}".format(request.form['regno']))
        db.commit()
        success="Deleted"
        return render_template('removeuser.html', success=success)
    return render_template('removeuser.html')

