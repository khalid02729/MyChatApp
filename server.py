import os
import sqlite3
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__, template_folder='.', static_folder='.')
app.config['SECRET_KEY'] = 'whatsapp_secret_key_98765'

socketio = SocketIO(app, cors_allowed_origins="*")
DB_FILE = 'whatsapp_app.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT NOT NULL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS messages (id TEXT PRIMARY KEY, sender_username TEXT, receiver_username TEXT, message TEXT, time TEXT, deleted_for TEXT DEFAULT "")')
    cursor.execute('CREATE TABLE IF NOT EXISTS stories (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, content TEXT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def send_static(path):
    return send_from_directory('.', path)

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'برجاء ملء جميع الحقول!'})
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'تم تسجيل الحساب بنجاح!'})
    except sqlite3.IntegrityError:
        return jsonify({'status': 'error', 'message': 'اسم المستخدم مأخوذ بالفعل!'})
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE username = ? AND password = ?', (username, password))
    user_row = cursor.fetchone()
    conn.close()
    if user_row:
        # التعديل السحري: أخذنا user_row[0] عشان نخلص من القوسين والفاصلة خالص والاسم يرجع صافي
        return jsonify({'status': 'success', 'user': {'username': user_row[0]}})
    return jsonify({'status': 'error', 'message': 'اسم المستخدم أو كلمة المرور غير صحيحة!'})

@app.route('/api/search', methods=['GET'])
def api_search():
    username = request.args.get('username', '').strip()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
    user_row = cursor.fetchone()
    conn.close()
    if user_row:
        return jsonify({'status': 'success', 'user': {'username': user_row[0]}})
    return jsonify({'status': 'error', 'message': 'المستخدم غير موجود!'})

@app.route('/api/active-chats', methods=['GET'])
def api_active_chats():
    username = request.args.get('username', '')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT CASE WHEN sender_username = ? THEN receiver_username ELSE sender_username END as chat_partner FROM messages WHERE sender_username = ? OR receiver_username = ?', (username, username, username))
    partners = cursor.fetchall()
    chats_list = []
    for p in partners:
        partner_name = p[0]
        cursor.execute('SELECT message FROM messages WHERE (sender_username = ? AND receiver_username = ?) OR (sender_username = ? AND receiver_username = ?) ORDER BY rowid DESC LIMIT 1', (username, partner_name, partner_name, username))
        last_msg_row = cursor.fetchone()
        last_msg = last_msg_row[0] if last_msg_row else ""
        chats_list.append({'username': partner_name, 'last_message': last_msg})
    conn.close()
    return jsonify(chats_list)

@app.route('/api/messages', methods=['GET'])
def api_get_messages():
    sender = request.args.get('sender', '')
    receiver = request.args.get('receiver', '')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT id, sender_username, receiver_username, message, time, deleted_for FROM messages WHERE (sender_username = ? AND receiver_username = ?) OR (sender_username = ? AND receiver_username = ?) ORDER BY rowid ASC', (sender, receiver, receiver, sender))
    rows = cursor.fetchall()
    conn.close()
    messages_list = []
    for row in rows:
        messages_list.append({
            'id': row[0],
            'sender_username': row[1],
            'receiver_username': row[2],
            'message': row[3],
            'time': row[4],
            'deleted_for': row[5].split(',') if row[5] else []
        })
    return jsonify(messages_list)

@app.route('/api/send', methods=['POST'])
def api_send_message():
    data = request.json
    msg_id = data.get('id')
    sender = data.get('sender_username')
    receiver = data.get('receiver_username')
    message = data.get('message')
    time = data.get('time')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (id, sender_username, receiver_username, message, time) VALUES (?, ?, ?, ?, ?)', (msg_id, sender, receiver, message, time))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/delete-message', methods=['POST'])
def api_delete_message():
    data = request.json
    msg_id = data.get('msg_id')
    delete_type = data.get('type')
    user = data.get('user')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if delete_type == 'me':
        cursor.execute('SELECT deleted_for FROM messages WHERE id = ?', (msg_id,))
        row = cursor.fetchone()
        if row:
            current_deleted = row[0]
            new_deleted = f"{current_deleted},{user}" if current_deleted else user
            cursor.execute('UPDATE messages SET deleted_for = ? WHERE id = ?', (new_deleted, msg_id))
    elif delete_type == 'everyone':
        cursor.execute('UPDATE messages SET message = "🚫 تم حذف هذه الرسالة" WHERE id = ?', (msg_id,))
        cursor.execute('SELECT sender_username, receiver_username FROM messages WHERE id = ?', (msg_id,))
        row = cursor.fetchone()
        if row:
            s_user = row[0]
            r_user = row[1]
            socketio.emit('message_deleted_for_everyone', {'sender': s_user, 'receiver': r_user}, room=s_user)
            socketio.emit('message_deleted_for_everyone', {'sender': s_user, 'receiver': r_user}, room=r_user)
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/add-story', methods=['POST'])
def api_add_story():
    data = request.json
    username = data.get('username')
    content = data.get('content')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO stories (username, content) VALUES (?, ?)', (username, content))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/stories', methods=['GET'])
def api_get_stories():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT username, content FROM stories ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    stories_list = [{'username': r[0], 'content': r[1]} for r in rows]
    return jsonify(stories_list)

@socketio.on('join')
def on_join(data):
    username = data.get('username')
    if username:
        join_room(username)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
