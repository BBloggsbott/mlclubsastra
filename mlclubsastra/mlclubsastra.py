import os
import pymongo
from pymongo import MongoClient
import time
import datetime
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
mongo_client = MongoClient('mongodb://username:password@ip:port/mlclubsastra')
def get_mongo_db():
    return mongo_client.mlclubsastra


def get_tasks(n = 1):
    db = get_mongo_db()
    tasks = db.tasks
    try:
        return tasks.find().sort('time', pymongo.DESCENDING)[0]
    except:
        return None


@app.route('/')
def show_entries():
    db = get_mongo_db()
    members_table = db.members
    members = members_table.find()
    tasks = get_tasks()
    return render_template('show_leaderboard.html', members=members, currenttask = tasks)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        db = get_mongo_db()
        members_table = db.members
        users = members_table.find({'regno':int(request.form['username'])})
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
            db = get_mongo_db()
            members_table = db.members
            users = members_table.find({'regno':int(request.form['regno'])})
            for user in users:
                error = 'User exists'
                return render_template('register.html', error=error)
            members_table.insert_one({
                "regno": int(request.form['regno']),
                'name': request.form['name'],
                'password': request.form['password'],
                'score': 0,
                'kaggle': request.form['kaggle']
            })
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
        db = get_mongo_db()
        members_table = db.members
        if(request.form['password']!=''):
            members_table.update_one(
                {'regno': int(request.form['member'])},
                {
                    '$set': {
                        'password': request.form['password']
                    }
                }
            )
            message='Password updated'
            return render_template('admin_controls.html', success=message)
        members_table.update_one(
            {'regno': int(request.form['member'])},
            {
                '$inc': {
                    'score': int(request.form['points'])
                }
            }, upsert=False
        )
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
        db = get_mongo_db()
        tasks_table = db.tasks
        tasks_table.insert_one({
            'task': request.form['task'],
            'time': datetime.datetime.utcnow()
        })
        success="Task added"
        return render_template('addtask.html', success=success)
    return render_template('addtask.html')

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    error = None
    success = None
    if request.method == 'POST':
        db = get_mongo_db()
        task = get_tasks()['task']
        submissions_table = db.submissions
        submissions_table.insert_one({
            'regno':    int(session['regno']),
            'sublink':  request.form['sublink'],
            'task':     task,
            'time':     datetime.datetime.utcnow()
        })
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
    db = get_mongo_db()
    task = get_tasks()
    #print(len(task))
    if(len(task) == 0):
        return render_template('viewsubmissions.html', subs = None)
    task = task['task']
    submissions_table = db.submissions
    subs = submissions_table.find({
        'task': task
    }).sort('time', pymongo.ASCENDING)
    return render_template('viewsubmissions.html', subs = subs, task = task)

@app.route('/viewallsubs', methods=['GET', 'POST'])
def viewallsubs():
    try:
        if not session['admin']:
            return render_template('show_leaderboard.html', error='Not admin')
    except:
        return render_template('show_leaderboard.html', error='Not admin')
    db = get_mongo_db()
    submissions_table = db.submissions
    subs = submissions_table.find().sort('time', pymongo.ASCENDING)
    return render_template('viewallsubs.html', subs = subs)

@app.route('/removeuser', methods=['GET', 'POST'])
def removeuser():
    try:
        if not session['admin']:
            return render_template('show_leaderboard.html', error='Not admin')
    except:
        return render_template('show_leaderboard.html', error='Not admin')
    if request.method == 'POST':
        db = get_mongo_db()
        members = db.members
        members.delete_many({
            'regno':    int(request.form['regno'])
        })
        success="User Removed"
        return render_template('removeuser.html', success=success)
    return render_template('removeuser.html')

@app.route('/viewallusers', methods=['GET', 'POST'])
def viewallusers():
    try:
        if not session['admin']:
            return render_template('show_leaderboard.html', error='Not admin')
    except:
        return render_template('show_leaderboard.html', error='Not admin')
    db = get_mongo_db()
    members_table = db.members
    members = members_table.find().sort('name', pymongo.ASCENDING)
    print(members.count())  #.sort('name', pymongo.ASCENDING)
    return render_template('viewallusers.html', members = members)
