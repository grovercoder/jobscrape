# from jobscrape.backend.app import create_app

# app = create_app()

# from flask import Flask
# from flask_login import LoginManager
# from jobscrape.backend.routes import bp as main_bp

# login_manager = LoginManager()
# login_manager.login_view = 'login'

# def create_app():
#     print('In create_app()')
#     app = Flask(__name__)
#     app.config.from_object('jobscrape.backend.config.Config')

#     login_manager.init_app(app)

#     with app.app_context():
#         app.register_blueprint(main_bp)

#     print(app)
#     return app

