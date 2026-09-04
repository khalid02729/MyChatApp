import http.server, json, urllib.parse, sqlite3, os
DB = "chat.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.cursor().execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, password TEXT, email TEXT)")
    conn.cursor().execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, receiver TEXT, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.cursor().execute("CREATE TABLE IF NOT EXISTS status (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT, name TEXT, text TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.commit(); conn.close()
init_db()

def search_user(phone):
    conn = sqlite3.connect(DB)
    u = conn.cursor().execute("SELECT name, email FROM users WHERE phone = ?", (phone,)).fetchone()
    conn.close()
    return u if u else None

class ChatHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/login":
            cl = int(self.headers['Content-Length'])
            params = urllib.parse.parse_qs(self.rfile.read(cl).decode('utf-8'))
            name, phone, password, email = params.get('name', ['']).strip(), params.get('phone', ['']).strip(), params.get('password', ['']).strip(), params.get('email', ['']).strip()
            if not phone or not password: self.send_response(400); self.end_headers(); return
            conn = sqlite3.connect(DB); user = conn.cursor().execute("SELECT name, password, email FROM users WHERE phone = ?", (phone,)).fetchone()
            if user:
                if user == password: self.send_response(200); r_msg = f"Login successful:{user}:{user}"
                else: self.send_response(401); r_msg = "كلمة السر خاطئة! هذا الرقم محمي."
            else:
                if name:
                    try: conn.cursor().execute("INSERT INTO users (name, phone, password, email) VALUES (?, ?, ?, ?)", (name, phone, password, email or f"{phone}@chat.com")); conn.commit(); self.send_response(200); r_msg = f"Registration successful:{name}:{email}"
                    except: self.send_response(400); r_msg = "خطأ بالتسجيل"
                else: self.send_response(400); r_msg = "هذا الرقم جديد، يرجى كتابة الاسم للتسجيل أول مرة."
            conn.close(); self.send_header("Content-Type", "text/plain; charset=utf-8"); self.end_headers(); self.wfile.write(r_msg.encode('utf-8'))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(parsed.query)
        if parsed.path in ["/", "/index.html"]:
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
            with open("index.html", "r", encoding="utf-8") as f: self.wfile.write(f.read().encode('utf-8'))
            return
        conn = sqlite3.connect(DB)
        if parsed.path == "/search":
            p = q.get('phone', ['']).strip(); u = conn.cursor().execute("SELECT name, email FROM users WHERE phone = ?", (p,)).fetchone()
            res = f"Found:{u}:{u}" if u else "User not found"
            self.send_response(200); self.send_header("Content-Type", "text/plain; charset=utf-8"); self.end_headers(); self.wfile.write(res.encode('utf-8'))
        elif parsed.path == "/send":
            s, rec, m = q.get('sender', ['']).strip(), q.get('receiver', ['']).strip(), q.get('message', ['']).strip()
            if s and rec and m: conn.cursor().execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)", (s, rec, m)); conn.commit()
            self.send_response(200); self.end_headers()
        elif parsed.path == "/get_messages":
            s, rec = q.get('sender', ['']).strip(), q.get('receiver', ['']).strip()
            rows = conn.cursor().execute("SELECT id, sender, message FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY timestamp ASC", (s, rec, rec, s)).fetchall()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps([{"id": r, "sender": r, "message": r} for r in rows]).encode('utf-8'))
        elif parsed.path == "/delete_msg":
            mid = q.get('id', ['']).strip()
            if mid: conn.cursor().execute("DELETE FROM messages WHERE id = ?", (mid,)); conn.commit()
            self.send_response(200); self.end_headers()
        elif parsed.path == "/send_status":
            p, n, t = q.get('phone', ['']).strip(), q.get('name', ['']).strip(), q.get('text', ['']).strip()
            if p and t: conn.cursor().execute("INSERT INTO status (phone, name, text) VALUES (?, ?, ?)", (p, n, t)); conn.commit()
            self.send_response(200); self.end_headers()
        elif parsed.path == "/get_statuses":
            rows = conn.cursor().execute("SELECT name, text FROM status ORDER BY timestamp DESC LIMIT 10").fetchall()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(json.dumps([{"name": r, "text": r} for r in rows]).encode('utf-8'))
        elif parsed.path == "/clear_chat":
            s, rec = q.get('sender', ['']).strip(), q.get('receiver', ['']).strip()
            if s and rec: conn.cursor().execute("DELETE FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)", (s, rec, rec, s)); conn.commit()
            self.send_response(200); self.end_headers()
        conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8082))
    http.server.ThreadingHTTPServer(('0.0.0.0', port), ChatHandler).serve_forever()

