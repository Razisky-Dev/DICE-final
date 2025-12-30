import pytest
from werkzeug.security import generate_password_hash
from app import app, db, User, Store, Transaction

@pytest.fixture(scope='function')
def test_client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()
        
        # create admin user
        admin = User(
            first_name='Admin', 
            last_name='User', 
            username='admin_test', 
            email='admin_test@dice.com', 
            mobile='0000000000', 
            password=generate_password_hash('test'), 
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        
    with app.test_client() as client:
        yield client
        
    with app.app_context():
        db.session.remove()
        db.drop_all()

def login_as_admin(client):
    return client.post('/admin/login', data={'email': 'admin_test@dice.com', 'password': 'test'}, follow_redirects=True)

def test_admin_users_route(test_client):
    login_as_admin(test_client)
    response = test_client.get('/admin/users')
    assert response.status_code == 200
    assert b'User Management' in response.data

def test_admin_stores_route(test_client):
    login_as_admin(test_client)
    response = test_client.get('/admin/stores')
    assert response.status_code == 200
    assert b'Store Management' in response.data

def test_admin_transactions_route(test_client):
    login_as_admin(test_client)
    response = test_client.get('/admin/transactions')
    assert response.status_code == 200
    assert b'Transaction History' in response.data
