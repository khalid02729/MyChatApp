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
            password TEXT
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

init_db()

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

class ChatHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == "/login":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = urllib.parse.parse_qs(post_data)
            
            name = params.get('name', [''])[0].strip()
            phone = params.get('phone', [''])[0].strip()
            password = params.get('password', [''])[0].strip()
            
            if not phone or not password:
                self.send_response(400)
                self.end_headers()
                self.wfile.write("Missing fields".encode('utf-8'))
                return

            conn = sqlite3.connect(DB)
            cursor = conn.cursor()
            cursor.execute("SELECT name, password FROM users WHERE phone = ?", (phone,))
            user = cursor.fetchone()

            if user:
                if user[1] == password:
                    response_msg = f"Login successful:{user[0]}"
                    self.send_response(200)
                else:
                    response_msg = "Wrong password"
                    self.send_response(401)
            else:
                if name:
                    try:
                        cursor.execute("INSERT INTO users (name, phone, password) VALUES (?, ?, ?)", (name, phone, password))
                        conn.commit()
                        response_msg = f"Registration successful:{name}"
                        self.send_response(200)
                    except sqlite3.IntegrityError:
                        response_msg = "Error creating user"
                        self.send_response(400)
                else:
                    response_msg = "Please enter your name to register"
                    self.send_response(400)

            conn.close()
            self.end_headers()
            self.wfile.write(response_msg.encode('utf-8'))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == "/search":
            params = urllib.parse.parse_qs(parsed.query)
            phone = params.get('phone', [''])[0].strip()
            user_name = search_user(phone)
            
            if user_name:
                response = f"Found: {user_name}"
            else:
                response = "User not found"
                
            self.send_response(200)
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            return

        if parsed.path == "/send":
            params = urllib.parse.parse_qs(parsed.query)
            sender = params.get('sender', [''])[0].strip()
            receiver = params.get('receiver', [''])[0].strip()
            msg_text = params.get('message', [''])[0].strip()
            
            if sender and receiver and msg_text:
                save_message(sender, receiver, msg_text)
                response = "Message sent and saved!"
            else:
                response = "Missing data"
                
            self.send_response(200)
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            return

        if parsed.path == "/get_messages":
            params = urllib.parse.parse_qs(parsed.query)
            sender = params.get('sender', [''])[0].strip()
            receiver = params.get('receiver', [''])[0].strip()
            
            messages = get_messages(sender, receiver)
            response = json.dumps(messages)
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            return

        return super().do_GET()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8082))
    server = http.server.ThreadingHTTPServer(('0.0.0.0', port), ChatHandler)
    print(f"Server running on port {port}...")
    server.serve_forever()
