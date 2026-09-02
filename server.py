
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

def clear_chat_db(user1, user2):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM messages 
        WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
    """, (user1, user2, user2, user1))
    conn.commit()
    conn.close()

# واجهة الواتساب الأخضر المودرن
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp | Khalid Edition</title>
    <link rel="stylesheet" href="https://cloudflare.com">
    <style>
        @import url('https://googleapis.com');
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', 'Tajawal', sans-serif; }
        body { background-color: #111b21; color: #e9edef; height: 100vh; display: flex; justify-content: center; align-items: center; }
        .app-container { width: 100%; max-width: 480px; height: 100vh; background-color: #222e35; display: flex; flex-direction: column; position: relative; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
        
        /* شاشات الدخول والتسجيل */
        .auth-container { margin: auto; width: 85%; text-align: center; background: #111b21; padding: 30px 20px; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
        .auth-logo { font-size: 60px; color: #00a884; margin-bottom: 15px; }
        .auth-container h2 { font-size: 22px; margin-bottom: 8px; color: #e9edef; }
        .auth-container p { font-size: 13px; color: #8696a0; margin-bottom: 25px; }
        .input-group { position: relative; margin-bottom: 15px; }
        .input-group input { width: 100%; padding: 12px 15px; background: #2a3942; border: 1px solid #3b4a54; border-radius: 8px; color: white; font-size: 14px; outline: none; text-align: right; }
        .input-group input:focus { border-color: #00a884; }
        .action-btn { background: #00a884; color: #111b21; border: none; padding: 12px; width: 100%; border-radius: 8px; font-size: 15px; font-weight: 700; cursor: pointer; transition: 0.2s; }
        .action-btn:hover { background: #008f6f; }
        .toggle-link { color: #53bdeb; font-size: 13px; cursor: pointer; display: inline-block; margin-top: 15px; text-decoration: underline; }
        .hidden { display: none !important; }

        /* الشاشة الرئيسية للواتساب */
        .wp-header { background: #202c33; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; color: #8696a0; border-bottom: 1px solid #2a3942; }
        .wp-header h1 { font-size: 20px; color: #e9edef; font-weight: 700; }
        .wp-tabs { background: #202c33; display: flex; border-bottom: 1px solid #2a3942; text-align: center; }
        .tab-item { flex: 1; padding: 12px 0; color: #8696a0; font-weight: 700; font-size: 14px; cursor: pointer; text-transform: uppercase; }
        .tab-item.active { color: #00a884; border-bottom: 3px solid #00a884; }
        
        /* قائمة الدردشات والبحث */
        .search-chat-box { padding: 8px 12px; background: #111b21; display: flex; gap: 8px; }
        .search-chat-input { flex: 1; background: #202c33; border: none; border-radius: 8px; padding: 8px 15px; color: white; font-size: 14px; outline: none; }
        .search-chat-btn { background: #00a884; border: none; color: #111b21; padding: 0 14px; border-radius: 8px; font-weight: 700; cursor: pointer; }
        
        /* فيوبورت الرسائل وخلفية الواتساب الشهيرة */
        .chat-viewport { flex: 1; padding: 20px; overflow-y: auto; background-color: #0b141a; background-image: url('https://githubusercontent.com'); background-blend-mode: overlay; display: flex; flex-direction: column; gap: 8px; }
        .msg-bubble { max-width: 75%; padding: 8px 12px; border-radius: 8px; font-size: 14.5px; position: relative; line-height: 1.4; box-shadow: 0 1px 1px rgba(0,0,0,0.2); }
        .msg-bubble.sent { background: #005c4b; color: #e9edef; align-self: flex-start; border-top-right-radius: 0; }
        .msg-bubble.received { background: #202c33; color: #e9edef; align-self: flex-end; border-top-left-radius: 0; }
        
        /* بار الإرسال السفلي */
        .wp-footer { padding: 10px 15px; background: #202c33; display: flex; gap: 10px; align-items: center; }
        .wp-input-field { flex: 1; background: #2a3942; border: none; border-radius: 8px; padding: 11px 15px; color: white; font-size: 14px; outline: none; }
        .wp-send-btn { background: #00a884; border: none; width: 40px; height: 40px; border-radius: 50%; color: #111b21; cursor: pointer; display: flex; justify-content: center; align-items: center; font-size: 16px; }
        .wp-send-btn:disabled { background: #2a3942; color: #8696a0; cursor: not-allowed; }
        .action-icon { cursor: pointer; color: #8696a0; font-size: 18px; transition: 0.2s; }
        .action-icon:hover { color: #ef4444; }
    </style>
</head>
<body>

    <div class="app-container">
        <!-- 1️⃣ شاشة تسجيل الدخول للحسابات القديمة -->
        <div id="login-view" class="auth-container">
            <div class="auth-logo"><i class="fa-brands fa-whatsapp"></i></div>
            <h2>تسجيل الدخول إلى واتساب</h2>
            <p>ادخل رقمك وكلمة السر للمتابعة</p>
            <div class="input-group"><input type="tel" id="log-phone" placeholder="رقم الموبايل"></div>
            <div class="input-group"><input type="password" id="log-pass" placeholder="كلمة السر"></div>
            <button id="btn-login-submit" class="action-btn">تسجيل الدخول</button>
            <span id="to-register" class="toggle-link">ليس لديك حساب؟ إنشاء حساب جديد الحين</span>
        </div>

        <!-- 2️⃣ شاشة إنشاء حساب جديد لأول مرة -->
        <div id="register-view" class="auth-container hidden">
            <div class="auth-logo"><i class="fa-brands fa-whatsapp" style="color: #53bdeb;"></i></div>
            <h2>إنشاء حساب جديد</h2>
            <p>سجل بياناتك لأول مرة لتأمين رقمك</p>
            <div class="input-group"><input type="text" id="reg-name" placeholder="الاسم الكامل"></div>
            <div class="input-group"><input type="tel" id="reg-phone" placeholder="رقم الموبايل"></div>
            <div class="input-group"><input type="password" id="reg-pass" placeholder="اختر كلمة سر قوية"></div>
            <button id="btn-register-submit" class="action-btn" style="background: #53bdeb;">إنشاء الحساب وتأمينه</button>
            <span id="to-login" class="toggle-link">لديك حساب بالفعل؟ سجل دخولك الحين</span>
        </div>

        <!-- 3️⃣ شاشة الشات والواجهة الرئيسية الشبيهة بالواتساب -->
        <div id="main-chat-view" class="hidden" style="flex-direction: column; height: 100%;">
            <header class="wp-header">
                <h1 id="chat-header-title">WhatsApp</h1>
                <div style="display: flex; gap: 15px; align-items: center;">
                    <i id="clear-chat-icon" class="fa-solid fa-trash-can action-icon" title="مسح محادثات هذا الصديق" style="display: none;"></i>
                    <i id="logout-icon" class="fa-solid fa-right-from-bracket action-icon" title="تسجيل الخروج" style="color: #8696a0;"></i>
                </div>
            </header>

            <div class="wp-tabs">
                <div class="tab-item active">الدردشات</div>
                <div id="status-tab" class="tab-item">الحالات (قريباً)</div>
            </div>

            <div class="search-chat-box">
                <input type="tel" id="find-friend-phone" placeholder="اكتب رقم موبايل صاحبك لبدء الشات...">
                <button id="btn-find-friend" class="search-chat-box search-chat-btn">بحث</button>
            </div>

            <div id="wp-chat-box" class="chat-viewport">
                <div class="empty-state">ابحث عن رقم موبايل صديقك المسجل لفتح محادثة واتساب الخضراء المشفرة أونلاين الحين!</div>
            </div>

            <div class="wp-footer">
                <input type="text" id="wp-msg-input" class="wp-input-field" placeholder="اكتب رسالة..." disabled>
                <button id="btn-wp-send" class="wp-send-btn" disabled><i class="fa-solid fa-paper-plane"></i></button>
            </div>
        </div>
    </div>

