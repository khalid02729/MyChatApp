
import http.server, json, urllib.parse, sqlite3, os
DB = "chat.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.cursor().execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, password TEXT)")
    conn.cursor().execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, receiver TEXT, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()
init_db()

def search_user(phone):
    conn = sqlite3.connect(DB)
    user = conn.cursor().execute("SELECT name FROM users WHERE phone = ?", (phone,)).fetchone()
    conn.close()
    return user[0] if user else None

def save_message(sender, receiver, msg_text):
    conn = sqlite3.connect(DB)
    conn.cursor().execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)", (sender, receiver, msg_text))
    conn.commit()
    conn.close()

def get_messages(user1, user2):
    conn = sqlite3.connect(DB)
    rows = conn.cursor().execute("SELECT sender, message FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY timestamp ASC", (user1, user2, user2, user1)).fetchall()
    conn.close()
    return [{"sender": r[0], "message": r[1]} for r in rows]

def clear_chat_db(user1, user2):
    conn = sqlite3.connect(DB)
    conn.cursor().execute("DELETE FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)", (user1, user2, user2, user1))
    conn.commit()
    conn.close()

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp</title>
    <link rel="stylesheet" href="https://cloudflare.com">
    <style>
        @import url('https://googleapis.com');
        * { margin:0; padding:0; box-sizing:border-box; font-family:'Tajawal', sans-serif; }
        body { background:#111b21; color:#e9edef; height:100vh; display:flex; justify-content:center; align-items:center; }
        .app { width:100%; max-width:480px; height:100vh; background:#222e35; display:flex; flex-direction:column; }
        .box { margin:auto; width:85%; text-align:center; background:#111b21; padding:30px 20px; border-radius:16px; }
        .logo { font-size:60px; color:#00a884; margin-bottom:15px; }
        .input-g { margin-bottom:15px; }
        .input-g input { width:100%; padding:12px; background:#2a3942; border:1px solid #3b4a54; border-radius:8px; color:white; outline:none; text-align:right; }
        .btn { background:#00a884; color:#111b21; border:none; padding:12px; width:100%; border-radius:8px; font-weight:700; cursor:pointer; }
        .link { color:#53bdeb; font-size:13px; cursor:pointer; display:inline-block; margin-top:15px; }
        .hidden { display:none !important; }
        .header { background:#202c33; padding:15px; display:flex; justify-content:space-between; align-items:center; }
        .view { flex:1; padding:20px; overflow-y:auto; background:#0b141a; display:flex; flex-direction:column; gap:8px; }
        .bubble { max-width:75%; padding:8px 12px; border-radius:8px; font-size:14px; }
        .bubble.sent { background:#005c4b; align-self:flex-start; }
        .bubble.received { background:#202c33; align-self:flex-end; }
        .footer { padding:10px; background:#202c33; display:flex; gap:10px; }
        .input-f { flex:1; background:#2a3942; border:none; border-radius:8px; padding:11px; color:white; outline:none; }
        .s-btn { background:#00a884; border:none; width:40px; height:40px; border-radius:50%; color:#111b21; cursor:pointer; }
    </style>
</head>
<body>
    <div class="app">
        <div id="l-view" class="box">
            <div class="logo"><i class="fa-brands fa-whatsapp"></i></div>
            <h2>تسجيل الدخول</h2><br>
            <div class="input-g"><input type="tel" id="l-phone" placeholder="رقم الموبايل"></div>
            <div class="input-g"><input type="password" id="l-pass" placeholder="كلمة السر"></div>
            <button id="b-login" class="btn">دخول</button>
            <span id="to-r" class="link">إنشاء حساب جديد الحين</span>
        </div>
        <div id="r-view" class="box hidden">
            <div class="logo"><i class="fa-brands fa-whatsapp" style="color:#53bdeb;"></i></div>
            <h2>إنشاء حساب جديد</h2><br>
            <div class="input-g"><input type="text" id="r-name" placeholder="الاسم الكامل"></div>
            <div class="input-g"><input type="tel" id="r-phone" placeholder="رقم الموبايل"></div>
            <div class="input-g"><input type="password" id="r-pass" placeholder="كلمة السر"></div>
            <button id="b-reg" class="btn" style="background:#53bdeb;">تأمين الحساب</button>
            <span id="to-l" class="link">لديك حساب؟ سجل دخولك</span>
        </div>
        <div id="c-view" class="hidden" style="flex-direction:column; height:100%;">
            <header class="header">
                <h1 id="h-title">WhatsApp</h1>
                <div style="display:flex; gap:15px;"><i id="b-clear" class="fa-solid fa-trash-can" style="display:none; cursor:pointer;"></i><i id="b-out" class="fa-solid fa-right-from-bracket" style="cursor:pointer;"></i></div>
            </header>
            <div style="padding:8px; background:#111b21; display:flex; gap:8px;"><input type="tel" id="f-phone" placeholder="رقم صاحبك..." style="flex:1; background:#202c33; border:none; border-radius:8px; padding:8px; color:white; outline:none;"><button id="b-find" style="background:#00a884; border:none; padding:0 10px; border-radius:8px; font-weight:700;">بحث</button></div>
            <div id="v-box" class="view"></div>
            <div class="footer"><input type="text" id="m-input" class="input-f" placeholder="اكتب رسالة..." disabled><button id="b-send" class="s-btn" disabled><i class="fa-solid fa-paper-plane"></i></button></div>
        </div>
    </div>
    <script>
        let myP='', targetP='', sync=null;
        document.getElementById('to-r').addEventListener('click', ()=>{ document.getElementById('l-view').classList.add('hidden'); document.getElementById('r-view').classList.remove('hidden'); });
        document.getElementById('to-l').addEventListener('click', ()=>{ document.getElementById('r-view').classList.add('hidden'); document.getElementById('l-view').classList.remove('hidden'); });
        
        document.getElementById('b-login').addEventListener('click', async()=>{
            const p=document.getElementById('log-phone')?.value || document.getElementById('l-phone').value, o=document.getElementById('l-pass').value;
            const fd=new URLSearchParams(); fd.append('phone',p); fd.append('password',o);
            const res=await fetch('/login',{method:'POST',body:fd});
            if(res.status===200){ myP=p; enter(); } else { alert(await res.text()); }
        });
        document.getElementById('b-reg').addEventListener('click', async()=>{
            const n=document.getElementById('r-name').value, p=document.getElementById('r-phone').value, o=document.getElementById('r-pass').value;
            const fd=new URLSearchParams(); fd.append('name',n); fd.append('phone',p); fd.append('password',o);
            const res=await fetch('/login',{method:'POST',body:fd});
            if(res.status===200){ myP=p; alert('تم الحفظ!'); enter(); } else { alert(await res.text()); }
        });
        function enter(){ document.getElementById('l-view').classList.add('hidden'); document.getElementById('r-view').classList.add('hidden'); document.getElementById('c-view').style.display='flex'; document.getElementById('c-view').classList.remove('hidden'); }
        
        document.getElementById('b-find').addEventListener('click', async()=>{
            const p=document.getElementById('f-phone').value.trim();
            if(!p || p===myP) return;
            const res=await fetch('/search?phone='+p); const t=await res.text();
            if(t.startsWith('Found:')){ targetP=p; document.getElementById('h-title').innerText=t.replace('Found:',''); document.getElementById('m-input').disabled=false; document.getElementById('b-send').disabled=false; document.getElementById('b-clear').style.display='block'; if(sync) clearInterval(sync); syncMsg(); sync=setInterval(syncMsg,2000); } else { alert('غير مسجل!'); }
        });
        document.getElementById('b-send').addEventListener('click', async()=>{
            const m=document.getElementById('m-input').value.trim(); if(!m||!targetP) return;
            await fetch('/send?sender='+myP+'&receiver='+targetP+'&message='+encodeURIComponent(m)); document.getElementById('m-input').value=''; syncMsg();
        });
        async function syncMsg(){
            if(!targetP) return; const res=await fetch('/get_messages?sender='+myP+'&receiver='+targetP); const list=await res.json(); const box=document.getElementById('v-box'); box.innerHTML='';
            list.forEach(m=>{ const d=document.createElement('div'); d.className='bubble '+(m.sender===myP?'sent':'received'); d.innerText=m.message; box.appendChild(d); }); box.scrollTop=box.scrollHeight;
        }
        document.getElementById('b-clear').addEventListener('click', async()=>{ if(confirm('مسح الشات؟')){ await fetch('/clear_chat?sender='+myP+'&receiver='+targetP); syncMsg(); }});
        document.getElementById('b-out').addEventListener('click', ()=>{ location.reload(); });
    </script>
</body>
</html>
"""

class ChatHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/login":
            cl = int(self.headers['Content-Length'])
            params = urllib.parse.parse_qs(self.rfile.read(cl).decode('utf-8'))
            name, phone, password = params.get('name', [''])[0].strip(), params.get('phone', [''])[0].strip(), params.get('password', [''])[0].strip()

