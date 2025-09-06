from flask import Blueprint, request, flash, redirect, url_for, current_app,render_template
from werkzeug.utils import secure_filename
import subprocess,re,os,uuid,string,datetime
from .utils import login_required, insert_vault_entry,delete_vault_entry
from .models import VaultEntry

vault_page = Blueprint('vault_page',__name__,template_folder='templates')


@vault_page.route('/vault/')
@login_required
def vault_home():
    entry_type = request.args.get('type', '').strip()
    from_date = request.args.get('from_date', '').strip()
    to_date = request.args.get('to_date', '').strip()

    query = VaultEntry.query

    if entry_type:
        query = query.filter(VaultEntry.entry_type == entry_type)

    if from_date:
        try:
            from_date_obj = datetime.datetime.strptime(from_date, '%Y-%m-%d')
            query = query.filter(VaultEntry.created_at >= from_date_obj)
        except ValueError:
            flash("Invalid 'From Date' format. Use YYYY-MM-DD.", "danger")

    if to_date:
        try:
            to_date_obj = datetime.datetime.strptime(to_date, '%Y-%m-%d') + datetime.timedelta(days=1)
            query = query.filter(VaultEntry.created_at < to_date_obj)
        except ValueError:
            flash("Invalid 'To Date' format. Use YYYY-MM-DD.", "danger")

    records = query.order_by(VaultEntry.created_at.desc()).all()

    return render_template('vault.html', records=records)


@vault_page.route('/vault/addcreds/',methods=['POST'])
@login_required
def add_creds():
    if request.method == 'POST':
        cred_name = request.form.get('cred_name')
        cred_pass = request.form.get('cred_password')
        insert_vault_entry('creds',cred_name,cred_pass)
        flash('Creds added successfully','success')
        return redirect(url_for('vault_page.vault_home'))
    

@vault_page.route('/vault/delete/<int:cred_id>',methods=['POST'])
@login_required
def delete_cred(cred_id):
    if request.method == 'POST':
        delete_vault_entry(cred_id)
        flash("Credential deleted.", "success")
        return redirect(url_for('vault_page.vault_home'))

