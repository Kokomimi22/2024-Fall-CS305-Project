from flask import Flask
from flask import Blueprint
from flask import Config
import pymongo as pm
from config import SERVER_IP, HTTP_SERVER_PORT, DATABASE_PORT

app = Flask(__name__)
app.config.from_object(Config(__name__))
app.config['SERVER_IP'] = SERVER_IP
app.config['HTTP_SERVER_PORT'] = HTTP_SERVER_PORT
app.config['DATABASE_PORT'] = DATABASE_PORT

existing_conferences = {}
db = pm.MongoClient('localhost', app.config['DATABASE_PORT'])['users']

from conference.routes import conference_bp
from conference.interface import Conference

app.register_blueprint(conference_bp)

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = db.find_one('users', {'username': request.form['username']})
        if user and bcrpt.check_password_hash(user['password'], request.form['password']):
            login_user(User(user))
            return redirect(url_for('index'))
        else:
            return 
    return jsonify({'message': 'Login page'})
    if request.method == 'GET':
        pass

def run():
    try:
        app.run(host=app.config['SERVER_IP'], port=app.config['HTTP_SERVER_PORT'])
    except Exception as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Server stopped")

if __name__ == '__main__':
    run()
