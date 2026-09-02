import os
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# إعداد الفلاسک لقرأة ملف الـ HTML والملفات الجانبية من الفولدر الرئيسي مباشرة
app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = 'whatsapp_secret_key_123'

# إعداد SocketIO للعمل مع السيرفرات السحابية مثل Railway وبدون مشاكل CORS
socketio = SocketIO(app, cors_allowed_origins="*")

DATABASE = 'chat_app.db'

# وظيفة للاتصال بقاعدة بيانات SQLite
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# إنشاء جداول قاعدة البيانات إذا لم تكن موجودة
def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_phone TEXT NOT NULL,
                receiver_phone TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

# مسار لعرض واجهة المستخدم (index.html) تلقائياً عند فتح الرابط
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# ================= مسارات الـ API (التسجيل، الدخول، والبحث) =================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    phone = data.get('phone')
    password = data.get('password')

    if not username or not phone or not password:
        return jsonify({'status': 'error', 'message': 'برجاء ملء جميع الحقول'}), 400

    hashed_password = generate_password_hash(password)

    try:
        with get_db() as conn:
            conn.execute('INSERT INTO users (username, phone, password) VALUES (?, ?, ?)',
                         (username, phone, hashed_password))
            conn.commit()
        return jsonify({'status': 'success', 'message': 'تم تسجيل الحساب بنجاح'})
    except sqlite3.IntegrityError:
        return jsonify({'status': 'error', 'message': 'هذا الرقم مسجل بالفعل قبل كده!'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    phone = data.get('phone')
    password = data.get('password')

    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE phone = ?', (phone,)).fetchone()

    if user and check_password_hash(user['password'], password):
        return jsonify({
            'status': 'success',
            'user': {'username': user['username'], 'phone': user['phone']}
        })
    
    return jsonify({'status': 'error', 'message': 'رقم الهاتف أو كلمة المرور غير صحيحة'}), 401

@app.route('/api/search', methods=['GET'])
def search_user():
    phone = request.args.get('phone')
    with get_db() as conn:
        user = conn.execute('SELECT username, phone FROM users WHERE phone = ?', (phone,)).fetchone()
    
    if user:
        return jsonify({'status': 'success', 'user': {'username': user['username'], 'phone': user['phone']}})
    return jsonify({'status': 'error', 'message': 'المستخدم غير موجود.. تأكد من الرقم'}), 404

# ================= اتصالات الـ SocketIO للدردشة الفورية =================

@socketio.on('join')
def on_join(data):
    phone = data['phone']
    join_room(phone)

@socketio.on('send_message')
def handle_message(data):
    sender = data['sender_phone']
    receiver = data['receiver_phone']
    message_text = data['message']

    with get_db() as conn:
        conn.execute('INSERT INTO messages (sender_phone, receiver_phone, message) VALUES (?, ?, ?)',
                     (sender, receiver, message_text))
        conn.commit()

    emit('receive_message', data, room=receiver)
    emit('receive_message', data, room=sender)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # التشغيل الصحيح المتوافق مع بيئة بيع السيرفرات لـ Railway
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
