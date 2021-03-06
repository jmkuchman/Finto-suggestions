"""
Authentication related API Endpoints.

Authentication flow:
    1.) A registered user acquires an accesst token (JSON Web Token, JWT) by logging in.
        (This can be tested from the Swagger UI, for example: /api/ui -> /login)
        Also refresh token is acquired.
    2.) Now authenticated user can access auth-only API endpoints by adding a
            Authorization: Bearer <access token>
        header to requests.
    3.) The access token has a default expiration of 15 minutes. The user needs to get
        a new token from the /api/refresh endpoint using the refresh token. It has a
        default expiration of 30 days.


Decorator @jwt_required (from flask_jwt_extended) should be added for each
API operation that requires authenticated access.

Token blacklisting partially from
https://github.com/vimalloc/flask-jwt-extended/tree/master/examples/database_blacklist

For additional configuration and features,
please see http://flask-jwt-extended.readthedocs.io/en/latest/
"""

import os
import connexion

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    jwt_refresh_token_required
)

import requests

from .common import create_response
from ..models import db, User, UserRoles
from ..authentication import blacklist_token

def login() -> str:
    """
    Logs the user in returning a valid access token (JWT) and user_id.

    POST request requires a body with user email and password.
    This should be sent over https!

    {
        "email": "test@test.com",
        "password": "mysecretpassword"
    }

    :returns: A JWT access token wrapped in a response object or an error message
    """

    email = connexion.request.json.get('email', None)
    password = connexion.request.json.get('password', None)

    if email and password:
        user = User.query.filter_by(email=email).first()
        if user and user.validate_password(password):
            # this time, skip overriden as_dict() to disable event
            # serialization
            serialized_user = super(User, user).as_dict()
            access_token = create_access_token(identity=serialized_user)
            refresh_token = create_refresh_token(identity=serialized_user)

            return {'access_token': access_token, 'refresh_token': refresh_token, 'user_id': user.id, 'code': 200}, 200

    return create_response(None, 401, "Incorrect email or password.")


@jwt_refresh_token_required
def refresh() -> str:
    """
    Refreshes the JWT access token with a refresh token.

    Requires the following header to get a fresh access token
        Authorization: Bearer <valid refresh token>

    :returns: A JWT access token wrapped in a response object
    """

    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)

    return create_response({}, 200, access_token=access_token)


@jwt_required
def logout() -> str:
    """
    Log the user out by blacklisting the tokens.

    POST request requires a body with
    an access_token and refresh_token.

    {
        "access_token": "eyJ0eXAiOiJKV1Q...",
        "refresh_token": "eyJ0eXAiOiJKV1..."
    }

    :returns: A JWT access token wrapped in a response object or an error message
    """

    access_token = connexion.request.json.get('access_token', None)
    refresh_token = connexion.request.json.get('refresh_token', None)

    if access_token and refresh_token:
        blacklist_token(access_token)
        blacklist_token(refresh_token)

    return create_response({}, 200, "Successfully logged out.")


@jwt_required
def revokeAuthentication() -> str:
    """
    Log the user out by blacklisting the tokens.

    POST request requires a body with
    an access_token and refresh_token.

    {
        "access_token": "eyJ0eXAiOiJKV1Q...",
        "refresh_token": "eyJ0eXAiOiJKV1..."
    }

    :returns: A JWT access token wrapped in a response object or an error message
    """

    access_token = connexion.request.json.get('access_token', None)
    refresh_token = connexion.request.json.get('refresh_token', None)

    try:
        blacklist_token(access_token)
        blacklist_token(refresh_token)
    except Exception as ex:
        print(ex)
        return {'error': str(ex)}, 400

    return create_response({}, 200, 'There was errors while trying to blacklist and remove tokens ')


def post_github() -> str:
    """
    Callback method for Github oAuth2 authorization

    :returns: A JWT access token wrapped in a response object or an error message
    """

    code = connexion.request.json.get('code')

    oauth_data = ()
    try:
        oauth_data = handle_github_request(code)
        return handle_user_creation(code, oauth_data)
    except ValueError as ex:
        print(ex)
        return {'error': str(ex)}, 400


def handle_github_request(code) -> (str, str):
    """
    Handles github request
    :returns tuple(name, email, github_access_token) or value error exception

    """

    name = ''
    email = ''
    image = ''

    # for debug if error occurred
    user_data = ''
    user_email_data = ''

    if code is not None:
        github_client_id = os.environ.get('GITHUB_CLIENT_ID')
        github_client_secret = os.environ.get('GITHUB_CLIENT_SECRET')
        redirect_uri = os.environ.get('GITHUB_REDIRECT_URI')

        payload = {
            'client_id': github_client_id,
            'client_secret': github_client_secret,
            'code': code,
            'redirect_uri': redirect_uri
        }

        token_response = requests.post(
            'https://github.com/login/oauth/access_token', data=payload)

        if token_response is not None and len(token_response.text) > 0:
            github_access_token = token_response.text.split('&')[0].split('=')[1]

            if github_access_token is not None and len(github_access_token) > 0:
                user_data_response = requests.get(f'https://api.github.com/user?access_token={github_access_token}')

                if user_data_response is not None and user_data_response.ok is True:
                    user_data = user_data_response.json()
                    if user_data['name'] is not None:
                        name = user_data['name']
                    else:
                        name = user_data['login']
                    if user_data['avatar_url'] is not None:
                        image = user_data['avatar_url']


            user_email_data_response = requests.get(f'https://api.github.com/user/emails?access_token={github_access_token}')
            if user_email_data_response is not None and user_email_data_response.ok is True:
                user_email_data = user_email_data_response.json()
                for data in user_email_data:
                    if data['primary'] is True and data['email'] is not None:
                        email = data['email']

    if email is not None:
        return (name, email, image)
    else:
        raise ValueError(f'Could not get github user email info {user_data} {user_email_data}')


def handle_user_creation(code, oauth_data) -> str:
    """
    Handles user creation
    :parameters oauth application code and oauthdata(name, email)
    :returns success response or exception that is upper method catched
    """

    name = oauth_data[0]
    email = oauth_data[1]
    image = oauth_data[2]

    local_access_token = ''

    user = User.query.filter_by(email=email).first()

    if user is None:
        user = User(
            name=name,
            email=email,
            imageUrl=image,
            password=None,
            role=UserRoles.NORMAL
        )

        try:
            db.session.add(user)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            raise ex

    serialized_user = super(User, user).as_dict()
    local_access_token = create_access_token(identity=serialized_user)
    local_refresh_token = create_refresh_token(identity=serialized_user)

    return {'access_token' : local_access_token, 'refresh_token': local_refresh_token, 'user_id': user.id, 'code': 200}, 200
