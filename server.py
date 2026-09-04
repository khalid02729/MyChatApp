import os
import sqlite3
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='', static_url_path='')
app.config['SECRET_KEY'] = 'whatsapp_secret_key_123'
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
                id TEXT PRIMARY KEY,
                sender_username TEXT NOT NULL,
                receiver_username TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_for TEXT DEFAULT ""
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
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'برجاء ملء جميع الحقول!'}), 400
        
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
    return jsonify({'status': 'error', 'message': 'المستخدم غير موجود!'}), 404

@app.route('/api/active-chats', methods=['GET'])
def get_active_chats():
    username = request.args.get('username', '').strip()
    with get_db() as conn:
        chats = conn.execute('''
            SELECT DISTINCT CASE 
                WHEN sender_username = ? THEN receiver_username 
                ELSE sender_username 
            END as chat_user 
            FROM messages 
            WHERE sender_username = ? OR receiver_username = ?
        ''', (username, username, username)).fetchall()
        
        result = []
        for row in chats:
            chat_user = row['chat_user']
            last_msg = conn.execute('''
                SELECT message FROM messages 
                WHERE (sender_username = ? AND receiver_username = ?) 
                   OR (sender_username = ? AND receiver_username = ?) 
                ORDER BY timestamp DESC LIMIT 1
            ''', (username, chat_user, chat_user, username)).fetchone()
            
            result.append({
                'username': chat_user,
                'last_message': last_msg['message'] if last_msg else "...اضغط لبدء الدردشة"
            })
            
    return jsonify(result)

@app.route('/api/messages', methods=['GET'])
def get_messages():
    sender = request.args.get('sender')
    receiver = request.args.get('receiver')
    with get_db() as conn:
        messages = conn.execute('''
            SELECT id, sender_username, receiver_username, message, timestamp, deleted_for 
            FROM messages 
            WHERE (sender_username = ? AND receiver_username = ?) 
               OR (sender_username = ? AND receiver_username = ?) 
            ORDER BY timestamp ASC
        ''', (sender, receiver, receiver, sender)).fetchall()
        
        return jsonify([dict(msg) for msg in messages])

@app.route('/api/send', methods=['POST'])
def send_message_api():
    data = request.json
    msg_id = data.get('id')
    sender = data.get('sender_username')
    receiver = data.get('receiver_username')
    message_text = data.get('message')
    
    with get_db() as conn:
        # هنا صلحنا المشكلة وشيلنا السطر اللي بيبوظ الإرسال
        conn.execute('''
            INSERT INTO messages (id, sender_username, receiver_username, message) 
            VALUES (?, ?, ?, ?)
        ''', (msg_id, sender, receiver, message_text))
        conn.commit()
        
    try:
        socketio.emit('receive_private_message', data, room=sender)
        socketio.emit('receive_private_message', data, room=receiver)
    except:
        pass
        
    return jsonify({'status': 'success'})

@app.route('/api/delete-message', methods=['POST'])
def delete_message_api():
    data = request.json
    msg_id = data.get('msg_id')
    delete_type = data.get('type')
    user = data.get('user')
    
    with get_db() as conn:
        if delete_type == 'me':
            row = conn.execute('SELECT deleted_for FROM messages WHERE id = ?', (msg_id,)).fetchone()
            current_deleted = row['deleted_for'] if row and row['deleted_for'] else ""
            new_deleted = f"{current_deleted},{user}" if current_deleted else user
            conn.execute('UPDATE messages SET deleted_for = ? WHERE id = ?', (new_deleted, msg_id))
        elif delete_type == 'everyone':
            conn.execute('UPDATE messages SET message = "🚫 تم حذف هذه الرسالة" WHERE id = ?', (msg_id,))
            msg_row = conn.execute('SELECT sender_username, receiver_username FROM messages WHERE id = ?', (msg_id,)).fetchone()
            if msg_row:
                socketio.emit('message_deleted_for_everyone', {
                    'msg_id': msg_id, 
                    'sender': msg_row['sender_username'], 
                    'receiver': msg_row['receiver_username']
                }, room=msg_row['sender_username'])
                socketio.emit('message_deleted_for_everyone', {
                    'msg_id': msg_id, 
                    'sender': msg_row['sender_username'], 
                    'receiver': msg_row['receiver_username']
                }, room=msg_row['receiver_username'])
        conn.commit()
        
    return jsonify({'status': 'success'})

@app.route('/api/add-story', methods=['POST'])
def add_story_api():
    data = request.json
    username = data.get('username')
    content = data.get('content')
    
    with get_db() as conn:
        conn.execute('INSERT INTO stories (username, content) VALUES (?, ?)', (username, content))
        conn.commit()
    return jsonify({'status': 'success'})

@app.route('/api/stories', methods=['GET'])
def get_stories_api():
    with get_db() as conn:
        rows = conn.execute('SELECT username, content FROM stories ORDER BY id DESC').fetchall()
        return jsonify([dict(r) for r in rows])

@socketio.on('join')
def on_join(data):
    username = data.get('username')
    if username:
        join_room(username)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
