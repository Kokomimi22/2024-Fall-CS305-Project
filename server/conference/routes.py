
from flask import Blueprint, request, jsonify
from flask_login import login_required
from conference.interface import Conference

from user import User

conference_bp = Blueprint('conference', __name__)

@conference_bp.route('/')
def index():
    return "This is the conference route"


@conference_bp.route('/list', methods=['GET'])
# @login_required
def get_conferences():
    '''
    Get all existing conferences
    '''
    conferences = existing_conferences
    return jsonify({'conferences': [Conference(conference) for conference in conferences]})

@conference_bp.route('/<conference_id>', methods=['GET'])
# @login_required
def get_conference(conference_id):
    '''
    Get a specific conference
    '''
    for conference in existing_conferences:
        if conference['uuid'] == conference_id:
            return jsonify(Conference(conference))

@conference_bp.route('/create', methods=['POST'])
# @login_required
def create_conference():
    '''
    Create a new conference
    '''
    query = request.json
    existing_conferences.conference_bpend(Conference.from_query(query))
    return jsonify(Conference(conference))

@conference_bp.route('/<conference_id>/join', methods=['POST'])
@login_required
def join_conference(conference_id):
    '''
    Join a conference
    '''
    query = request.json
    for conference in existing_conferences:
        if conference['uuid'] == conference_id:
            conference.add_client(request)
            return jsonify(Conference(conference))