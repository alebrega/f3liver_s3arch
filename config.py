#configuration file for votr
import os

INSTALL_LINK='#'

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

if (os.environ['FLASK_ENV']=='development'):
    HOST = "127.0.0.1:5000"
    HTTPS="http://"
    DEBUG = True
    MYSQL_DATABASE_HOST = "localhost"
    MYSQL_DATABASE_USER = "root"
    MYSQL_DATABASE_DB = "ebdb"
    MYSQL_DATABASE_PASSWORD = ""
    REDIRECT_URI= "http://127.0.0.1:5000/app/install_ok"
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
else:
    HOST = "feliver.com"
    HTTPS="https://"
    DEBUG = False
    MYSQL_DATABASE_HOST = "aaqudwzjpiyvtl.cgx6t1co0xhl.us-east-1.rds.amazonaws.com:3306"
    MYSQL_DATABASE_USER = "FeLiVer"
    MYSQL_DATABASE_DB = "ebdb"
    MYSQL_DATABASE_PASSWORD = "FeLiVerPasS"
    REDIRECT_URI= "https://feliver.com/app/install_ok"
    CELERY_BROKER_URL='redis://127.0.0.1:6379',
    CELERY_RESULT_BACKEND='redis://127.0.0.1:6379'

sql_string = 'mysql+pymysql://'+MYSQL_DATABASE_USER+':'+MYSQL_DATABASE_PASSWORD+'@'+MYSQL_DATABASE_HOST+'/'+MYSQL_DATABASE_DB
SECRET_KEY = '0d44aecebcdbbc97c095a6123b6f2efca0' # keep this key secret during production
SQLALCHEMY_DATABASE_URI = sql_string
SQLALCHEMY_TRACK_MODIFICATIONS = False

SESSION_TYPE = 'cookie'
