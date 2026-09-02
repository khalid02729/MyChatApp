import os
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
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
        # 1. جدول المستخدمين (الاسم، الرقم، الباسورد مشفر)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # 2. جدول الرسائل لحفظ تاريخ الدردشة
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

# تشغيل تهيئة قاعدة البيانات عند بدء السيرفر
init_db()

# ================= 1. مسارات الـ API (التسجيل، الدخول، والبحث) =================

# تسجيل حساب جديد
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    phone = data.get('phone')
    password = data.get('password')

    if not username or not phone or not password:
        return jsonify({'status': 'error', 'message': 'برجاء ملء جميع الحقول'}), 400

    # تشفير كلمة المرور لحمايتها في قاعدة البيانات
    hashed_password = generate_password_hash(password)

    try:
        with get_db() as conn:
            conn.execute('INSERT INTO users (username, phone, password) VALUES (?, ?, ?)',
                         (username, phone, hashed_password))
            conn.commit()
        return jsonify({'status': 'success', 'message': 'تم تسجيل الحساب بنجاح'})
    except sqlite3.IntegrityError:
        return jsonify({'status': 'error', 'message': 'هذا الرقم مسجل بالفعل قبل كده!'}), 400

# تسجيل الدخول للبرنامج
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    phone = data.get('phone')
    password = data.get('password')

    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE phone = ?', (phone,)).fetchone()

    # التحقق من وجود المستخدم وصحة الباسورد المشفر
    if user and check_password_hash(user['password'], password):
        return jsonify({
            'status': 'success',
            'user': {'username': user['username'], 'phone': user['phone']}
        })
    
    return jsonify({'status': 'error', 'message': 'رقم الهاتف أو كلمة المرور غير صحيحة'}), 401

# البحث عن شخص داخل البرنامج بواسطة رقم الهاتف
@app.route('/api/search', methods=['GET'])
def search_user():
    phone = request.args.get('phone')
    with get_db() as conn:
        user = conn.execute('SELECT username, phone FROM users WHERE phone = ?', (phone,)).fetchone()
    
    if user:
        return jsonify({'status': 'success', 'user': {'username': user['username'], 'phone': user['phone']}})
    return jsonify({'status': 'error', 'message': 'المستخدم غير موجود.. تأكد من الرقم'}), 404

# جلب الرسائل القديمة بين مستخدمين (تاريخ المحادثة)
@app.route('/api/messages', methods=['GET'])
def get_messages():
    sender = request.args.get('sender')
    receiver = request.args.get('receiver')
    
    with get_db() as conn:
        messages = conn.execute('''
            SELECT sender_phone, receiver_phone, message, timestamp FROM messages 
            WHERE (sender_phone = ? AND receiver_phone = ?) 
               OR (sender_phone = ? AND receiver_phone = ?)
            ORDER BY timestamp ASC
        ''', (sender, receiver, receiver, sender)).fetchall()
        
    return jsonify([dict(msg) for msg in messages])

# ================= 2. اتصالات الـ SocketIO للدردشة الفورية (Real-time) =================

# ربط المستخدم بـ "غرفة" خاصة برقم تليفونه عشان يستقبل رسائله فورياً
@socketio.on('join')
def on_join(data):
    phone = data['phone']
    join_room(phone)
    print(f"[Socket] المستخدم صاحب الرقم {phone} متصل الآن بغرفته الخاصة.")

# استقبال وإرسال الرسائل حياً فور الضغط على إرسال
@socketio.on('send_message')
def handle_message(data):
    sender = data['sender_phone']
    receiver = data['receiver_phone']
    message_text = data['message']

    # حفظ الرسالة في قاعدة البيانات قبل إرسالها
    with get_db() as conn:
        conn.execute('INSERT INTO messages (sender_phone, receiver_phone, message) VALUES (?, ?, ?)',
                     (sender, receiver, message_text))
        conn.commit()

    # إرسال الرسالة فوراً في نفس اللحظة للمستلم والمرسل لتحديث واجهاتهم
    emit('receive_message', data, room=receiver)
    emit('receive_message', data, room=sender)

if __name__ == '__main__':
    # قراءة بورت السيرفر الموفر من Railway تلقائياً، وإلا يعمل على 5000
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)

