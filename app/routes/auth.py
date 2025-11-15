from flask import request
from flask_restx import Namespace, Resource, fields
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import User
from ..extensions import db
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from ..blacklist import blacklist

auth_ns = Namespace('auth', description='Authentication', security='Bearer Auth')

register_model = auth_ns.model('Register', {
    'username': fields.String(required=True),
    'email': fields.String(required=True),
    'password': fields.String(required=True)
})

login_model = auth_ns.model('Login', {
    'username': fields.String(required=True),
    'password': fields.String(required=True)
})

reset_model = auth_ns.model('ResetPassword', {
    'new_password': fields.String(required=True)
})


@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.expect(register_model)
    def post(self):
        data = request.get_json()
        
        if User.query.filter((User.username == data['username']) | (User.email == data['email'])).first():
            return {'message': 'User already exists'}, 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password'])
        )
        
        db.session.add(user)
        db.session.commit()

        return {'message': 'User created successfully'}, 201


@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(username=data.get('username')).first()

        if not user or not check_password_hash(user.password_hash, data.get('password')):
            return {'message': 'Invalid username or password'}, 401

        token = create_access_token(identity=str(user.id))
        return {'access_token': token}, 200


@auth_ns.route('/protected')
class Protected(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        return {'message': f'Access granted for user {current_user}'}, 200


@auth_ns.route('/users')
class GetAllUsers(Resource):
    @jwt_required()
    def get(self):
        users = User.query.all()
        
        return {
            'users': [
                {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                } for user in users
            ]
        }, 200


@auth_ns.route('/reset/<int:user_id>')
class ResetPassword(Resource):
    @jwt_required()
    @auth_ns.expect(reset_model)
    def put(self, user_id):
        data = request.get_json()
        new_password = data['new_password']

        user = User.query.get(user_id)
        if not user:
            return {'message': 'User not found'}, 404

        user.password_hash = generate_password_hash(new_password)
        db.session.commit()

        return {'message': 'Password updated successfully'}, 200


@auth_ns.route('/logout')
class Logout(Resource):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        blacklist.add(jti)
        return {'message': 'Successfully logged out'}, 200
