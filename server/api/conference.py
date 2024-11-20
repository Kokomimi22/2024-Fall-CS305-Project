from httpserver import app, db, existing_conferences
from flask import request, jsonify, session
from flask_login import login_required
from shared.interface.conference import Conference
from shared.interface.client import Client


