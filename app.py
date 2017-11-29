import datetime
import pymongo
import hashlib
import string
import random
from flask import Flask, render_template, request, redirect, session, g, url_for


app = Flask(__name__)
app.secret_key = 'qwerty'

@app.before_request
def before_request():
    if 'session_id' in request.cookies:
        m = pymongo.MongoClient()
        try:
            user = m.todo.session.find_one({
                'session_id':request.cookies['session_id']
            })['login']
            g.login = user
        except:
            return redirect('/')


def encrypt_password(password):
    h = hashlib.sha256()
    h.update(password.encode('utf8'))
    return h.hexdigest()

def create_session_id():
    return ''.join(random.choice(string.ascii_letters+string.digits) for i in range(128))


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        login = request.form.get('login', '')
        passwd = encrypt_password(request.form.get('passwd', ''))
        m = pymongo.MongoClient()
        user = m.todo.user.find_one({'login':login, 'passwd':passwd})
        if user:
            session_id = create_session_id()
            m.todo.session.insert({
                'login':login,
                'session_id':session_id
            })
        response = app.make_response(redirect('/list'))
        response.set_cookie('session_id', session_id, httponly=True)
        return response
    return render_template('login.html')


@app.route('/signup',  methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        login = request.form.get('login', '')
        passwd1 = request.form.get('passwd1', '')
        passwd2 = request.form.get('passwd2', '')
        if login and passwd1 and passwd1 == passwd2:
            m = pymongo.MongoClient()
            m.todo.user.insert({
                'login':login,
                'passwd': encrypt_password(passwd1)
            })
        return redirect('/')
    return render_template('signup.html')


@app.route('/list')
def list_():
    m = pymongo.MongoClient()
    tasks = m.todo.todo.find({'login':g.login})
    tasks = [{'desc':task['desc'],
              'deadline':task['deadline'].strftime('%d.%m.%Y')}
             for task in tasks]
    message = session.pop('message', '')
    return render_template('index.html',
                           message=message,
                           tasks=tasks)


@app.route('/add', methods=['GET', 'POST'])
def add():
    desc = deadline = message = ''
    if request.method == 'POST':
        desc = request.form.get('desc', '')
        deadline = request.form.get('deadline', '')
        try:
            date = datetime.datetime.strptime(deadline, '%d.%m.%Y')
        except ValueError:
            date = ''
        if desc and date:
            m = pymongo.MongoClient()
            m.todo.todo.insert({'desc':desc, 'deadline':date, 'login':g.login})
            session['message'] = 'task success'
            return redirect('/list')
        else:
            message = 'incorrect'
    return render_template('add.html',
                           desc=desc,
                           deadline=deadline,
                           message=message
                           )


if __name__ == '__main__':
    app.run(debug=True)