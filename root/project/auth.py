from .password_utils import is_strong_password,derive_key
from .utils import delete_local_folder,load_or_create_file
from project import db
from flask import Blueprint, render_template,session,redirect,url_for,request,flash,current_app
import os,json,base64,hashlib

auth_bp = Blueprint('auth_bp',__name__,template_folder='templates')

@auth_bp.route('/', methods=['GET', 'POST'])
def signup_page():
    db_path = os.path.join(current_app.config['instance_path'], "vault.db")
    #print(db_path)
    if os.path.exists(db_path):
        return redirect(url_for('auth_bp.login_page'))
    
    if request.method == 'POST':
        master_pass = request.form.get('password')
        hash_of_master_pass = hashlib.sha256(master_pass.encode()).digest()
        if is_strong_password(master_pass):
            salt = os.urandom(16)
            key_hash = derive_key(master_pass, salt)
            current_app.config['SQLCIPHER_KEY'] = key_hash
            #db.engine.dispose()
            from .models import VaultEntry
            with current_app.app_context():
                db.create_all()

            data = {
                "salt": base64.b64encode(salt).decode(),
                "key": key_hash
            }  
            load_or_create_file(hash_of_master_pass,data)
            return redirect(url_for('auth_bp.login_page'))
            
        else:
            flash('Password does not match the criteria', 'danger')
            return render_template('signup.html')
    return render_template('signup.html')


@auth_bp.route('/login/',methods=['GET','POST'])
def login_page():
    if request.method == 'POST':
        login_pass = request.form.get('password')
        hash_of_master_pass = hashlib.sha256(login_pass.encode()).digest()
        db_path = os.path.join(current_app.instance_path, "vault.db")
        if not os.path.exists(current_app.config['enc_file_path']) and  not os.path.exists(db_path):
            return redirect(url_for('auth_bp.signup_page'))
        else:
            sec_json, status = load_or_create_file(hash_of_master_pass,data=False)
            if status == False:
                flash('Invalid password. Please try again.','danger')
                return render_template('login.html')
            else:
                
                salt = sec_json['salt']
                salt_bytes = base64.b64decode(salt)
                stored_key = sec_json['key']
                supplied_key_hash = derive_key(login_pass,salt_bytes)
                if supplied_key_hash == stored_key:
                    current_app.config['SQLCIPHER_KEY'] = supplied_key_hash
                    session['authenticated'] = True
                    # flash('Vault unlocked successfully!', 'success')
                    return redirect(url_for('index.landing_page'))
                else:
                    flash('Invalid password. Please try again.', 'danger')
                    return render_template('login.html')
                


    return render_template('login.html')


@auth_bp.route('/logout/')
def logout():
    session.clear()
    current_app.config['SQLCIPHER_KEY'] = None
    delete_local_folder()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth_bp.login_page'))
