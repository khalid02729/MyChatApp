import sqlite3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import json

PORT = 8082
DB = "chat.db"

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
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/search":
            params = parse_qs(parsed.query)
            phone = params.get("phone", [""])[0].strip()
            user_name = search_user(phone)
            
            if user_name:
                response = f"Found: {user_name}"
            else:
                response = "User not found"
            
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
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
                
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))
            return

        if parsed.path == "/get_messages":
            params = parse_qs(parsed.query)
            sender = params.get("sender", [""])[0].strip()
            receiver = params.get("receiver", [""])[0].strip()
            
            messages = get_messages(sender, receiver)
            response = json.dumps(messages)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))
            return

        return super().do_GET()

    import os
    port = int(os.environ.get('PORT', 8082))
    server = ThreadingHTTPServer(('0.0.0.0', port), ChatHandler)
    print(f"Server running on port {port}...")
    server.serve_forever()
    
