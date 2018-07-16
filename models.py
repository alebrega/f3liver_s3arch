
from flask_sqlalchemy import SQLAlchemy
from flask_validator import Validator,ValidateInteger, ValidateString, ValidateURL
from sqlalchemy.orm import relationship, backref
from pprint import pprint


# create a new SQLAlchemy object
db = SQLAlchemy()

# Base model that for other models to inherit from
class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(),
            onupdate=db.func.current_timestamp())


class Customer(Base):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(500), unique=False)
    hmac = db.Column(db.String(500), unique=False)
    shop = db.Column(db.String(120), unique=True)
    products = relationship("Product",secondary="installs")

    def __init__(self, code=None, hmac=None,shop=None):
        self.code = code
        self.hmac = hmac
        self.shop = shop

    def __repr__(self):
        return '<Customer %r>' % (self.shop)

    @classmethod
    def __declare_last__(cls):
        ValidateString(Customer.code,False,True)
        ValidateString(Customer.hmac,False,True)
        ValidateString(Customer.shop,False,True)

class Product(Base):
    __tablename__ = 'products'
    image_src = db.Column(db.Text, unique=False)
    product_id = db.Column(db.Text, unique=False)
    shop = db.Column(db.String(120), unique=False)
    download = db.Column(db.Boolean, unique=False, default=False)
    indexed = db.Column(db.Boolean, unique=False, default=False)
    customers = relationship("Customer",secondary="installs")

    def __init__(self, product_id=None, image_src=None,shop=None):
        self.image_src = image_src
        self.product_id = product_id
        self.shop = shop
        self.download = False
        self.indexed = False

    def __repr__(self):
        return '<Product %r>' % (self.id)

    @classmethod
    def __declare_last__(cls):
        ValidateString(Product.id,False,True)
        ValidateURL(Product.image_src,False,True)

class ScriptTag(Base):
    __tablename__ = 'script_tags'
    script_id = db.Column(db.Text, unique=False)
    display_scope =  db.Column(db.Text, unique=False)
    shop = db.Column(db.String(120), unique=False)

    def __init__(self, script_id=None, display_scope=None,shop=None):
        self.script_id = script_id
        self.display_scope = display_scope
        self.shop = shop

    def __repr__(self):
        return '<ScriptTag %r>' % (self.id)

class Install(Base):
    __tablename__ = 'installs'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))

    customer = relationship(Customer, backref=backref("installs", cascade="all, delete-orphan"))
    product = relationship(Product, backref=backref("installs", cascade="all, delete-orphan"))
