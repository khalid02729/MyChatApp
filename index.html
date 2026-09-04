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
        .btn { background: #00a884; color: #111b21; border: none; padding: 12px; width: 100%; border-radius: 8px; font-size: 15px; font-weight: 700; cursor: pointer; }
        .link { color: #53bdeb; font-size: 13px; cursor: pointer; display: inline-block; margin-top: 15px; }
        .hidden { display: none !important; }
        .wp-header { background: #202c33; padding: 12px 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #2a3942; }
        .header-center { display: flex; align-items: center; gap: 10px; cursor: pointer; }
        .pfp { width: 40px; height: 40px; background: #00a884; color: #111b21; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: 700; font-size: 18px; }
        .search-area { padding: 8px 12px; background: #111b21; display: flex; gap: 8px; }
        .search-area input { flex: 1; background: #202c33; border: none; border-radius: 8px; padding: 8px 15px; color: white; font-size: 14px; outline: none; }
        .search-area button { background: #00a884; border: none; padding: 0 15px; border-radius: 8px; font-weight: 700; cursor: pointer; }
        .status-bar { padding: 10px; background: #1f2c34; display: flex; gap: 12px; overflow-x: auto; border-bottom: 1px solid #2a3942; align-items: center; }
        .status-item { display: flex; flex-direction: column; align-items: center; font-size: 11px; color: #8696a0; cursor: pointer; min-width: 55px; }
        .status-circle { width: 42px; height: 42px; border: 2px dashed #00a884; border-radius: 50%; display: flex; justify-content: center; align-items: center; color: white; font-weight: 700; margin-bottom: 4px; }
        .add-status-btn { background: #2a3942; border: none; width: 35px; height: 35px; border-radius: 50%; color: #00a884; cursor: pointer; font-size: 16px; }
        .chat-view { flex: 1; padding: 20px; overflow-y: auto; background-color: #0b141a; background-image: url('https://githubusercontent.com'); background-blend-mode: overlay; display: flex; flex-direction: column; gap: 8px; }
        .msg { max-width: 85%; padding: 8px 12px; border-radius: 8px; font-size: 14.5px; line-height: 1.4; word-break: break-word; cursor: pointer; }
        .msg.sent { background: #005c4b; color: #e9edef; align-self: flex-start; border-top-right-radius: 0; }
        .msg.received { background: #202c33; color: #e9edef; align-self: flex-end; border-top-left-radius: 0; }
        .empty { text-align: center; margin: auto; color: #8696a0; font-size: 13px; }
        .wp-footer { padding: 10px 15px; background: #202c33; display: flex; gap: 10px; align-items: center; }
        .wp-input { flex: 1; background: #2a3942; border: none; border-radius: 8px; padding: 11px 15px; color: white; font-size: 14px; outline: none; }
        .wp-send { background: #00a884; border: none; width: 40px; height: 40px; border-radius: 50%; color: #111b21; cursor: pointer; font-size: 16px; display: flex; justify-content: center; align-items: center; }
        .modal { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); display: flex; justify-content: center; align-items: center; z-index: 10; }
        .modal-card { background: #222e35; width: 85%; padding: 25px; border-radius: 16px; text-align: center; border: 1px solid #3b4a54; }
        .modal-pfp { width: 80px; height: 80px; background: #00a884; color: #111b21; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 35px; font-weight: 700; margin:  0 auto 15px; }
        .modal-card h3 { margin-bottom: 10px; font-size: 20px; }
        .modal-card p { color: #8696a0; font-size: 14px; margin-bottom: 8px; }
        .close-btn { background: #ef4444; color: white; border: none; padding: 8px 20px; border-radius: 8px; margin-top: 15px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="app-container">
        <div id="login-view" class="auth-box">
            <div class="auth-logo"><i class="fa-brands fa-whatsapp"></i></div>
            <h2>تسجيل الدخول</h2>
            <div class="input-g"><input type="tel" id="l-phone" placeholder="رقم الموبايل"></div>
            <div class="input-g"><input type="password" id="l-pass" placeholder="كلمة السر"></div>
            <button id="b-login" class="btn">دخول</button>
            <span id="to-r" class="link">إنشاء حساب تأميني جديد الحين</span>
        </div>
        <div id="register-view" class="auth-box hidden">
            <div class="auth-logo"><i class="fa-brands fa-whatsapp" style="color: #53bdeb;"></i></div>
            <h2>إنشاء حساب آمن</h2>
            <div class="input-g"><input type="text" id="r-name" placeholder="الاسم الكامل"></div>
            <div class="input-g"><input type="email" id="r-email" placeholder="البريد الإلكتروني"></div>
            <div class="input-g"><input type="tel" id="r-phone" placeholder="رقم الموبايل"></div>
            <div class="input-g"><input type="password" id="r-pass" placeholder="كلمة السر"></div>
            <button id="b-reg" class="btn" style="background:#53bdeb;">إنشاء الحساب</button>
            <span id="to-l" class="link">لديك حساب؟ سجل دخولك</span>
        </div>
        <div id="main-view" class="hidden" style="flex-direction: column; height: 100%;">
            <header class="wp-header">
                <div id="header-profile-trigger" class="header-center">
                    <div id="top-pfp" class="pfp">خ</div>
                    <h1 id="h-title">WhatsApp</h1>
                </div>
                <div style="display:flex; gap:15px; align-items:center;">
                    <i id="b-clear-all" class="fa-solid fa-trash-can" style="display:none; cursor:pointer; color:#8696a0;" title="مسح المحادثة بالكامل"></i>
                    <i id="b-out" class="fa-solid fa-right-from-bracket" style="cursor:pointer; color:#8696a0; font-size:18px;"></i>
                </div>
            </header>
            <div class="search-area"><input type="tel" id="f-phone" placeholder="ابحث برقم موبايل صاحبك..."><button id="b-find">بحث</button></div>
            <div class="status-bar">
                <button id="add-status" class="add-status-btn"><i class="fa-solid fa-plus"></i></button>
                <div id="status-list" style="display:flex; gap:10px;"></div>
            </div>
            <div id="v-box" class="chat-view"><div class="empty">ابحث عن رقم صديق مسجل لفتح محادثة الواتساب الموحدة أونلاين الحين!</div></div>
            <div class="wp-footer"><input type="text" id="m-input" class="wp-input" placeholder="اكتب رسالة شيك..." disabled><button id="b-send" class="wp-send" disabled><i class="fa-solid fa-paper-plane"></i></button></div>
        </div>
        <div id="profile-modal" class="modal hidden">
            <div class="modal-card">
                <div id="modal-pfp-img" class="modal-pfp">خ</div>
                <h3 id="modal-name">---</h3>
                <p id="modal-phone">الرقم: ---</p>
                <p id="modal-email">البريد: ---</p>
                <button id="close-modal" class="close-btn">إغلاق</button>
            </div>
        </div>
    </div>
    <script>
        let myP='', myName='', myEmail='', targetP='', targetN='', targetE='', sync=null;
        document.getElementById('to-r').addEventListener('click', ()=>{ document.getElementById('login-view').classList.add('hidden'); document.getElementById('register-view').classList.remove('hidden'); });
        document.getElementById('to-l').addEventListener('click', ()=>{ document.getElementById('register-view').classList.add('hidden'); document.getElementById('login-view').classList.remove('hidden'); });
        document.getElementById('b-login').addEventListener('click', async()=>{
            const p=document.getElementById('l-phone').value.trim(), o=document.getElementById('l-pass').value.trim(); if(!p||!o) return;
            const fd=new URLSearchParams(); fd.append('phone',p); fd.append('password',o);
            const res=await fetch('/login',{method:'POST',body:fd}); const txt=await res.text();
            if(res.status===200){ myP=p; myName=txt.split(':')[1]; myEmail=txt.split(':')[2]; enter(); } else { alert(txt); }
        });
        document.getElementById('b-reg').addEventListener('click', async()=>{
