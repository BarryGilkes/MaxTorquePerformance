import os
from app import create_app, db
from app.models import User

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db}

@app.cli.command()
def init_db():
    db.create_all()
    print('Database initialized')

@app.cli.command()
def create_admin():
    email = input('Admin email: ')
    password = input('Password: ')
    if User.query.filter_by(email=email).first():
        print('User already exists')
        return
    admin = User(email=email)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f'Admin user {email} created')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
