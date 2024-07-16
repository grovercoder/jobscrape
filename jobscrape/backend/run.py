from werkzeug.security import generate_password_hash
from jobscrape.backend.app import create_app, login_manager
from jobscrape.db import DB
from jobscrape.models import User

app = create_app()

# Create the tables
mydb = DB()
mydb.setup_db()
session = mydb.get_session()

# Add some users (for demo purposes)
if not session.query(User).filter_by(username='admin').first():
    admin_user = User(
        email='admin@example.com',
        username='admin',
        password=generate_password_hash('admin123', method='pbkdf2:sha256')
    )
    session.add(admin_user)
    session.commit()


if __name__ == '__main__':
    app.run(debug=True)
