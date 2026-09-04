import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = 'thanaweya_2027_secret_key'

# فتح الحماية بأعلى صلاحيات مطلقة لمنع رسائل خطأ الاتصال للأبد
CORS(app, supports_credentials=True, origins="*")

DATABASE = 'thanaweya_books.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# تأسيس جداول المواد والكتب على نظافة
def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                track TEXT NOT NULL -- common / elmi_oloom / elmi_riada / adabi
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                pdf_url TEXT NOT NULL,
                book_type TEXT DEFAULT 'شرح', -- شرح / أسئلة / امتحانات
                FOREIGN KEY (subject_id) REFERENCES subjects (id)
            )
        ''')
        conn.commit()
        
        # وضع بيانات تجريبية فورية للمواد والكتب عشان نختبر بيها العظمة
        check = conn.execute('SELECT COUNT(*) FROM subjects').fetchone()
        if check[0] == 0:
            # 1. مواد مشتركة
            cursor = conn.execute("INSERT INTO subjects (name, track) VALUES ('اللغة العربية', 'common')")
            arabic_id = cursor.lastrowid
            conn.execute("INSERT INTO books (subject_id, title, pdf_url, book_type) VALUES (?, 'كتاب الامتحان - شرح وعربي', 'https://w3.org', 'شرح')", (arabic_id,))
            conn.execute("INSERT INTO books (subject_id, title, pdf_url, book_type) VALUES (?, 'كتاب الأضواء - أسئلة وتدريبات', 'https://w3.org', 'أسئلة')", (arabic_id,))
            
            # 2. علمي علوم
            cursor = conn.execute("INSERT INTO subjects (name, track) VALUES ('الفيزياء', 'elmi_oloom')")
            physics_id = cursor.lastrowid
            conn.execute("INSERT INTO books (subject_id, title, pdf_url, book_type) VALUES (?, 'كتاب الامتحان فيزياء - شرح', 'https://w3.org', 'شرح')", (physics_id,))
            conn.execute("INSERT INTO books (subject_id, title, pdf_url, book_type) VALUES (?, 'كتاب نيوتن - أسئلة وعقد', 'https://w3.org', 'أسئلة')", (physics_id,))
            
            # 3. علمي رياضة
            cursor = conn.execute("INSERT INTO subjects (name, track) VALUES ('الرياضيات البحتة', 'elmi_riada')")
            math_id = cursor.lastrowid
            conn.execute("INSERT INTO books (subject_id, title, pdf_url, book_type) VALUES (?, 'كتاب المعاصر - الشرح والخطوات', 'https://w3.org', 'شرح')", (math_id,))
            
            # 4. أدبي
            cursor = conn.execute("INSERT INTO subjects (name, track) VALUES ('التاريخ', 'adabi')")
            history_id = cursor.lastrowid
            conn.execute("INSERT INTO books (subject_id, title, pdf_url, book_type) VALUES (?, 'كتاب الوجيز تاريخ - شرح كامل', 'https://w3.org', 'شرح')", (history_id,))
            
            conn.commit()

init_db()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# API لجلب المواد بناءً على الشعبة المختارة
@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    track = request.args.get('track', 'common')
    with get_db() as conn:
        subjects = conn.execute('SELECT * FROM subjects WHERE track = ? OR track = "common"', (track,)).fetchall()
    return jsonify([dict(sub) for sub in subjects])

# API لجلب الكتب الخاصة بمادة معينة
@app.route('/api/books', methods=['GET'])
def get_books():
    subject_id = request.args.get('subject_id')
    with get_db() as conn:
        books = conn.execute('SELECT * FROM books WHERE subject_id = ?', (subject_id,)).fetchall()
    return jsonify([dict(bk) for bk in books])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
