import os
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = 'whatsapp_super_secret_key'
CORS(app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60)

DATABASE = 'chat_app.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                avatar TEXT,
                bio TEXT DEFAULT 'متاح استخدام واتساب كول'
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_username TEXT NOT NULL,
                receiver_username TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_for_all INTEGER DEFAULT 0
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    avatar = data.get('avatar', '')
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'برجاء ملء جميع الحقول'}), 400
    hashed_password = generate_password_hash(password)
    try:
        with get_db() as conn:
            conn.execute('INSERT INTO users (username, password, avatar) VALUES (?, ?, ?)', (username, hashed_password, avatar))
            conn.commit()
        return jsonify({'status': 'success', 'message': 'تم تسجيل الحساب بنجاح!'})
    except sqlite3.IntegrityError:
        return jsonify({'status': 'error', 'message': 'اسم المستخدم مأخوذ بالفعل!'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if user and check_password_hash(user['password'], password):
        return jsonify({'status': 'success', 'user': {'username': user['username'], 'avatar': user['avatar'], 'bio': user['bio']}})
    return jsonify({'status': 'error', 'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'}), 401

@app.route('/api/user-profile', methods=['GET'])
def user_profile():
    username = request.args.get('username')
    with get_db() as conn:
        user = conn.execute('SELECT username, avatar, bio FROM users WHERE username = ?', (username,)).fetchone()
    if user:
        return jsonify({'status': 'success', 'user': dict(user)})
    return jsonify({'status': 'error'})

@app.route('/api/search', methods=['GET'])
def search_user():
    username = request.args.get('username', '').strip()
    with get_db() as conn:
        user = conn.execute('SELECT username, avatar FROM users WHERE username = ?', (username,)).fetchone()
    if user:
        return jsonify({'status': 'success', 'user': dict(user)})
    return jsonify({'status': 'error', 'message': 'المستخدم غير موجود'}), 404

@app.route('/api/messages', methods=['GET'])
def get_messages():
    sender = request.args.get('sender')
    receiver = request.args.get('receiver')
    with get_db() as conn:
        messages = conn.execute('''
            SELECT id, sender_username, receiver_username, message, timestamp, deleted_for_all FROM messages 
            WHERE (sender_username = ? AND receiver_username = ?) OR (sender_username = ? AND receiver_username = ?)
            ORDER BY timestamp ASC
        ''', (sender, receiver, receiver, sender)).fetchall()
    return jsonify([dict(msg) for msg in messages])

@app.route('/api/send', methods=['POST'])
def send_message_api():
    data = request.json
    sender = data.get('sender_username')
    receiver = data.get('receiver_username')
    message_text = data.get('message')
    with get_db() as conn:
        cursor = conn.execute('INSERT INTO messages (sender_username, receiver_username, message) VALUES (?, ?, ?)', (sender, receiver, message_text))
        msg_id = cursor.lastrowid
        conn.commit()
    data['id'] = msg_id
    try:
        socketio.emit('receive_message', data, room=receiver)
        socketio.emit('receive_message', data, room=sender)
    except:
        pass
    return jsonify({'status': 'success'})

@app.route('/api/delete-message', methods=['POST'])
def delete_message():
    data = request.json
    msg_id = data.get('id')
    receiver = data.get('receiver_username')
    sender = data.get('sender_username')
    with get_db() as conn:
        conn.execute('UPDATE messages SET message = "🚫 تم حذف هذه الرسالة", deleted_for_all = 1 WHERE id = ?', (msg_id,))
        conn.commit()
    socketio.emit('message_deleted', {'id': msg_id}, room=receiver)
    socketio.emit('message_deleted', {'id': msg_id}, room=sender)
    return jsonify({'status': 'success'})

@app.route('/api/stories', methods=['GET', 'POST'])
def handle_stories():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        content = data.get('content')
        with get_db() as conn:
            conn.execute('INSERT INTO stories (username, content) VALUES (?, ?)', (username, content))
            conn.commit()
        return jsonify({'status': 'success'})
    else:
        with get_db() as conn:
            stories = conn.execute('''
                SELECT s.*, u.avatar FROM stories s 
                JOIN users u ON s.username = u.username
                WHERE s.timestamp >= datetime('now', '-1 day')
                ORDER BY s.id DESC
            ''').fetchall()
        return jsonify([dict(st) for st in stories])

@socketio.on('join')
def on_join(data):
    join_room(data['username'])

@socketio.on('typing')
def on_typing(data):
    emit('display_typing', data, room=data['receiver'])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)

