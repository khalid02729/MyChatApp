import os
import random
import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = 'whatsapp_secret_key_123'
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60)

DATABASE = 'chat_app.db'

# 🔑 إعدادات إرسال البريد الإلكتروني (Gmail SMTP)
EMAIL_ADDRESS = "your_gmail@gmail.com" 
EMAIL_PASSWORD = "your_app_password_here" 

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
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                is_active INTEGER DEFAULT 0,
                otp_code TEXT
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

def send_otp_email(user_email, otp_code):
    try:
        msg = MIMEText(f"مرحباً بك في واتساب كول.\n\nكود تفعيل حسابك هو: {otp_code}\nبرجاء كتابته في التطبيق لتفعيل الحساب.")
        msg['Subject'] = 'كود تفعيل حساب واتساب كول 🟢'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = user_email
        with smtplib.SMTP_SSL('://gmail.com', 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, user_email, msg.as_string())
        return True
    except:
        return False

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# ================= مسارات الـ API =================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    if not username or not email or not password:
        return jsonify({'status': 'error', 'message': 'برجاء ملء جميع الحقول'}), 400
    hashed_password = generate_password_hash(password)
    otp_code = str(random.randint(1000, 9999))
    try:
        with get_db() as conn:
            conn.execute('INSERT INTO users (username, email, password, otp_code, is_active) VALUES (?, ?, ?, ?, 0)', 
                         (username, email, hashed_password, otp_code))
            conn.commit()
        send_otp_email(email, otp_code)
        return jsonify({'status': 'success', 'message': 'تم تسجيل الحساب! أرسلنا كود التفعيل إلى بريدك الإلكتروني.'})
    except sqlite3.IntegrityError:
        return jsonify({'status': 'error', 'message': 'اسم المستخدم مأخوذ بالفعل!'}), 400

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    username = data.get('username', '').strip()
    otp_input = data.get('otp', '').strip()
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if user and user['otp_code'] == otp_input:
        with get_db() as conn:
            conn.execute('UPDATE users SET is_active = 1, otp_code = NULL WHERE username = ?', (username,))
            conn.commit()
        return jsonify({'status': 'success', 'message': 'تم تفعيل الحساب بنجاح! يمكنك الآن الدخول.'})
    return jsonify({'status': 'error', 'message': 'كود التفعيل غير صحيح!'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if user and check_password_hash(user['password'], password):
        if user['is_active'] == 0:
            return jsonify({'status': 'unverified', 'message': 'الحساب غير مفعل! برجاء كتابة كود التفعيل المرسل لإيميلك.'}), 401
        return jsonify({'status': 'success', 'user': {'username': user['username']}})
    return jsonify({'status': 'error', 'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'}), 401

@app.route('/api/search', methods=['GET'])
def search_user():
    username = request.args.get('username', '').strip()
    with get_db() as conn:
        user = conn.execute('SELECT username FROM users WHERE username = ? AND is_active = 1', (username,)).fetchone()
    if user:
        return jsonify({'status': 'success', 'user': {'username': user['username']}})
    return jsonify({'status': 'error', 'message': 'المستخدم غير موجود أو غير مفعل'}), 404

# 🔑 دالة سحب قائمة الشاتات النشطة تلقائياً للمستخدم
@app.route('/api/active-chats', methods=['GET'])
def get_active_chats():
    username = request.args.get('username', '').strip()
    with get_db() as conn:
        # البحث عن كل الأسماء الفريدة التي تواصل معها المستخدم
        chats = conn.execute('''
            SELECT DISTINCT CASE WHEN sender_username = ? THEN receiver_username ELSE sender_username END as chat_user
            FROM messages WHERE sender_username = ? OR receiver_username = ?
        ''', (username, username, username)).fetchall()
        
        result = []
        for row in chats:
            chat_user = row['chat_user']
            # جلب آخر رسالة بينهما لعرضها برة في القائمة
            last_msg = conn.execute('''
                SELECT message, timestamp FROM messages 
                WHERE (sender_username = ? AND receiver_username = ?) OR (sender_username = ? AND receiver_username = ?)
                ORDER BY id DESC LIMIT 1
            ''', (username, chat_user, chat_user, username)).fetchone()
            
            result.append({
                'username': chat_user,
                'last_message': last_msg['message'] if last_msg else "اضغط لبدء المحادثة..."
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

@socketio.on('send_message')
def handle_message(data):
    sender = data['sender_username']
    receiver = data['receiver_username']
    message_text = data['message']
    with get_db() as conn:
        conn.execute('INSERT INTO messages (sender_username, receiver_username, message) VALUES (?, ?, ?)', (sender, receiver, message_text))
        conn.commit()
    emit('receive_message', data, room=receiver)
    emit('receive_message', data, room=sender)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
