from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import json
from database import Database
from wiremock_service import WireMockService
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = Database()
wiremock = WireMockService()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        
        user = db.get_user_by_id(session['user_id'])
        if not user or not user['is_admin']:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        user = db.get_user_by_id(session['user_id'])
        if user and user['is_admin']:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = db.verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Admin Routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    users = db.get_all_users()
    wiremock_status = wiremock.test_connection()
    return render_template('admin/dashboard.html', users=users, wiremock_status=wiremock_status)

@app.route('/admin/users/create', methods=['POST'])
@admin_required
def admin_create_user():
    username = request.form.get('username')
    password = request.form.get('password')
    is_admin = request.form.get('is_admin') == 'on'
    
    if not username or not password:
        flash('Username and password are required.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        db.create_user(username, password, is_admin)
        flash(f'User {username} created successfully.', 'success')
    except Exception as e:
        flash(f'Error creating user: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def admin_toggle_user_admin(user_id):
    user = db.get_user_by_id(user_id)
    if user:
        new_status = not user['is_admin']
        db.update_user(user_id, is_admin=new_status)
        flash(f'User admin status updated.', 'success')
    else:
        flash('User not found.', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/users/<int:user_id>/toggle-active', methods=['POST'])
@admin_required
def admin_toggle_user_active(user_id):
    user = db.get_user_by_id(user_id)
    if user:
        new_status = not user['is_active']
        db.update_user(user_id, is_active=new_status)
        flash(f'User active status updated.', 'success')
    else:
        flash('User not found.', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    if user_id == session['user_id']:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if db.delete_user(user_id):
        flash('User deleted successfully.', 'success')
    else:
        flash('Error deleting user.', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/sync-wiremock', methods=['POST'])
@admin_required
def admin_sync_wiremock():
    mappings = db.get_all_active_mappings()
    results = wiremock.sync_all_mappings(mappings)
    
    success_count = sum(1 for r in results if r['success'])
    flash(f'Synced {success_count} of {len(results)} mappings to WireMock.', 'success')
    
    return redirect(url_for('admin_dashboard'))

# User Routes
@app.route('/user')
@login_required
def user_dashboard():
    user_id = session['user_id']
    mappings = db.get_user_mappings(user_id)
    return render_template('user/dashboard.html', mappings=mappings)

@app.route('/user/mappings/create', methods=['GET', 'POST'])
@login_required
def user_create_mapping():
    if request.method == 'POST':
        name = request.form.get('name')
        request_method = request.form.get('request_method')
        request_url = request.form.get('request_url')
        response_status = int(request.form.get('response_status', 200))
        response_body = request.form.get('response_body', '')
        
        # Parse response headers
        response_headers = '{}'
        headers_input = request.form.get('response_headers', '').strip()
        if headers_input:
            try:
                json.loads(headers_input)
                response_headers = headers_input
            except:
                flash('Invalid JSON format for response headers.', 'error')
                return render_template('user/create_mapping.html')
        
        priority = int(request.form.get('priority', 5))
        
        if not all([name, request_method, request_url]):
            flash('Name, method, and URL are required.', 'error')
            return render_template('user/create_mapping.html')
        
        try:
            mapping_id = db.create_mapping(
                session['user_id'], name, request_method, request_url,
                response_status, response_body, response_headers, priority
            )
            
            # Sync to WireMock
            mapping = db.get_mapping_by_id(mapping_id)
            success, result = wiremock.sync_mapping(mapping)
            
            if success:
                flash(f'Mapping "{name}" created and synced to WireMock.', 'success')
            else:
                flash(f'Mapping created but sync failed: {result}', 'warning')
            
            return redirect(url_for('user_dashboard'))
        except Exception as e:
            flash(f'Error creating mapping: {str(e)}', 'error')
    
    return render_template('user/create_mapping.html')

@app.route('/user/mappings/<int:mapping_id>/edit', methods=['GET', 'POST'])
@login_required
def user_edit_mapping(mapping_id):
    mapping = db.get_mapping_by_id(mapping_id, session['user_id'])
    if not mapping:
        flash('Mapping not found.', 'error')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        updates = {
            'name': request.form.get('name'),
            'request_method': request.form.get('request_method'),
            'request_url': request.form.get('request_url'),
            'response_status': int(request.form.get('response_status', 200)),
            'response_body': request.form.get('response_body', ''),
            'priority': int(request.form.get('priority', 5))
        }
        
        # Parse response headers
        headers_input = request.form.get('response_headers', '').strip()
        if headers_input:
            try:
                json.loads(headers_input)
                updates['response_headers'] = headers_input
            except:
                flash('Invalid JSON format for response headers.', 'error')
                return render_template('user/edit_mapping.html', mapping=mapping)
        else:
            updates['response_headers'] = '{}'
        
        try:
            db.update_mapping(mapping_id, session['user_id'], **updates)
            
            # Re-sync to WireMock
            updated_mapping = db.get_mapping_by_id(mapping_id)
            if updated_mapping['is_active']:
                wiremock.sync_all_mappings(db.get_all_active_mappings())
            
            flash('Mapping updated successfully.', 'success')
            return redirect(url_for('user_dashboard'))
        except Exception as e:
            flash(f'Error updating mapping: {str(e)}', 'error')
    
    return render_template('user/edit_mapping.html', mapping=mapping)

@app.route('/user/mappings/<int:mapping_id>/toggle', methods=['POST'])
@login_required
def user_toggle_mapping(mapping_id):
    mapping = db.get_mapping_by_id(mapping_id, session['user_id'])
    if mapping:
        new_status = not mapping['is_active']
        db.update_mapping(mapping_id, session['user_id'], is_active=new_status)
        
        # Re-sync to WireMock
        wiremock.sync_all_mappings(db.get_all_active_mappings())
        
        flash(f'Mapping {"activated" if new_status else "deactivated"}.', 'success')
    else:
        flash('Mapping not found.', 'error')
    
    return redirect(url_for('user_dashboard'))

@app.route('/user/mappings/<int:mapping_id>/delete', methods=['POST'])
@login_required
def user_delete_mapping(mapping_id):
    if db.delete_mapping(mapping_id, session['user_id']):
        # Re-sync to WireMock
        wiremock.sync_all_mappings(db.get_all_active_mappings())
        flash('Mapping deleted successfully.', 'success')
    else:
        flash('Error deleting mapping.', 'error')
    
    return redirect(url_for('user_dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
