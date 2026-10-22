import os
import secrets
import hashlib
import sqlite3
from functools import wraps
from datetime import datetime

from flask import (Flask, render_template, request, jsonify,
                   session, redirect, url_for, abort, send_from_directory)
from werkzeug.utils import secure_filename

# ── App Configuration ──────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['DATABASE'] = os.environ.get('DATABASE_PATH', 'database.db')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Database Helper ────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# ── Security Helpers ───────────────────────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_csrf():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

def verify_csrf(token):
    return token and secrets.compare_digest(session.get('csrf_token', ''), token)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            if request.path.startswith('/admin/api/'):
                return jsonify({'error': 'Admin login required'}), 401
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ── Security Headers Middleware ────────────────────────────────────────────────
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), camera=(), microphone=()'
    # Allow frames only for the Google Maps embed origin
    if request.endpoint not in ('admin_login', 'admin_dashboard'):
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

@app.context_processor
def inject_csrf():
    return dict(csrf_token=generate_csrf())

# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html', is_admin=bool(session.get('admin_logged_in')))

@app.route('/residents')
def residents():
    return render_template('residents.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/api/residents', methods=['GET'])
def api_residents():
    conn = get_db()
    rows = conn.execute('SELECT * FROM residents ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/gallery', methods=['GET'])
def api_gallery():
    category = request.args.get('category', 'all')
    conn = get_db()
    if category == 'all':
        rows = conn.execute('SELECT * FROM gallery_images ORDER BY created_at DESC').fetchall()
    else:
        rows = conn.execute(
            'SELECT * FROM gallery_images WHERE category = ? ORDER BY created_at DESC',
            (category,)
        ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    full_name      = str(data.get('full_name', '')).strip()[:200]
    contact_number = str(data.get('contact_number', '')).strip()[:50]
    email          = str(data.get('email', '')).strip()[:200]
    inquiry        = str(data.get('inquiry', '')).strip()[:2000]
    csrf_token     = data.get('csrf_token', '')

    if not verify_csrf(csrf_token):
        return jsonify({"error": "Invalid CSRF token"}), 403

    if not all([full_name, contact_number, email, inquiry]):
        return jsonify({"error": "All fields are required"}), 400

    if '@' not in email or '.' not in email:
        return jsonify({"error": "Please enter a valid email address."}), 400

    conn = get_db()
    conn.execute(
        'INSERT INTO contacts (full_name, contact_number, email, inquiry) VALUES (?, ?, ?, ?)',
        (full_name, contact_number, email, inquiry)
    )
    conn.commit()
    conn.close()
    return jsonify({"success": "Inquiry received"}), 201

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        csrf     = request.form.get('csrf_token', '')

        if not verify_csrf(csrf):
            error = 'Session expired. Please refresh and try again.'
        else:
            pwd_hash = hashlib.sha256(password.encode()).hexdigest()
            conn = get_db()
            user = conn.execute(
                'SELECT * FROM admin_users WHERE username = ? AND password_hash = ?',
                (username, pwd_hash)
            ).fetchone()
            conn.close()
            if user:
                session['admin_logged_in'] = True
                session['admin_user'] = username
                return redirect(url_for('admin_dashboard'))
            else:
                error = 'Invalid credentials. Please try again.'

    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db()
    inquiries = conn.execute('SELECT * FROM contacts ORDER BY created_at DESC').fetchall()
    residents = conn.execute('SELECT * FROM residents ORDER BY created_at DESC').fetchall()
    gallery   = conn.execute('SELECT * FROM gallery_images ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin.html',
                           inquiries=[dict(i) for i in inquiries],
                           residents=[dict(r) for r in residents],
                           gallery=[dict(g) for g in gallery])

# ── Admin API: Gallery Upload ──────────────────────────────────────────────────
@app.route('/admin/api/gallery/upload', methods=['POST'])
@admin_required
def admin_upload_gallery():
    if not verify_csrf(request.form.get('csrf_token', '')):
        return jsonify({'error': 'Invalid CSRF token'}), 403

    if 'image' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['image']
    title    = request.form.get('title', 'Untitled').strip()[:200]
    category = request.form.get('category', 'private_suite').strip()
    availability = request.form.get('availability', 'Available').strip()

    filename = file.filename or ''
    if filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(filename):
        return jsonify({'error': 'File type not allowed'}), 400

    filename = secure_filename(filename)
    # Prepend timestamp to avoid collisions
    unique_name = f"{int(datetime.now().timestamp())}_{filename}"
    save_path   = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file.save(save_path)

    url = f'/static/uploads/{unique_name}'

    conn = get_db()
    conn.execute(
        'INSERT INTO gallery_images (title, category, filename, url, availability) VALUES (?, ?, ?, ?, ?)',
        (title, category, unique_name, url, availability)
    )
    conn.commit()
    img_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()

    return jsonify({'success': True, 'id': img_id, 'url': url, 'title': title}), 201

@app.route('/admin/api/gallery/delete/<int:img_id>', methods=['DELETE'])
@admin_required
def admin_delete_gallery(img_id):
    conn = get_db()
    row = conn.execute('SELECT filename FROM gallery_images WHERE id = ?', (img_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Image not found'}), 404

    # Delete file from disk
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], row['filename'])
    if os.path.exists(file_path):
        os.remove(file_path)

    conn.execute('DELETE FROM gallery_images WHERE id = ?', (img_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ── Admin API: Resident Management ────────────────────────────────────────────
@app.route('/admin/api/residents/add', methods=['POST'])
@admin_required
def admin_add_resident():
    if not verify_csrf(request.form.get('csrf_token', '')):
        return jsonify({'error': 'Invalid CSRF token'}), 403

    name     = request.form.get('name', '').strip()[:200]
    college  = request.form.get('college', '').strip()[:300]
    major    = request.form.get('major', '').strip()[:200]
    category = request.form.get('category', 'general').strip()

    if not all([name, college, major]):
        return jsonify({'error': 'All fields are required'}), 400

    image_url = '/static/img/avatar.png'
    if 'photo' in request.files:
        file = request.files['photo']
        filename = file.filename or ''
        if filename and allowed_file(filename):
            filename    = secure_filename(filename)
            unique_name = f"resident_{int(datetime.now().timestamp())}_{filename}"
            save_path   = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            file.save(save_path)
            image_url = f'/static/uploads/{unique_name}'

    conn = get_db()
    conn.execute(
        'INSERT INTO residents (name, college, major, image_url, category) VALUES (?, ?, ?, ?, ?)',
        (name, college, major, image_url, category)
    )
    conn.commit()
    res_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return jsonify({'success': True, 'id': res_id, 'image_url': image_url}), 201

@app.route('/admin/api/residents/delete/<int:res_id>', methods=['DELETE'])
@admin_required
def admin_delete_resident(res_id):
    conn = get_db()
    row = conn.execute('SELECT image_url FROM residents WHERE id = ?', (res_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Resident not found'}), 404

    # Remove uploaded photo if it's not the default avatar
    if row['image_url'] and '/uploads/' in row['image_url']:
        fname = row['image_url'].rsplit('/', 1)[-1]
        fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
        if os.path.exists(fpath):
            os.remove(fpath)

    conn.execute('DELETE FROM residents WHERE id = ?', (res_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ── Admin API: Delete Inquiry ──────────────────────────────────────────────────
@app.route('/admin/api/contacts/delete/<int:cid>', methods=['DELETE'])
@admin_required
def admin_delete_contact(cid):
    conn = get_db()
    conn.execute('DELETE FROM contacts WHERE id = ?', (cid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    from init_db import init_db
    init_db()
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5001)),
        debug=os.environ.get('FLASK_ENV', '').lower() == 'development'
    )
