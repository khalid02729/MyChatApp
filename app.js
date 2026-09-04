const SERVER_URL = window.location.protocol + "//" + window.location.host;
let socket = null, currentUser = null, activeChatUser = null, activeChats = {}, globalAvatarBase64 = "";
let storyMediaBase64 = "", storyMediaType = "text";

window.onload = function() {
    try {
        const savedUser = localStorage.getItem("chat_user");
        if (savedUser) { currentUser = JSON.parse(savedUser); showChatScreen(); }
    } catch (e) {}
};

function previewAvatar(event) {
    const file = event.target.files;
    if (file && file[0]) {
        const reader = new FileReader();
        reader.onload = function() {
            globalAvatarBase64 = reader.result;
            document.getElementById("avatar-preview").innerHTML = `<img src="${globalAvatarBase64}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
        };
        reader.readAsDataURL(file[0]);
    }
}

function toggleAuthForms() {
    document.getElementById("login-form-box").classList.toggle("hidden");
    document.getElementById("register-form-box").classList.toggle("hidden");
}

async function handleRegister(event) {
    if (event) event.preventDefault();
    const u = document.getElementById("reg-username").value.trim();
    const p = document.getElementById("reg-pass").value.trim();
    if (!u || !p) return alert("برجاء ملء الحقول");
    try {
        const r = await fetch(`${SERVER_URL}/api/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: u, password: p, avatar: globalAvatarBase64 })
        });
        const d = await r.json();
        if (r.ok) {
            alert(d.message);
            if (d.status === "success") toggleAuthForms();
        } else {
            alert("🚨 السيرفر رفض التسجيل وقال:\n" + d.message);
        }
    } catch (err) { 
        alert("🚨 مصيدة الشبكة: السيرفر لم يستقبل الطلب أصلاً!\nتفاصيل الخطأ: " + err.message); 
    }
}

async function handleLogin(event) {
    if (event) event.preventDefault();
    const u = document.getElementById("login-username").value.trim();
    const p = document.getElementById("login-pass").value.trim();
    if (!u || !p) return alert("برجاء ملء الحقول");
    try {
        const r = await fetch(`${SERVER_URL}/api/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: u, password: p })
        });
        const d = await r.json();
        if (r.ok && d.status === "success") {
            currentUser = d.user;
            localStorage.setItem("chat_user", JSON.stringify(currentUser));
            showChatScreen();
        } else {
            alert("🚨 السيرفر رفض الدخول وقال:\n" + d.message);
        }
    } catch (err) { 
        alert("🚨 مصيدة الشبكة: خطأ بالاتصال بالسيرفر أثناء الدخول!\nتفاصيل الخطأ: " + err.message); 
    }
}

function showChatScreen() {
    document.getElementById("auth-screen").classList.add("hidden");
    document.getElementById("chat-screen").classList.remove("hidden");
    document.getElementById("current-user-name").innerText = currentUser.username;
    if (currentUser.avatar) {
        document.getElementById("my-avatar-view").innerHTML = `<img src="${currentUser.avatar}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
    }
    initSocketConnection();
    loadActiveChatsFromServer();
    loadStories();
    setInterval(() => { if (currentUser) { loadActiveChatsFromServer(); loadStories(); } }, 5000);
}

function initSocketConnection() {
    if (typeof io === 'undefined') return;
    try {
        socket = io(SERVER_URL, { transports: ['websocket', 'polling'] });
        socket.on("connect", () => { socket.emit("join", { username: currentUser.username }); });
        socket.on("receive_message", (data) => {
            const s = document.getElementById("notif-sound");
            if(s) s.play().catch(()=>{});
            if (activeChatUser && (data.sender_username === activeChatUser.username || data.receiver_username === activeChatUser.username)) { fetchActiveChatMessages(); }
            loadActiveChatsFromServer();
        });
        socket.on("message_deleted", () => { if (activeChatUser) fetchActiveChatMessages(); });
        socket.on("display_typing", (data) => {
            if (activeChatUser && data.sender === activeChatUser.username) {
                document.getElementById("typing-status").innerText = data.typing ? "يكتب الآن..." : "";
            }
        });
    } catch (e) {}
}

function emitTyping() {
    if (!activeChatUser || !socket) return;
    socket.emit("typing", { sender: currentUser.username, receiver: activeChatUser.username, typing: true });
    clearTimeout(window.typingTimeout);
    window.typingTimeout = setTimeout(() => { socket.emit("typing", { sender: currentUser.username, receiver: activeChatUser.username, typing: false }); }, 2000);
}

function openChat(username, avatarImg = "") {
    activeChatUser = { username: username };
    document.getElementById("app-sidebar").classList.add("hidden-mobile");
    document.getElementById("app-chat-area").classList.remove("hidden-mobile");
    document.getElementById("welcome-chat-view").classList.add("hidden");
    document.getElementById("active-chat-view").classList.remove("hidden");
    document.getElementById("active-chat-name").innerText = activeChatUser.username;
    const box = document.getElementById("active-chat-avatar");
    if(box) { box.innerHTML = avatarImg ? `<img src="${avatarImg}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">` : `<i class="fas fa-user"></i>`; }
    fetchActiveChatMessages();
}

function backToSidebar() {
    document.getElementById("app-sidebar").classList.remove("hidden-mobile");
    document.getElementById("app-chat-area").classList.add("hidden-mobile");
    activeChatUser = null;
}

async function loadActiveChatsFromServer() {
    try {
        const r = await fetch(`${SERVER_URL}/api/active-chats?username=${currentUser.username}`);
        const c = await r.json();
        renderChatsList(c);
    } catch (err) {}
}

function renderChatsList(serverChats = []) {
    const container = document.getElementById("chats-list-container");
    if(!container) return;
    container.innerHTML = "";
    if (serverChats.length === 0) {
        container.innerHTML = `<div class="no-chats">لا توجد محادثات. ابحث عن صديق لبدء دردشة!</div>`;
        return;
    }
    serverChats.forEach(chat => {
        const isActive = activeChatUser && activeChatUser.username === chat.username ? "active" : "";
        const item = document.createElement("div");
        item.className = `chat-item ${isActive}`;
        item.onclick = () => { const img = item.querySelector('.avatar-circle img'); openChat(chat.username, img ? img.src : ""); };
        item.innerHTML = `<div class="avatar-circle" id="chat-ava-${chat.username}"><i class="fas fa-user"></i></div><div class="chat-item-info"><h4>${chat.username}</h4><p>${chat.last_message}</p></div>`;
        container.appendChild(item);

        fetch(`${SERVER_URL}/api/user-profile?username=${chat.username}`).then(r => r.json()).then(d => {
            if(d.status === "success" && d.user.avatar) {
                const b = document.getElementById(`chat-ava-${chat.username}`);
                if(b) b.innerHTML = `<img src="${d.user.avatar}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
            }
        }).catch(()=>{});
    });
}

async function handleSearch(event) {
    if (event.key !== "Enter") return;
    const u = document.getElementById("search-username").value.trim();
    if (!u || u === currentUser.username) return;
    try {
        const r = await fetch(`${SERVER_URL}/api/search?username=${u}`);
        const d = await r.json();
        if (d.status === "success") { document.getElementById("search-username").value = ""; openChat(d.user.username, d.user.avatar); }
        else { alert(d.message); }
    } catch (err) { alert("خطأ أثناء البحث"); }
}

async function fetchActiveChatMessages() {
    if (!activeChatUser) return;
    try {
        const r = await fetch(`${SERVER_URL}/api/messages?sender=${currentUser.username}&receiver=${activeChatUser.username}`);
        const m = await r.json();
        renderMessages(m);
    } catch (err) {}
}

function renderMessages(messages = []) {
    const box = document.getElementById("messages-box");
    if(!box) return;
    box.innerHTML = "";
    messages.forEach(msg => {
        const isMe = msg.sender_username === currentUser.username;
        const bubble = document.createElement("div");
        bubble.className = `msg-bubble ${isMe ? 'sent' : 'received'}`;
        bubble.innerText = msg.message;
        if (!msg.deleted_for_all && isMe) {
            bubble.style.cursor = "pointer";
            bubble.onclick = () => { if(confirm("هل تريد حذف هذه الرسالة لدى الجميع؟")) { triggerDeleteMessage(msg.id); } };
        }
        box.appendChild(bubble);
    });
    box.scrollTop = box.scrollHeight;
}

async function triggerDeleteMessage(msgId) {
    try {
        await fetch(`${SERVER_URL}/api/delete-message`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: msgId, sender_username: currentUser.username, receiver_username: activeChatUser.username })
        });
        fetchActiveChatMessages();
    } catch(e){}
}

async function sendMessage() {
    const input = document.getElementById("message-input");
    if(!input) return;
    const txt = input.value.trim();
    if (!txt || !activeChatUser) return;
    input.value = ""; 
    try {
        await fetch(`${SERVER_URL}/api/send`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sender_username: currentUser.username, receiver_username: activeChatUser.username, message: txt })
        });
