from flask import Blueprint, render_template, request,current_app, flash, redirect, url_for,send_from_directory
import uuid,tarfile
from werkzeug.utils import secure_filename
from .utils import *


folder_page = Blueprint('folder_page',__name__,template_folder='templates')

@folder_page.route('/folders/')
@login_required
def folders_home():
    return render_template('folders_home.html')


@folder_page.route('/folder/encrypt')
@login_required
def folders_enc():
    if not check_gpg_installed():
        flash('gpg binary not found on the system','danger')
    return render_template('folders_enc.html')

@folder_page.route('/folder/decrypt')
@login_required
def folders_dec():
    if not check_gpg_installed():
        flash('gpg binary not found on the system','danger')
    return render_template('folders_dec.html')


def create_tarball(output_filename, source_dir):
    try:
        path = source_dir + '/' + output_filename
        with tarfile.open(path, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
        #flash(f"Successfully created {output_filename}",'success')
        return True, path, None
    except Exception as e:
        return False, None, e



@folder_page.route('/folders/encrypt/upload/',methods=['GET','POST'])
@login_required
def encrypt_folder():
    if request.method == 'POST':
        folder = request.files.getlist('folder')

        if folder:
            first_file_name = folder[0].filename
            base_folder = first_file_name.split('/')[0]
            base_folder = secure_filename(base_folder)
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'],base_folder)
            #save the folder on upload folder
            for file in folder:
                relative_path = file.filename
                inner_path = "/".join(relative_path.split('/')[1:])
                final_path = os.path.join(upload_folder,inner_path)
                os.makedirs(os.path.dirname(final_path),exist_ok=True)
                file.save(final_path)
            #flash(f'folder uploaded {upload_folder}','success')
            output_filename = upload_folder.split('/')[-1] + ".tar.gz"
            status_tar,upload_path,error = create_tarball(output_filename,current_app.config['UPLOAD_FOLDER']) #tar the uploaded folder

            algo = request.form.get('algorithm') #gpg
            algo = algo.lower()
            gpg_mode = request.form.get('gpg_mode') # 'symmetric' or 'asymmetric'
            gpg_mode = gpg_mode.lower()

            if status_tar:
                if gpg_mode == 'symmetric':
                    gpg_sym_algo = request.form.get('gpg_sym_algo')  # symmetric cipher AES256, AES192, AES128
                    gpg_sym_algo = gpg_sym_algo.lower()
                    passphrase = request.form.get('passphrase') # passphrase for file enc
                    status,encrypted_file,command,error = crypt_sym_files(algo,gpg_mode,gpg_sym_algo,passphrase,upload_path)
                    if status:
                        flash('✅ Folder encrypted successfully!', 'success')
                        insert_vault_entry('folder',base_folder,passphrase)
                        return render_template('folders_enc.html',encrypted_file=os.path.basename(encrypted_file))
                    else:
                        flash(f'❌ Encryption Failed, {error}', 'danger')
                        return redirect(url_for("folder_page.folders_enc"))
                    
                elif gpg_mode == 'asymmetric':
                    email = request.form.get('gpg_recp_email')
                    status,encrypted_file,command,error = crypt_asym_files(algo,gpg_mode,email,upload_path)
                    if status:
                        flash('✅ Folder encrypted successfully!', 'success')
                        return render_template('folders_enc.html', encrypted_file=os.path.basename(encrypted_file))
                    else:
                        flash(f'❌ Encryption Failed, {error}', 'danger')

                        return redirect(url_for("folder_page.folders_enc"))
                    
                else:
                    flash('❌ Encryption Failed, Invalid gpg mode selected!','danger')
                    return redirect(url_for("folder_page.folders_enc"))
            
            else:
                flash(f"Error creating tarball: {error}",'danger')
                return redirect(url_for("folder_page.folders_enc"))
                    
        else:
            flash("No folder uploaded", "danger")
            return redirect(url_for("folder_page.folders_enc"))
        
        
@folder_page.route('/folders/decrypt/upload',methods=['GET','POST'])
@login_required
def decrypt_files():
    if request.method == 'POST':
        file = request.files['encrypted_file'] #.tar.gz.gpg
        if file:
            if file.filename.endswith(".tar.gz.gpg"):
                filename = secure_filename(file.filename)
                unique_id = uuid.uuid4()
                filename = f'{unique_id}'+ '_' +f'{filename}'
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                print(upload_path)
                passphrase = request.form.get('passphrase')
                file.save(upload_path)
                output = upload_path.removesuffix('.gpg')
                status_decrypt, error_decrypt = decrypt_util_files(passphrase,output,upload_path)
                if status_decrypt:
                    flash('✅ Folder decrypted successfully','success')
                    return render_template('folders_dec.html',decrypted_folder = os.path.basename(output))
                else:
                    flash(f'❌ Decryption Failed, {error_decrypt}', 'danger')
                    return render_template('folders_dec.html')
            else:
                flash('Uploaded folder is not accepted for decryption!','danger')
                return render_template('folders_dec.html')
        else:
            flash('No file uploaded!', 'danger')
            return render_template('folders_dec.html')
        

@folder_page.route('/folder/download/<filename>')
@login_required
def download_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
