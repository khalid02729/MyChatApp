
import http.server
import json
import urllib.parse
import sqlite3
import os

DB = "chat.db"

def init_db():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT UNIQUE,
            password TEXT,
            email TEXT
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            name TEXT,
            text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

class ChatHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/login":
            cl = int(self.headers['Content-Length'])
            params = urllib.parse.parse_qs(self.rfile.read(cl).decode('utf-8'))
            name = params.get('name', [''])[0].strip()
            phone = params.get('phone', [''])[0].strip()
            password = params.get('password', [''])[0].strip()
            email = params.get('email', [''])[0].strip() or f"{phone}@khalidchat.com"
            
            if not phone or not password:
                self.send_response(400); self.end_headers(); return
                
            conn = sqlite3.connect(DB)
            user = conn.cursor().execute("SELECT name, password, email FROM users WHERE phone = ?", (phone,)).fetchone()
            
            if user:
                if user[1] == password:
                    self.send_response(200)
                    r_msg = f"Login successful:{user[0]}:{user[2]}"
                else:
                    self.send_response(401)
                    r_msg = "كلمة السر خاطئة! هذا الرقم محمي."
            else:
                if name:
                    try:
                        conn.cursor().execute("INSERT INTO users (name, phone, password, email) VALUES (?, ?, ?, ?)", (name, phone, password, email))
                        conn.commit()
                        self.send_response(200)
                        r_msg = f"Registration successful:{name}:{email}"
                    except:
                        self.send_response(400); r_msg = "خطأ في التسجيل"
                else:
                    self.send_response(400); r_msg = "هذا الرقم جديد، يرجى كتابة الاسم والبريد لإنشاء حسابك لأول مرة."
            
            conn.close()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(r_msg.encode('utf-8'))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(parsed.query)
        
        if parsed.path in ["/", "/index.html"]:
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8')); return
            
        conn = sqlite3.connect(DB)
        
        if parsed.path == "/search":
            p = q.get('phone', [''])[0].strip()
            u = conn.cursor().execute("SELECT name, email FROM users WHERE phone = ?", (p,)).fetchone()
            res = f"Found:{u[0]}:{u[1]}" if u else "User not found"
            self.send_response(200); self.send_header("Content-Type", "text/plain; charset=utf-8"); self.end_headers()
            self.wfile.write(res.encode('utf-8'))
            
        elif parsed.path == "/send":
            s, rec, m = q.get('sender', [''])[0].strip(), q.get('receiver', [''])[0].strip(), q.get('message', [''])[0].strip()
            if s and rec and m:
                conn.cursor().execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)", (s, rec, m))
                conn.commit()
            self.send_response(200); self.end_headers()
            
        elif parsed.path == "/get_messages":
            s, rec = q.get('sender', [''])[0].strip(), q.get('receiver', [''])[0].strip()
            rows = conn.cursor().execute("SELECT id, sender, message FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY timestamp ASC", (s, rec, rec, s)).fetchall()
            msgs = [{"id": r[0], "sender": r[1], "message": r[2]} for r in rows]
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(msgs).encode('utf-8'))
            
        elif parsed.path == "/delete_msg":
            mid = q.get('id', [''])[0].strip()
            if mid:
                conn.cursor().execute("DELETE FROM messages WHERE id = ?", (mid,))
                conn.commit()
            self.send_response(200); self.end_headers()
            
        elif parsed.path == "/send_status":
            p, n, t = q.get('phone', [''])[0].strip(), q.get('name', [''])[0].strip(), q.get('text', [''])[0].strip()
            if p and t:
                conn.cursor().execute("INSERT INTO status (phone, name, text) VALUES (?, ?, ?)", (p, n, t))
                conn.commit()
            self.send_response(200); self.end_headers()
            
        elif parsed.path == "/get_statuses":
            rows = conn.cursor().execute("SELECT name, text, phone FROM status ORDER BY timestamp DESC LIMIT 10").fetchall()
            st = [{"name": r[0], "text": r[1], "phone": r[2]} for r in rows]
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(st).encode('utf-8'))
            
        conn.close()

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp Pro | Khalid Edition</title>
    <link rel="stylesheet" href="https://cloudflare.com">
    <style>
        @import url('https://googleapis.com');
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', 'Tajawal', sans-serif; }
        body { background-color: #111b21; color: #e9edef; height: 100vh; display: flex; justify-content: center; align-items: center; }
        .app-container { width: 100%; max-width: 480px; height: 100vh; background-color: #222e35; display: flex; flex-direction: column; position: relative; }
        
        .auth-box { margin: auto; width: 85%; text-align: center; background: #111b21; padding: 30px 20px; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
        .auth-logo { font-size: 60px; color: #00a884; margin-bottom: 15px; }
        .auth-box h2 { font-size: 22px; margin-bottom: 8px; }
        .auth-box p { font-size: 13px; color: #8696a0; margin-bottom: 25px; }
        .input-g { margin-bottom: 15px; }
        .input-g input { width: 100%; padding: 12px; background: #2a3942; border: 1px solid #3b4a54; border-radius: 8px; color: white; font-size: 14px; outline: none; text-align: right; }
        .input-g input:focus { border-color: #00a884; }
        .btn { background: #00a884; color: #111b21; border: none; padding: 12px; width: 100%; border-radius: 8px; font-size: 15px; font-weight: 700; cursor: pointer; }
        .link { color: #53bdeb; font-size: 13px; cursor: pointer; display: inline-block; margin-top: 15px; }
        .hidden { display: none !important; }

        .wp-header { background: #202c33; padding: 12px 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #2a3942; }
        .header-center { display: flex; align-items: center; gap: 10px; cursor: pointer; }
        .pfp { width: 40px; height: 40px; background: #00a884; color: #111b21; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: 700; font-size: 18px; }
        .search-area { padding: 8px 12px; background: #111b21; display: flex; gap: 8px; }
        .search-area input { flex: 1; background: #202c33; border: none; border-radius: 8px; padding: 8px 15px; color: white; font-size: 14px; outline: none; }
        .search-area button { background: #00a884; border: none; padding: 0 15px; border-radius: 8px; font-weight: 700; cursor: pointer; }
        
        /* بار الحالات */
        .status-bar { padding: 10px; background: #1f2c34; display: flex; gap: 12px; overflow-x: auto; border-bottom: 1px solid #2a3942; align-items: center; }
        .status-item { display: flex; flex-direction: column; align-items: center; font-size: 11px; color: #8696a0; cursor: pointer; min-width: 55px; }
        .status-circle { width: 42px; height: 42px; border: 2px dashed #00a884; border-radius: 50%; display: flex; justify-content: center; align-items: center; color: white; font-weight: 700; margin-bottom: 4px; }
        .add-status-btn { background: #2a3942; border: none; width: 35px; height: 35px; border-radius: 50%; color: #00a884; cursor: pointer; font-size: 16px; }

        .chat-view { flex: 1; padding: 20px; overflow-y: auto; background-color: #0b141a; background-image: url('https://githubusercontent.com'); background-blend-mode: overlay; display: flex; flex-direction: column; gap: 8px; align-items: center; }
        .msg { max-width: 85%; padding: 8px 12px; border-radius: 8px; font-size: 14.5px; line-height: 1.4; word-break: break-word; user-select: none; cursor: pointer; }

