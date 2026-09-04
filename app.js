const SERVER_URL = window.location.protocol + "//" + window.location.host;
let socket = null, currentUser = null, activeChatUser = null, globalAvatarBase64 = "", storyMediaBase64 = "", storyMediaType = "text";

window.onload = function() {
    try { const u = localStorage.getItem("chat_user"); if (u) { currentUser = JSON.parse(u); showChatScreen(); } } catch (e) {}
};
function previewAvatar(e) {
    const f = e.target.files;
    if (f) { const r = new FileReader(); r.onload = () => { globalAvatarBase64 = r.result; document.getElementById("avatar-preview").innerHTML = `<img src="${r.result}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`; }; r.readAsDataURL(f); }
}
function toggleAuthForms() {
    document.getElementById("login-form-box").classList.toggle("hidden"); document.getElementById("register-form-box").classList.toggle("hidden");
}

// 🎯 مصيدة أخطاء السيرفر المجمّعة والشاملة عند التسجيل
async function handleRegister(e) {
    if (e) e.preventDefault();
    const u = document.getElementById("reg-username").value.trim(), p = document.getElementById("reg-pass").value.trim();
    if (!u || !p) return alert("برجاء ملء الحقول");
    
    let report = ["📋 تقرير مصيدة أخطاء التسجيل المجمّع:"];
    try {
        report.push("🔹 1. محاولة الاتصال بـ: " + SERVER_URL + "/api/register");
        const r = await fetch(`${SERVER_URL}/api/register`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: u, password: p, avatar: globalAvatarBase64 }) });
        
        report.push("🔹 2. حالة الـ Response HTTP: " + r.status + " (" + r.statusText + ")");
        const d = await r.json(); 
        
        if (r.ok && d.status === "success") {
            alert(d.message); toggleAuthForms();
        } else {
            report.push("🔴 3. رفض داخلي من السيرفر: " + (d.message || "لا توجد رسالة رفض محددة"));
            alert(report.join("\n\n"));
        }
    } catch (err) { 
        report.push("💥 3. فشل أمني أو انقطاع شبكة (CORS/Failed to fetch)");
        report.push("📝 تفاصيل رسالة الخطأ: " + err.message);
        report.push("💡 نصيحة: تأكد أنك تفتح السيرفر الأخضر النشط cd6f من التبويب المتخفي وليس الرابط القديم.");
        alert(report.join("\n\n")); 
    }
}

// 🎯 مصيدة أخطاء السيرفر المجمّعة والشاملة عند تسجيل الدخول
async function handleLogin(e) {
    if (e) e.preventDefault();
    const u = document.getElementById("login-username").value.trim(), p = document.getElementById("login-pass").value.trim();
    if (!u || !p) return alert("برجاء ملء الحقول");
    
    let report = ["📋 تقرير مصيدة أخطاء الدخول المجمّع:"];
    try {
        report.push("🔹 1. محاولة الاتصال بـ: " + SERVER_URL + "/api/login");
        const r = await fetch(`${SERVER_URL}/api/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: u, password: p }) });
        
        report.push("🔹 2. حالة الـ Response HTTP: " + r.status + " (" + r.statusText + ")");
        const d = await r.json();
        
        if (r.ok && d.status === "success") { 
            currentUser = d.user; localStorage.setItem("chat_user", JSON.stringify(d.user)); showChatScreen(); 
        } else { 
            report.push("🔴 3. رفض داخلي من السيرفر: " + (d.message || "بيانات الدخول غير صحيحة"));
            alert(report.join("\n\n"));
        }
    } catch (err) { 
        report.push("💥 3. فشل أمني أو انقطاع شبكة (CORS/Failed to fetch)");
        report.push("📝 تفاصيل رسالة الخطأ: " + err.message);
        alert(report.join("\n\n")); 
    }
}

function showChatScreen() {
    document.getElementById("auth-screen").classList.add("hidden"); document.getElementById("chat-screen").classList.remove("hidden");
    document.getElementById("current-user-name").innerText = currentUser.username;
    if (currentUser.avatar) document.getElementById("my-avatar-view").innerHTML = `<img src="${currentUser.avatar}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
    initSocketConnection(); loadActiveChatsFromServer(); loadStories();
    setInterval(() => { if (currentUser) { loadActiveChatsFromServer(); loadStories(); } }, 5000);
}
function initSocketConnection() {
    if (typeof io === 'undefined') return;
    try {
        socket = io(SERVER_URL, { transports: ['websocket', 'polling'] });
        socket.on("connect", () => { socket.emit("join", { username: currentUser.username }); });
        socket.on("receive_message", (d) => {
            const s = document.getElementById("notif-sound"); if(s) s.play().catch(()=>{});
            if (activeChatUser && (d.sender_username === activeChatUser.username || d.receiver_username === activeChatUser.username)) fetchActiveChatMessages();
            loadActiveChatsFromServer();
        });
        socket.on("message_deleted", () => { if (activeChatUser) fetchActiveChatMessages(); });
        socket.on("display_typing", (d) => { if (activeChatUser && d.sender === activeChatUser.username) document.getElementById("typing-status").innerText = d.typing ? "يكتب الآن..." : ""; });
    } catch (e) {}
}
function emitTyping() {
    if (!activeChatUser || !socket) return;
    socket.emit("typing", { sender: currentUser.username, receiver: activeChatUser.username, typing: true });
    clearTimeout(window.typingTimeout); window.typingTimeout = setTimeout(() => { socket.emit("typing", { sender: currentUser.username, receiver: activeChatUser.username, typing: false }); }, 2000);
}
function openChat(u, a = "") {
    activeChatUser = { username: u }; document.getElementById("app-sidebar").classList.add("hidden-mobile"); document.getElementById("app-chat-area").classList.remove("hidden-mobile");
    document.getElementById("welcome-chat-view").classList.add("hidden"); document.getElementById("active-chat-view").classList.remove("hidden");
    document.getElementById("active-chat-name").innerText = u; const box = document.getElementById("active-chat-avatar");
    if(box) box.innerHTML = a ? `<img src="${a}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">` : `<i class="fas fa-user"></i>`;
    fetchActiveChatMessages();
}
function backToSidebar() { document.getElementById("app-sidebar").classList.remove("hidden-mobile"); document.getElementById("app-chat-area").classList.add("hidden-mobile"); activeChatUser = null; }
async function loadActiveChatsFromServer() {
    try {
        const r = await fetch(`${SERVER_URL}/api/active-chats?username=${currentUser.username}`), c = await r.json(), container = document.getElementById("chats-list-container"); if(!container) return; container.innerHTML = "";
        if (c.length === 0) { container.innerHTML = `<div class="no-chats">لا توجد محادثات. ابحث عن صديق لبدء دردشة!</div>`; return; }
        c.forEach(chat => {
            const isActive = activeChatUser && activeChatUser.username === chat.username ? "active" : "";
            const item = document.createElement("div"); item.className = `chat-item ${isActive}`;
            item.onclick = () => { const img = item.querySelector('.avatar-circle img'); openChat(chat.username, img ? img.src : ""); };
            item.innerHTML = `<div class="avatar-circle" id="chat-ava-${chat.username}"><i class="fas fa-user"></i></div><div class="chat-item-info"><h4>${chat.username}</h4><p>${chat.last_message}</p></div>`; container.appendChild(item);
            fetch(`${SERVER_URL}/api/user-profile?username=${chat.username}`).then(res => res.json()).then(d => {
                if(d.status === "success" && d.user.avatar) { const b = document.getElementById(`chat-ava-${chat.username}`); if(b) b.innerHTML = `<img src="${d.user.avatar}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`; }
            }).catch(()=>{});
        });
    } catch (err) {}
}
async function handleSearch(e) {
    if (e.key !== "Enter") return; const u = document.getElementById("search-username").value.trim(); if (!u || u === currentUser.username) return;
    try {
        const r = await fetch(`${SERVER_URL}/api/search?username=${u}`), d = await r.json();
        if (d.status === "success") { document.getElementById("search-username").value = ""; openChat(d.user.username, d.user.avatar); } else { alert(d.message); }
    } catch (err) { alert("خطأ أثناء البحث"); }
}
async function fetchActiveChatMessages() {
    if (!activeChatUser) return;
    try {
        const r = await fetch(`${SERVER_URL}/api/messages?sender=${currentUser.username}&receiver=${activeChatUser.username}`), m = await r.json(), box = document.getElementById("messages-box"); if(!box) return; box.innerHTML = "";
        m.forEach(msg => {
            const isMe = msg.sender_username === currentUser.username, bubble = document.createElement("div"); bubble.className = `msg-bubble ${isMe ? 'sent' : 'received'}`; bubble.innerText = msg.message;
            if (!msg.deleted_for_all && isMe) { bubble.style.cursor = "pointer"; bubble.onclick = () => { if(confirm("هل تريد حذف هذه الرسالة لدى الجميع؟")) triggerDeleteMessage(msg.id); }; } box.appendChild(bubble);
        });
        box.scrollTop = box.scrollHeight;
    } catch (err) {}
}
async function triggerDeleteMessage(id) { try { await fetch(`${SERVER_URL}/api/delete-message`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id: id, sender_username: currentUser.username, receiver_username: activeChatUser.username }) }); fetchActiveChatMessages(); } catch(e){} }
async function sendMessage() {
    const input = document.getElementById("message-input"); if(!input) return; const txt = input.value.trim(); if (!txt || !activeChatUser) return; input.value = ""; 
    try { await fetch(`${SERVER_URL}/api/send`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sender_username: currentUser.username, receiver_username: activeChatUser.username, message: txt }) }); fetchActiveChatMessages(); } catch(e){}
}
