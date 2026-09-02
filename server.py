
import os
import sqlite3
import json
import logging
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

# إعداد السجلات لمتابعة الأخطاء في لوحة التحكم
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DB = "chat.db"

# دالة للتأكد من إنشاء جداول قاعدة البيانات عند بدء التشغيل لمنع أي خطأ
def init_db():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            phone TEXT PRIMARY KEY,
            name TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def search_user(phone):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM users WHERE phone = ?", (phone,))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

def save_message(sender, receiver, msg_text):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)", (sender, receiver, msg_text))
    conn.commit()
    conn.close()

def get_messages(user1, user2):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sender, message FROM messages 
        WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
        ORDER BY timestamp ASC
    """, (user1, user2, user2, user1))
    rows = cursor.fetchall()
    messages = [{"sender": row[0], "message": row[1]} for row in rows]
    conn.close()
    return messages

class ChatHandler(SimpleHTTPRequestHandler):
    
    # دالة مساعدة لإرسال الهيدرز شاملة الـ CORS لمنع حظر الاتصال
    def _send_cors_headers(self, status_code=200, content_type="text/plain"):
        self.send_response(status_code)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # معالجة طلبات الأمان المسبقة من المتصفحات (CORS Options)
    def do_OPTIONS(self):
        self._send_cors_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        
        # مسار إضافي للتأكد من عمل السيرفر من المتصفح مباشرة
        if parsed.path == "/" or parsed.path == "/api/status":
            self._send_cors_headers(200, "application/json")
            self.wfile.write(json.dumps({"status": "running"}).encode("utf-8"))
            return

        if parsed.path == "/search":
            params = parse_qs(parsed.query)
            phone = params.get("phone", [""])[0].strip()
            user_name = search_user(phone)
            
            response = f"Found: {user_name}" if user_name else "User not found"
            self._send_cors_headers(200, "text/plain")
            self.wfile.write(response.encode("utf-8"))
            return
            
        if parsed.path == "/send":
            params = parse_qs(parsed.query)
            sender = params.get("sender", [""])[0].strip()
            receiver = params.get("receiver", [""])[0].strip()
            msg_text = params.get("message", [""])[0].strip()
            
            if sender and receiver and msg_text:
                save_message(sender, receiver, msg_text)
                response = "Message sent and saved!"
            else:
                response = "Missing data"
                
            self._send_cors_headers(200, "text/plain")
            self.wfile.write(response.encode("utf-8"))
            return

        if parsed.path == "/get_messages":
            params = parse_qs(parsed.query)
            sender = params.get("sender", [""])[0].strip()
            receiver = params.get("receiver", [""])[0].strip()
            
            messages = get_messages(sender, receiver)
            response = json.dumps(messages)
            
            self._send_cors_headers(200, "application/json")
            self.wfile.write(response.encode("utf-8"))
            return

        return super().do_GET()

# كود التشغيل الرئيسي تم إخراجه خارج الكلاس ليعمل بشكل سليم تماماً
if __name__ == "__main__":
    init_db()
    # قراءة المنفذ ديناميكياً من ريلواي وإلا سيستخدم 8082 كافتراضي
    port = int(os.environ.get('PORT', 8082))
    
    # الاستماع لعنوان فارغ لجعل السيرفر يستقبل اتصالات الـ Proxy الخارجية في ريلواي
    server = ThreadingHTTPServer(('', port), ChatHandler)
    logging.info(f"🚀 Server successfully running on port {port}...")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("🛑 Server shutting down.")
        server.server_close()
