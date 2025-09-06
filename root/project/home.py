from flask import Blueprint, render_template,session,redirect,url_for,flash

index = Blueprint('index',__name__,template_folder='templates')


@index.route('/dashboard')
def landing_page():
    if 'authenticated' not in session or not session['authenticated']:
        return redirect(url_for('auth_bp.login_page'))
    return render_template('index.html')













