import sqlite3
import hashlib
from contextlib import contextmanager
from config import Config

class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_admin INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Mock mappings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mock_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    request_method TEXT NOT NULL,
                    request_url TEXT NOT NULL,
                    response_status INTEGER DEFAULT 200,
                    response_body TEXT,
                    response_headers TEXT,
                    priority INTEGER DEFAULT 5,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Create default admin user if not exists
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
            if cursor.fetchone()[0] == 0:
                admin_password = self.hash_password('admin123')
                cursor.execute(
                    'INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)',
                    ('admin', admin_password, 1)
                )
    
    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_user(self, username, password):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM users WHERE username = ? AND is_active = 1',
                (username,)
            )
            user = cursor.fetchone()
            if user and user['password_hash'] == self.hash_password(password):
                return dict(user)
        return None
    
    def get_user_by_id(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def get_all_users(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, is_admin, is_active, created_at FROM users')
            return [dict(row) for row in cursor.fetchall()]
    
    def create_user(self, username, password, is_admin=False):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            password_hash = self.hash_password(password)
            cursor.execute(
                'INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)',
                (username, password_hash, 1 if is_admin else 0)
            )
            return cursor.lastrowid
    
    def update_user(self, user_id, is_admin=None, is_active=None):
        updates = []
        params = []
        if is_admin is not None:
            updates.append('is_admin = ?')
            params.append(1 if is_admin else 0)
        if is_active is not None:
            updates.append('is_active = ?')
            params.append(1 if is_active else 0)
        
        if updates:
            params.append(user_id)
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f'UPDATE users SET {", ".join(updates)} WHERE id = ?',
                    params
                )
                return cursor.rowcount > 0
        return False
    
    def delete_user(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            return cursor.rowcount > 0
    
    def get_user_mappings(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM mock_mappings WHERE user_id = ? ORDER BY created_at DESC',
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_mapping_by_id(self, mapping_id, user_id=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute(
                    'SELECT * FROM mock_mappings WHERE id = ? AND user_id = ?',
                    (mapping_id, user_id)
                )
            else:
                cursor.execute('SELECT * FROM mock_mappings WHERE id = ?', (mapping_id,))
            mapping = cursor.fetchone()
            return dict(mapping) if mapping else None
    
    def create_mapping(self, user_id, name, request_method, request_url, 
                      response_status=200, response_body='', response_headers='{}',
                      priority=5):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO mock_mappings 
                (user_id, name, request_method, request_url, response_status, 
                 response_body, response_headers, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, request_method, request_url, response_status,
                  response_body, response_headers, priority))
            return cursor.lastrowid
    
    def update_mapping(self, mapping_id, user_id, **kwargs):
        allowed_fields = ['name', 'request_method', 'request_url', 'response_status',
                         'response_body', 'response_headers', 'priority', 'is_active']
        updates = []
        params = []
        
        for field in allowed_fields:
            if field in kwargs:
                updates.append(f'{field} = ?')
                params.append(kwargs[field])
        
        if updates:
            updates.append('updated_at = CURRENT_TIMESTAMP')
            params.extend([mapping_id, user_id])
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f'UPDATE mock_mappings SET {", ".join(updates)} WHERE id = ? AND user_id = ?',
                    params
                )
                return cursor.rowcount > 0
        return False
    
    def delete_mapping(self, mapping_id, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM mock_mappings WHERE id = ? AND user_id = ?',
                (mapping_id, user_id)
            )
            return cursor.rowcount > 0
    
    def get_all_active_mappings(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM mock_mappings WHERE is_active = 1 ORDER BY priority DESC'
            )
            return [dict(row) for row in cursor.fetchall()]
