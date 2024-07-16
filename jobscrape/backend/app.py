from flask import Flask
from jobscrape.backend.routes import bp as main_bp
from jobscrape.backend.loginmanager import login_manager

def create_app():
    print('In create_app()')
    app = Flask(__name__)
    app.config.from_object('jobscrape.backend.config.Config')

    login_manager.init_app(app)

    with app.app_context():
        app.register_blueprint(main_bp)

    print(app)
    return app

