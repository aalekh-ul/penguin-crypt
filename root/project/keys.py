from flask import Blueprint, request, flash, redirect, url_for, current_app,render_template
from werkzeug.utils import secure_filename
import subprocess,re,os,uuid,string
from .utils import extract_info
from .password_utils import is_strong_password
from .utils import insert_vault_entry,login_required



keys_page = Blueprint('keys_page',__name__,template_folder='templates')


@keys_page.route('/keys/')
@login_required
def keys_home():
    return render_template('keys.html')


@keys_page.route('/keys/create')
@login_required
def keys_create_home():
    return render_template('key_create.html')

@keys_page.route('/keys/import')
@login_required
def keys_import_home():
    return render_template('key_import.html')


def sanitize_string(val, allow_email=False):
    val = val.strip()
    if any(c in val for c in '\n\r%'):
        return False,None
    if allow_email:
        if not re.fullmatch(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', val):
            False,None
    else:
        if any(c not in string.printable for c in val):
            False,None
    return True,val


@keys_page.route('/keys/generate',methods=['POST'])
@login_required
def create_key():
    if request.method == 'POST':
        key_type = request.form.get('key_type')
        key_size = request.form.get('key_size')
        expiry = request.form.get('expiry')
        real_name = request.form.get('real_name')
        email = request.form.get('email')
        password = request.form.get('password')
        if not is_strong_password(password):
            flash('Password length should be greater than 8 and it should contain uppercase,lowercase and number','danger')
            return redirect(url_for('keys_page.keys_create_home'))
        if not key_size.isdigit():
            flash('Malicious input for Key Size','danger')
            return redirect(url_for('keys_page.keys_create_home'))
        if key_type not in ['RSA and RSA (default)','DSA and Elgamal','DSA (sign only)','RSA (sign only)']:
            flash('Malicious input for Key Type','danger')
            return redirect(url_for('keys_page.keys_create_home'))
        if not re.fullmatch(r'[0-9]+[dwmoy]?|0', expiry):
            flash('Malicious input for expiry detected','danger')
            return redirect(url_for('keys_page.keys_create_home'))
        if not sanitize_string(real_name):
            flash('Malicious input for name','danger')
            return redirect(url_for('keys_page.keys_create_home'))
        if not sanitize_string(email,allow_email=True):
            flash('Invalid or Malicious email input','danger')
            return redirect(url_for('keys_page.keys_create_home'))
        if key_type in ['RSA and RSA (default)','RSA (sign only)'] and (int(key_size) < 1024 or int(key_size) > 4096) :
            flash('Invalid key size for RSA','danger')
            return redirect(url_for('keys_page.keys_create_home'))
        else:
            if key_type == 'RSA and RSA (default)':
                data = f'%echo Generating a GPG key\nKey-Type: RSA\nKey-Length: {key_size}\nSubkey-Type: RSA\nSubkey-Length: {key_size}\nName-Real: {real_name}\nName-Email: {email}\nExpire-Date: {expiry}\n%commit\n%echo done'
            if key_type == 'RSA (sign only)':
                data = f'%echo Generating a GPG key\nKey-Type: RSA\nKey-Length: {key_size}\nName-Real: {real_name}\nName-Email: {email}\nExpire-Date: {expiry}\n%commit\n%echo done'

        if key_type in ['DSA and Elgamal','DSA (sign only)'] and (int(key_size) < 1024 or int(key_size) > 3072) :
            flash('Invalid key size for DSA','danger')
            return redirect(url_for('keys_page.keys_create_home'))
        else:
            if key_type == 'DSA and Elgamal':
                data = f'%echo Generating a GPG key\nKey-Type: DSA\nKey-Length: {key_size}\nSubkey-Type: ELG-E\nSubkey-Length: {key_size}\nName-Real: {real_name}\nName-Email: {email}\nExpire-Date: {expiry}\n%commit\n%echo done'
            if key_type == 'DSA (sign only)':
                data = f'%echo Generating a GPG key\nKey-Type: DSA\nKey-Length: {key_size}\nName-Real: {real_name}\nName-Email: {email}\nExpire-Date: {expiry}\n%commit\n%echo done'


        config_file_path = current_app.config['UPLOAD_FOLDER'] + '/' +'test.txt'    
        #print(config_file_path)    
        with open(config_file_path,'w') as f:
            f.write(data)
            
        try:
            cmd_keygen = ['gpg','--batch','--pinentry-mode','loopback','--passphrase', f'{password}','--generate-key',f'{config_file_path}']
            testing = subprocess.run(cmd_keygen,check=True,capture_output=True, text=True)
            flash('🔐✅ Key created successfullly','success')
            insert_vault_entry('gpg key',email,password)
            return redirect(url_for('keys_page.keys_create_home'))
        except Exception as e:
            flash(f'Error creating key {e}','danger')
            return redirect(url_for('keys_page.keys_create_home'))
        finally:
            if os.path.exists(config_file_path):
                os.remove(config_file_path)


@keys_page.route('/keys/import', methods=['POST'])
@login_required
def import_key():
    if request.method == 'POST':
        uploaded_file = request.files['gpg_key_file']
        #print(uploaded_file)
        if uploaded_file and uploaded_file.filename and  uploaded_file.filename.lower().endswith('.asc'):
            original_filename = secure_filename(uploaded_file.filename)
            temp_filename = f"{uuid.uuid4()}_{original_filename}"
            temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], temp_filename)

            try:
                uploaded_file.save(temp_path)
                result = subprocess.run(
                    ['gpg', '--import', temp_path],
                    check=True,
                    capture_output=True,
                    text=True
                )

                flash('🔐✅ Key imported successfully.', 'success')
                return redirect(url_for('keys_page.keys_import_home'))

            except subprocess.CalledProcessError as e:
                flash('❌ GPG key import failed.', 'danger')
                flash(e.stderr, 'danger')
                return redirect(url_for('keys_page.keys_import_home'))
            except Exception as e:
                flash(f'❌ Error: {str(e)}', 'danger')
                return redirect(url_for('keys_page.keys_import_home'))
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        else:
            flash("No file uploaded","danger")
            return redirect(url_for('keys_page.keys_import_home'))


@keys_page.route('/keys/manage',methods=['GET'])
@login_required
def manage_keys():
    payload = extract_info()
    return render_template('key_manage.html',keys = payload)


@keys_page.route('/keys/manage/delete',methods=['POST'])
@login_required
def delete_keys():
    if request.method == "POST":
        key_mail = request.form.getlist('selected_keys')
        for key_id in key_mail:
            #print(key_id)
            try:
                result = subprocess.run(['gpg','--batch','--yes','--delete-secret-keys',key_id],check=True,capture_output=True,text=True)
                flash('✅ Secret Deleted Successfully','success')
            except subprocess.CalledProcessError as e:
                    flash(f'❌ Error {e.stderr}','danger')
            try:
                result = subprocess.run(['gpg','--batch','--yes','--delete-keys',key_id],check=True,capture_output=True,text=True)
                flash('✅ Public key Deleted Successfully','success')
            except subprocess.CalledProcessError as e:
                flash(f'❌ Error {e.stderr}','danger')   
        return redirect(url_for('keys_page.manage_keys'))

