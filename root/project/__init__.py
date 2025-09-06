import os
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()

def create_project():

    home_path = os.path.expanduser('~')
    UPLOAD_FOLDER = os.path.join(home_path,'.penguin-crypt','uploads')
    instance_path = os.path.join(home_path,'.penguin-crypt','instance')
    enc_file_path = os.path.join(home_path,'.penguin-crypt','file.enc')

    # UPLOAD_FOLDER = os.path.join('/app/penguin-crypt','uploads')
    # instance_path = os.path.join('/app/penguin-crypt','instance')
    # enc_file_path = os.path.join('/app/penguin-crypt','file.enc')

    
    app = Flask(__name__)
    #app = Flask(__name__)



    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['enc_file_path'] = enc_file_path
    app.config['instance_path'] = instance_path
    app.secret_key = 'super secret key'

    os.makedirs(UPLOAD_FOLDER,exist_ok=True)
    os.makedirs(instance_path,exist_ok=True)
  
    db_path = os.path.join(instance_path, "vault.db")
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite+pysqlcipher://:@/{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


    db.init_app(app)

  
    from .home import index
    from .files import files_page
    from .folders import folder_page
    from .keys import keys_page
    from .vault import vault_page
    from .auth import auth_bp

    app.register_blueprint(index, url_prefix='/')
    app.register_blueprint(files_page, url_prefix='/')
    app.register_blueprint(folder_page, url_prefix='/')
    app.register_blueprint(keys_page, url_prefix='/')
    app.register_blueprint(vault_page, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/')



    @event.listens_for(Engine, "connect")
    def set_cipher_pragma(dbapi_connection, connection_record):
        key = current_app.config.get('SQLCIPHER_KEY')
        if key:
            #print("from handler: ",key)
            cursor = dbapi_connection.cursor()
            #cursor.execute(f"PRAGMA key = 'test';")
            cursor.execute(f"PRAGMA key = '{key}';")
            cursor.close()

    return app
