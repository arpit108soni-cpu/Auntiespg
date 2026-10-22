import sqlite3
import hashlib
import os

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # ── Contacts Table ─────────────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            contact_number TEXT NOT NULL,
            email TEXT,
            inquiry TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    def table_has_column(table, column):
        cursor.execute(f"PRAGMA table_info({table})")
        return any(row[1] == column for row in cursor.fetchall())

    if not table_has_column('contacts', 'email'):
        cursor.execute('ALTER TABLE contacts ADD COLUMN email TEXT')

    # ── Residents Table ────────────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS residents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            college TEXT NOT NULL,
            major TEXT NOT NULL,
            image_url TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ── Gallery Images Table ───────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gallery_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'private_suite',
            filename TEXT NOT NULL,
            url TEXT NOT NULL,
            availability TEXT DEFAULT 'Available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ── Admin Users Table ──────────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    if not table_has_column('residents', 'created_at'):
        cursor.execute("ALTER TABLE residents RENAME TO residents_old")
        cursor.execute('''
            CREATE TABLE residents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                college TEXT NOT NULL,
                major TEXT NOT NULL,
                image_url TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            INSERT INTO residents (id, name, college, major, image_url, category, created_at)
            SELECT id, name, college, major, image_url, 'general', CURRENT_TIMESTAMP
            FROM residents_old
        ''')
        cursor.execute('DROP TABLE residents_old')

    # ── Seed Residents ─────────────────────────────────────────────────────────
    cursor.execute("SELECT COUNT(*) FROM residents")
    if cursor.fetchone()[0] == 0:
        placeholder_residents = [
            ('Arjun Mehta',   "St. Xavier's College",        'Medical Sciences',     '/static/img/avatar.png', 'medical'),
            ('Sanya Iyer',    'National Design Academy',      'Visual Communication', '/static/img/avatar.png', 'arts'),
            ('Rohan Kapoor',  'Indian Institute of Tech',     'Computer Science',     '/static/img/avatar.png', 'engineering'),
            ('Ananya Reddy',  'Lady Shriram College',         'Psychology',           '/static/img/avatar.png', 'arts'),
            ('Vikram Singh',  'Delhi School of Economics',    'Finance',              '/static/img/avatar.png', 'general'),
            ('Meera Joshi',   'Amity University',             'Law',                  '/static/img/avatar.png', 'general'),
            ('Zayed Khan',    'Loyola College',               'Architecture',         '/static/img/avatar.png', 'engineering'),
            ('Priya Nair',    'Mount Carmel College',         'Journalism',           '/static/img/avatar.png', 'arts'),
        ]
        cursor.executemany(
            'INSERT INTO residents (name, college, major, image_url, category) VALUES (?, ?, ?, ?, ?)',
            placeholder_residents
        )
        print("Seeded residents table.")

    # ── Seed Default Admin ─────────────────────────────────────────────────────
    cursor.execute("SELECT COUNT(*) FROM admin_users")
    if cursor.fetchone()[0] == 0:
        pwd_hash = hashlib.sha256('aunties2026'.encode()).hexdigest()
        cursor.execute(
            'INSERT INTO admin_users (username, password_hash) VALUES (?, ?)',
            ('admin', pwd_hash)
        )
        print("Default admin created — username: admin | password: aunties2026")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
