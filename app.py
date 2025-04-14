from flask import Flask, render_template, request, redirect, url_for, session
from bson.objectid import ObjectId
from db_config import users_collection, tasks_collection
from datetime import datetime
from pymongo import MongoClient
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Replace with your own MongoDB connection string if needed
client = MongoClient("mongodb://localhost:27017/")

# Database and collections
db = client['todo_app']
users_collection = db['users']
tasks_collection = db['tasks']
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = users_collection.find_one({'username': username})
        if existing_user:
            return 'User already exists!'

        users_collection.insert_one({'username': username, 'password': password})
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users_collection.find_one({'username': username, 'password': password})
        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid credentials!'

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Get the current date
    current_date = datetime.now().date()

    if request.method == 'POST':
        task_name = request.form['task-name']
        task_date = request.form['task-date']
        task_time = request.form['task-time']
        task_priority = request.form['task-priority']  # New field

        if task_name and task_date and task_time and task_priority:
            tasks_collection.insert_one({
                'username': session['username'],
                'name': task_name,
                'date': task_date,
                'time': task_time,
                'priority': task_priority,
                'completed': 0
            })
        return redirect(url_for('dashboard'))

    filter_option = request.args.get('filter', 'all')

    if filter_option == 'completed':
        user_tasks = list(tasks_collection.find({
            'username': session['username'],
            'completed': 1
        }))
    elif filter_option == 'pending':
        user_tasks = list(tasks_collection.find({
            'username': session['username'],
            'completed': 0
        }))
    else:
        user_tasks = list(tasks_collection.find({
            'username': session['username']
        }).sort('date', 1))

    return render_template('dashboard.html', tasks=user_tasks, current_date=current_date)
@app.route('/update_task', methods=['POST'])
def update_task():
    if 'username' not in session:
        return 'Unauthorized', 401

    task_id = request.form['id']
    completed = int(request.form['completed'])

    tasks_collection.update_one({'_id': ObjectId(task_id)}, {'$set': {'completed': completed}})
    return redirect(url_for('dashboard'))
@app.route('/edit_task', methods=['POST'])
def edit_task():
    if 'username' not in session:
        return 'Unauthorized', 401

    task_id = request.form['id']
    name = request.form['name']
    date = request.form['date']
    time = request.form['time']

    tasks_collection.update_one(
        {'_id': ObjectId(task_id)},
        {'$set': {'name': name, 'date': date, 'time': time}}
    )
    return redirect(url_for('dashboard'))
@app.route('/delete_task', methods=['POST'])
def delete_task():
    if 'username' not in session:
        return 'Unauthorized', 401

    task_id = request.form['id']
    tasks_collection.delete_one({'_id': ObjectId(task_id)})
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)

