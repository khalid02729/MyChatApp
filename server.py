import os
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS  # تم إضافة مكتبة لمنع حظر اتصال المتصفحات بالـ API
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = 'whatsapp_secret_key_123'

# تفعيل الـ CORS لحل مشكلة الاتصال تماماً بين التطبيق والسيرفر
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
                password TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_username TEXT NOT NULL,
                receiver_username TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# ================= مسارات الـ API =================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'برجاء ملء جميع الحقول'}), 400
    hashed_password = generate_password_hash(password)
    try:
        with get_db() as conn:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
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
        return jsonify({'status': 'success', 'user': {'username': user['username']}})
    return jsonify({'status': 'error', 'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'}), 401

@app.route('/api/search', methods=['GET'])
def search_user():
    username = request.args.get('username', '').strip()
    with get_db() as conn:
        user = conn.execute('SELECT username FROM users WHERE username = ?', (username,)).fetchone()
    if user:
        return jsonify({'status': 'success', 'user': {'username': user['username']}})
    return jsonify({'status': 'error', 'message': 'المستخدم غير موجود'}), 404

@app.route('/api/active-chats', methods=['GET'])
def get_active_chats():
    username = request.args.get('username', '').strip()
    with get_db() as conn:
        chats = conn.execute('''
            SELECT DISTINCT CASE WHEN sender_username = ? THEN receiver_username ELSE sender_username END as chat_user
            FROM messages WHERE sender_username = ? OR receiver_username = ?
        ''', (username, username, username)).fetchall()
        result = []
        for row in chats:
            chat_user = row['chat_user']
            last_msg = conn.execute('''
                SELECT message FROM messages 
                WHERE (sender_username = ? AND receiver_username = ?) OR (sender_username = ? AND receiver_username = ?)
                ORDER BY id DESC LIMIT 1
            ''', (username, chat_user, chat_user, username)).fetchone()
            result.append({
                'username': chat_user,
                'last_message': last_msg['message'] if last_msg else "اضغط لبدء الدردشة..."
            })
    return jsonify(result)

@app.route('/api/messages', methods=['GET'])
def get_messages():
    sender = request.args.get('sender')
    receiver = request.args.get('receiver')
    with get_db() as conn:
        messages = conn.execute('''
            SELECT sender_username, receiver_username, message, timestamp FROM messages 
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
        conn.execute('INSERT INTO messages (sender_username, receiver_username, message) VALUES (?, ?, ?)', (sender, receiver, message_text))
        conn.commit()
    try:
        socketio.emit('receive_message', data, room=receiver)
        socketio.emit('receive_message', data, room=sender)
    except:
        pass
    return jsonify({'status': 'success'})

@socketio.on('join')
def on_join(data):
    username = data['username']
    join_room(username)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
