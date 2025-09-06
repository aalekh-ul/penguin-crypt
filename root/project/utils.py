import shutil,os,subprocess,re
from functools import wraps
from flask import session, redirect,current_app, url_for
from .models import VaultEntry
from . import db
from functools import wraps
from nacl.secret import SecretBox
import json


#decorator for login check
def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not os.path.exists(current_app.config['instance_path']) or not os.path.exists(os.path.join(current_app.config['instance_path'], "vault.db")):
            return redirect(url_for('auth_bp.signup_page'))
        if 'authenticated' not in session or not session['authenticated']:
            return redirect(url_for('auth_bp.login_page'))
        return view_func(*args, **kwargs)
    return wrapper

def load_or_create_file(key,data):
    box = SecretBox(key)
    if os.path.exists(current_app.config['enc_file_path']):
        try:
            with open(current_app.config['enc_file_path'],'rb') as f:
                read = f.read()
                sec_json_bytes = box.decrypt(read)
                sec_json = sec_json_bytes.decode('utf-8')
                return json.loads(sec_json),True
        except:
            return None,False
    else:
        encrypted = box.encrypt(json.dumps(data).encode('utf-8')) 
        with open(current_app.config['enc_file_path'],'wb') as f:
            f.write(encrypted)
        

def delete_local_folder():
    folder = current_app.config['UPLOAD_FOLDER']
    for item in os.listdir(folder):
        item_path = os.path.join(folder, item)
        shutil.rmtree(item_path) if os.path.isdir(item_path) else os.remove(item_path)

##data insertion function
def insert_vault_entry(entry_type, name, encrypted_passphrase):
    new_entry = VaultEntry(
        entry_type=entry_type,
        name=name,
        passphrase_enc=encrypted_passphrase
    )
    db.session.add(new_entry)
    db.session.commit()

#data deletion function
def delete_vault_entry(cred_id):
    rec = VaultEntry.query.get_or_404(cred_id)
    db.session.delete(rec)
    db.session.commit()


#gpg check function
def check_gpg_installed():
    if not shutil.which('gpg'):
        return False
    else:
        return True
    
#email extraction
def extract_emails_from_gpg():
    email_pattern = re.compile(r'<([^>]+)>')
    output = subprocess.run(
        ['gpg', '--list-keys'],
        check=True,
        text=True,
        capture_output=True 
    )
    emails = email_pattern.findall(output.stdout)
    return emails


#assym crypt function
def crypt_asym_files(algo,gpg_mode,email,filepath):
    if algo != 'gpg':
        return False,None,None,'Invalid algorithm selected'
    
    valid_emails = extract_emails_from_gpg()
    if email not in valid_emails:
        return False,None,None,'Invalid email address'
    
    try:
        command_asym = ['gpg','--encrypt','--recipient',f'{email}',f'{filepath}']
        subprocess.run(command_asym,check=True)
        return True,filepath + '.gpg', " ".join(command_asym),None
    except Exception as e:
        return False, None, None, e
    
#sym crypt function
def crypt_sym_files(algo,gpg_mode,gpg_sym_algo,passphrase,filepath):
    if algo != 'gpg':
        return False,None,None,'Invalid algorithm selected'
    
    VALID_GPG_SYM_ALGOS = ['aes256', 'aes192', 'aes128']
    if gpg_sym_algo not in VALID_GPG_SYM_ALGOS:
        return False, None, None, 'Invalid gpg symmetric algorithm selected'

    try:
        command = [
            'gpg', '--symmetric','--cipher-algo',f'{gpg_sym_algo}','--batch','--yes','--pinentry-mode','loopback','--passphrase',f'{passphrase}',f'{filepath}'
        ]
        subprocess.run(command,check=True)
        return True, filepath + '.gpg'," ".join(command),None
    
    except Exception as e:
        return False, None, None, e
    
def decrypt_util_files(passphrase,output,upload_path):
        try:
            result = subprocess.run([
                'gpg', '--batch', '--yes', '--pinentry-mode', 'loopback',
                '--passphrase', passphrase,
                '--output', output,
                '--decrypt', upload_path
            ], check=True,capture_output=True,text=True)
            return True,None
        except subprocess.CalledProcessError as e:
            return False,e.stderr



def extract_info():
    result = subprocess.run(['gpg', '--list-keys'], check=True, capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()

    result_data = []
    current_key = {}

    for line in lines:
        line = line.strip()

        if line.startswith('pub'):
            # Save the previous key if exists
            if current_key:
                result_data.append(current_key)
                current_key = {}

            parts = line.split()
            if len(parts) >= 3:
                current_key['created'] = parts[2]

        elif re.match(r'^[A-F0-9]{40}$', line):
            current_key['key_id'] = line.strip()

        elif line.startswith('uid'):
            match = re.search(r'<(.+?)>', line)
            if match:
                current_key['email'] = match.group(1)

    if current_key:
        result_data.append(current_key)

    return result_data


