from flask import Blueprint, request, jsonify, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

from shared.interface.conference import Conference
from shared.interface.client import Client
from shared.interface.user import User

from httpserver import app, db

bcrpt = Bcrypt()

@app.route('/')
def index():
    if request.method == 'GET':
        pass

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = db.find_one('users', {'username': request.form['username']})
        if user and bcrpt.check_password_hash(user['password'], request.form['password']):
            login_user(User(user))
            return redirect(url_for('index'))
        else:
            return 
    return jsonify({'message': 'Login page'})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        pass
    pass