from flask import Blueprint, render_template, request,current_app, flash, redirect, url_for,send_from_directory
import uuid
from werkzeug.utils import secure_filename,send_file
from .utils import *


files_page = Blueprint('files_page',__name__,template_folder='templates')

@files_page.route('/files/')
@login_required
def files_home():
    return render_template('files_home.html')


@files_page.route('/files/encrypt')
@login_required
def files_enc():
    if not check_gpg_installed():
        flash('gpg binary not found on the system','danger')
    return render_template('files_enc.html')

@files_page.route('/files/decrypt')
@login_required
def files_dec():
    if not check_gpg_installed():
        flash('gpg binary not found on the system','danger')
    return render_template('files_dec.html')


@files_page.route('/gpg/emails')
@login_required
def get_gpg_emails_api():
    emails = extract_emails_from_gpg()
    return {'emails': emails}


@files_page.route('/files/encrypt/upload/',methods=['GET','POST'])
@login_required
def encrypt_files():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            unique_id = uuid.uuid4()
            filename = f'{unique_id}'+ '_' +f'{filename}'
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            #print(upload_path)
            file.save(upload_path)
            #flash('File uploaded successfully!', 'success')
            
            algo = request.form.get('algorithm')
            algo = algo.lower()
            gpg_mode = request.form.get('gpg_mode') # 'symmetric' or 'asymmetric'
            gpg_mode = gpg_mode.lower()

            if gpg_mode == 'symmetric':
                gpg_sym_algo = request.form.get('gpg_sym_algo')  # symmetric ciphers AES256, AES192, AES128
                gpg_sym_algo = gpg_sym_algo.lower()
                passphrase = request.form.get('passphrase') # passphrase for file enc
                status,encrypted_file,command,error = crypt_sym_files(algo,gpg_mode,gpg_sym_algo,passphrase,upload_path)
                if status:
                    flash('✅ File encrypted successfully!', 'success')
                    insert_vault_entry('file',encrypted_file,passphrase)
                    return render_template('files_enc.html',encrypted_file=os.path.basename(encrypted_file))
                else:
                    flash(f'❌ Encryption Failed, {error}', 'danger')
                    return redirect(url_for('files_page.files_enc'))
                
            elif gpg_mode == 'asymmetric':
                email = request.form.get('gpg_recp_email')
                status,encrypted_file,command,error = crypt_asym_files(algo,gpg_mode,email,upload_path)
                if status:
                    flash('✅ File encrypted successfully!', 'success')
                    return render_template('files_enc.html', encrypted_file=os.path.basename(encrypted_file))
                else:
                    flash(f'❌ Encryption Failed, {error}', 'danger')
                    return redirect(url_for('files_page.files_enc'))
                
            else:
                flash('❌ Encryption Failed, Invalid gpg mode selected!','danger')
                return redirect(url_for('files_page.files_enc'))
            
        else:
            flash('No file uploaded!', 'danger')
            return redirect(url_for('files_page.files_enc'))
        


@files_page.route('/files/decrypt/upload',methods=['GET','POST'])
@login_required
def decrypt_files():
    if request.method == 'POST':
        file = request.files['encrypted_file']
        if file:
            filename = secure_filename(file.filename)
            unique_id = uuid.uuid4()
            filename = f'{unique_id}'+ '_' +f'{filename}'
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            passphrase = request.form.get('passphrase')
            file.save(upload_path)
            output = current_app.config['UPLOAD_FOLDER'] + '/' + filename.rsplit('.',1)[0]
            status_decrypt, error_decrypt = decrypt_util_files(passphrase,output,upload_path)
            if status_decrypt:
                flash('✅ File decrypted successfully','success')
                return render_template('files_dec.html',decrypted_file = os.path.basename(output))
            else:
                flash(f'❌ Decryption Failed, {error_decrypt}', 'danger')
                return render_template('files_dec.html')
        else:
            flash('No file uploaded!', 'danger')
            return redirect(url_for('files_page.files_dec'))

@files_page.route('/files/download/<filename>')
@login_required
def download_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'],filename, as_attachment=True)

     
    





