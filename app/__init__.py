import os
from flask import Flask, send_from_directory, jsonify, render_template, redirect
from .config import Config
from .extensions import db, migrate, jwt, api
from . import models
from .blacklist import blacklist

from .routes.auth import auth_ns
from .routes.categories import cat_ns
from .routes.products import prod_ns
from .routes.invoices import inv_ns
from .routes.reports import rep_ns


def create_app():
    app = Flask(__name__, static_folder=None)

    # Load .env if exists
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(env_path)

    # Load config
    app.config.from_object(Config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Swagger Authentication
    authorizations = {
        "Bearer Auth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Use token from /auth/login. Format: Bearer <token>"
        }
    }

    api.authorizations = authorizations
    api.security = "Bearer Auth"
    api.init_app(app)

    # JWT Handlers
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        return jti in blacklist

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"msg": "Missing Authorization Header"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"msg": "Invalid Token"}), 422

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"msg": "Token has expired"}), 401

    # Register API Namespaces
    api.add_namespace(auth_ns)
    api.add_namespace(cat_ns)
    api.add_namespace(prod_ns)
    api.add_namespace(inv_ns)
    api.add_namespace(rep_ns)

    # Uploaded images route
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # FRONT-END UI ROUTE
    @app.route('/minimart')
    def minimart_ui():
        # Make sure /app/templates/minimart.html exists
        return render_template('minimart.html')

    # Redirect root → minimart UI
    @app.route('/')
    def index():
        return redirect('/minimart')

    return app
