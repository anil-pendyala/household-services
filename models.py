from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///household_services.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy()
db.init_app(app)  # Bind SQLAlchemy instance to the Flask app

# Models
class Customers(db.Model):
    __tablename__ = 'customers'
    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    pincode = db.Column(db.String(6))
    is_blocked = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    # service_requests = db.relationship('Requests', back_populates='customer', lazy=True)


class Professionals(db.Model):
    __tablename__ = 'professionals'
    professional_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.service_id'))
    experience = db.Column(db.Float, nullable=False)
    doc_link = db.Column(db.String(300), nullable=False)
    address = db.Column(db.Text)
    pincode = db.Column(db.String(6))
    services_did = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float)
    is_approved = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    # service = db.relationship('Services', backref='professionals', lazy=True)


class Services(db.Model):
    __tablename__ = 'services'
    service_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    service_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    base_price = db.Column(db.Integer, nullable=False)
    # professionals = db.relationship('Professionals', backref='service', lazy=True)
    # requests = db.relationship('Requests', backref='service', lazy=True)


class Requests(db.Model):
    __tablename__ = 'requests'
    request_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.service_id'), nullable=False)
    requirements = db.Column(db.Text, nullable=True)
    service_date = db.Column(db.Date, nullable=False)
    service_time = db.Column(db.String(20), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.professional_id'), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Pending')
    # service = db.relationship('Services', back_populates='requests', lazy=True)
    # professional = db.relationship('Professionals', back_populates='requests', lazy=True)


# Create tables
with app.app_context():
    db.create_all()

print("Database and tables created successfully!")
