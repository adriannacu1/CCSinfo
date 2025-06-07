from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Configure the app
    app.config['SECRET_KEY'] = 'your-very-secret-key-change-this-in-production'  # Change this to a random secret key
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes

    # MySQL configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/ccs_info'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize SQLAlchemy and bcrypt with app
    db.init_app(app)
    bcrypt.init_app(app)

    # Register routes
    from app.routes import register_routes
    register_routes(app)

    return app

# Create the app instance
app = create_app()
