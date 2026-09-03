import os
import sqlite3
from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room

# تأكد أن ملفات index.html و style.css و app.js موجودة في نفس الفولدر أو فولدر اسمه templates
app = Flask(__name__, template_folder='.', static_folder='.')
app.config['SECRET_KEY'] = 'whatsapp_secret_key_98765'

socketio = SocketIO(app, cors_allowed_origins="*")
DB_FILE = 'whatsapp_app.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT NOT NULL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS messages (msg_id TEXT PRIMARY KEY, sender TEXT, receiver TEXT, message TEXT, time TEXT, deleted_by_sender INTEGER DEFAULT 0, deleted_by_receiver INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS stories (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, content TEXT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    conn.commit()
    conn.close()

init_db()

# 🌐 الدالة السحرية اللي هتخلي الرابط يفتح الـ HTML علطول لما تدخل عليه
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def send_static(path):
    return send_from_directory('.', path)

@socketio.on('login_request')
def handle_login(data):
    username = data.get('username', '').strip()
    password = data.get('password', '')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0] == password:
        join_room(username)
        emit('login_success', {'username': username})
    else:
        emit('login_error', '❌ اسم المستخدم أو كلمة المرور غير صحيحة!')

@socketio.on('register_request')
def handle_register(data):
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        emit('register_error', '❌ الرجاء إدخل بيانات صحيحة')
        return
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        emit('register_success')
    except sqlite3.IntegrityError:
        emit('register_error', '❌ اسم المستخدم هذا مأخوذ بالفعل!')
    finally:
        conn.close()

@socketio.on('new_private_message')
def handle_new_message(data):
    msg_id = data.get('id')
    sender = data.get('sender')
    receiver = data.get('receiver')
    message = data.get('message')
    time = data.get('time')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (msg_id, sender, receiver, message, time) VALUES (?, ?, ?, ?, ?)', (msg_id, sender, receiver, message, time))
    conn.commit()
    conn.close()
    emit('receive_private_message', data, room=receiver)

@socketio.on('load_chat_history')
def handle_load_history(data):
    user = data.get('user')
    partner = data.get('partner')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT msg_id, sender, receiver, message, time FROM messages WHERE ((sender = ? AND receiver = ? AND deleted_by_sender = 0) OR (sender = ? AND receiver = ? AND deleted_by_receiver = 0)) ORDER BY rowid ASC', (user, partner, partner, user))
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        emit('receive_private_message', {'id': row[0], 'sender': row[1], 'receiver': row[2], 'message': row[3], 'time': row[4]})

@socketio.on('delete_message_for_me')
def handle_delete_for_me(data):
    msg_id = data.get('msg_id')
    user = data.get('user')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE messages SET deleted_by_sender = 1 WHERE msg_id = ? AND sender = ?', (msg_id, user))
    cursor.execute('UPDATE messages SET deleted_by_receiver = 1 WHERE msg_id = ? AND receiver = ?', (msg_id, user))
    conn.commit()
    conn.close()

@socketio.on('delete_message_for_everyone')
def handle_delete_for_everyone(data):
    msg_id = data.get('msg_id')
    sender = data.get('sender')
    receiver = data.get('receiver')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE messages SET message = "🚫 تم حذف هذه الرسالة" WHERE msg_id = ? AND sender = ?', (msg_id, sender))
    conn.commit()
    conn.close()
    emit('message_deleted_for_everyone', {'msg_id': msg_id}, room=sender)
    emit('message_deleted_for_everyone', {'msg_id': msg_id}, room=receiver)

@socketio.on('post_new_story')
def handle_new_story(data):
    username = data.get('username')
    content = data.get('content')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO stories (username, content) VALUES (?, ?)', (username, content))
    conn.commit()
    conn.close()
    handle_get_chats_and_stories({'username': username})

@socketio.on('get_chats_and_stories')
def handle_get_chats_and_stories(data):
    username = data.get('username')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT CASE WHEN sender = ? THEN receiver ELSE sender END as chat_partner FROM messages WHERE sender = ? OR receiver = ?', (username, username, username))
    partners = cursor.fetchall()
    chats_list = []
    for p in partners:
        partner_name = p[0]
        cursor.execute('SELECT message FROM messages WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?) ORDER BY rowid DESC LIMIT 1', (username, partner_name, partner_name, username))
        last_msg_row = cursor.fetchone()
        last_msg = last_msg_row[0] if last_msg_row else ""
        chats_list.append({'name': partner_name, 'lastMessage': last_msg})
    conn.close()
    emit('update_chats_and_stories_view', {'chats': chats_list}, room=username)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)

