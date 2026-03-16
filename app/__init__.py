import os
import logging
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_session import Session
from werkzeug.exceptions import HTTPException

from app.config import config

# Initialize extensions
db = SQLAlchemy()
csrf = CSRFProtect()
bcrypt = Bcrypt()
migrate = Migrate()
session = Session()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(config_name='default'):
    """Application factory for creating Flask app."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Add Python built-ins to Jinja2 globals
    app.jinja_env.globals.update(
        str=str,
        int=int,
        float=float,
        list=list,
        dict=dict,
        range=range,
        len=len,
        enumerate=enumerate,
        zip=zip
    )
    
    # Register custom Jinja2 filters
    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%b %d, %Y'):
        if value is None:
            return ''
        if isinstance(value, str):
            return value
        return value.strftime(format)
    
    @app.template_filter('markdown')
    def markdown_filter(text):
        """Simple markdown-like formatting."""
        if not text:
            return ''
        # Basic markdown-like formatting
        import re
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
        text = re.sub(r'\n', '<br>', text)
        return text
    
    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    session.init_app(app)
    
    # Initialize login manager from user_loader module
    from app.utils.user_loader import login_manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Create upload folder if not exists
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder and not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.courses import courses_bp
    from app.routes.materials import materials_bp
    from app.routes.quizzes import quizzes_bp
    from app.routes.attendance import attendance_bp
    from app.routes.marks import marks_bp
    from app.routes.ai import ai_bp
    from app.routes.career import career_bp
    from app.routes.analytics import analytics_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(materials_bp)
    app.register_blueprint(quizzes_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(marks_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(career_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp)
    
    # ==================== ERROR HANDLERS ====================
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors."""
        logger.warning(f"404 error: {request.path}")
        return render_template('error.html', error_code=404, 
                               error_message="Page Not Found",
                               error_description="The page you're looking for doesn't exist or has been moved."), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        logger.error(f"500 error: {error}")
        # Rollback any failed database transactions
        db.session.rollback()
        return render_template('error.html', error_code=500, 
                               error_message="Internal Server Error",
                               error_description="Something went wrong on our end. Please try again later."), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 Forbidden errors."""
        logger.warning(f"403 error: {request.path}")
        return render_template('error.html', error_code=403, 
                               error_message="Access Forbidden",
                               error_description="You don't have permission to access this resource."), 403

    @app.errorhandler(400)
    def bad_request_error(error):
        """Handle 400 Bad Request errors."""
        logger.warning(f"400 error: {request.path} - {error}")
        return render_template('error.html', error_code=400, 
                               error_message="Bad Request",
                               error_description="The request couldn't be understood. Please check your input."), 400

    @app.errorhandler(405)
    def method_not_allowed_error(error):
        """Handle 405 Method Not Allowed errors."""
        logger.warning(f"405 error: {request.method} {request.path}")
        return render_template('error.html', error_code=405, 
                               error_message="Method Not Allowed",
                               error_description="The method you used is not allowed for this resource."), 405

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle all HTTP exceptions."""
        logger.warning(f"HTTP exception: {error.code} - {error.description}")
        return render_template('error.html', error_code=error.code, 
                               error_message=error.name,
                               error_description=error.description), error.code

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all unhandled exceptions."""
        logger.exception(f"Unhandled exception: {error}")
        # Rollback any failed database transactions
        db.session.rollback()
        return render_template('error.html', error_code=500, 
                               error_message="Internal Server Error",
                               error_description="An unexpected error occurred. Our team has been notified."), 500

    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
