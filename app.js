const SERVER_URL = "https://mychatapp-production-b225.up.railway.app"; 
let socket = null; 
let currentUser = null;
let activeChatUser = null;
let activeChats = {}; 
let globalAvatarBase64 = "";

document.addEventListener("DOMContentLoaded", () => {
    const savedUser = localStorage.getItem("chat_user");
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        showChatScreen();
    }
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    if (loginForm) loginForm.addEventListener("submit", handleLogin);
    if (registerForm) registerForm.addEventListener("submit", handleRegister);
});

function previewAvatar(event) {
    const file = event.target.files;
    if (file && file[0]) {
        const reader = new FileReader();
        reader.onload = function() {
            globalAvatarBase64 = reader.result;
            document.getElementById("avatar-preview").innerHTML = `<img src="${globalAvatarBase64}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
        }
        reader.readAsDataURL(file[0]);
    }
}

function toggleAuthForms() {
    document.getElementById("login-form").classList.toggle("hidden");
    document.getElementById("register-form").classList.toggle("hidden");
}

async function handleRegister(event) {
    if (event) event.preventDefault();
    const username = document.getElementById("reg-username").value.trim();
    const password = document.getElementById("reg-pass").value.trim();
    if (!username || !password) return alert("برجاء ملء جميع الحقول");
    try {
        const response = await fetch(`${SERVER_URL}/api/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password, avatar: globalAvatarBase64 })
        });
        const data = await response.json();
        alert(data.message);
        if (data.status === "success") toggleAuthForms();
    } catch (err) { alert("خطأ في الاتصال بالسيرفر"); }
}

async function handleLogin(event) {
    if (event) event.preventDefault();
    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-pass").value.trim();
    if (!username || !password) return alert("برجاء ملء جميع الحقول");
    try {
        const response = await fetch(`${SERVER_URL}/api/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        if (data.status === "success") {
            currentUser = data.user;
            localStorage.setItem("chat_user", JSON.stringify(currentUser));
            showChatScreen();
        } else { alert(data.message); }
    } catch (err) { alert("خطأ بالاتصال بالسيرفر"); }
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
    socket = io(SERVER_URL, { transports: ['websocket', 'polling'] });
    socket.on("connect", () => { socket.emit("join", { username: currentUser.username }); });
    
    socket.on("receive_message", (data) => {
        const sound = document.getElementById("notif-sound");
        if(sound) sound.play().catch(()=>{});
        if (activeChatUser && (data.sender_username === activeChatUser.username || data.receiver_username === activeChatUser.username)) {
            fetchActiveChatMessages();
        }
        loadActiveChatsFromServer();
    });

    socket.on("message_deleted", () => { if (activeChatUser) fetchActiveChatMessages(); });
    socket.on("display_typing", (data) => {
        if (activeChatUser && data.sender === activeChatUser.username) {
            document.getElementById("typing-status").innerText = data.typing ? "يكتب الآن..." : "";
        }
    });
}

function emitTyping() {
    if (!activeChatUser) return;
    socket.emit("typing", { sender: currentUser.username, receiver: activeChatUser.username, typing: true });
    clearTimeout(window.typingTimeout);
    window.typingTimeout = setTimeout(() => {
        socket.emit("typing", { sender: currentUser.username, receiver: activeChatUser.username, typing: false });
    }, 2000);
}

function openChat(username, avatarImg = "") {
    activeChatUser = { username: username };
    document.getElementById("app-sidebar").classList.add("hidden-mobile");
    document.getElementById("app-chat-area").classList.remove("hidden-mobile");
    document.getElementById("welcome-chat-view").classList.add("hidden");
    document.getElementById("active-chat-view").classList.remove("hidden");
    document.getElementById("active-chat-name").innerText = activeChatUser.username;
    
    const chatAvatarBox = document.getElementById("active-chat-avatar");
    if(avatarImg) chatAvatarBox.innerHTML = `<img src="${avatarImg}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
    else chatAvatarBox.innerHTML = `<i class="fas fa-user"></i>`;
    fetchActiveChatMessages();
}

function backToSidebar() {
    document.getElementById("app-sidebar").classList.remove("hidden-mobile");
    document.getElementById("app-chat-area").classList.add("hidden-mobile");
    activeChatUser = null;
}

async function loadActiveChatsFromServer() {
    try {
        const response = await fetch(`${SERVER_URL}/api/active-chats?username=${currentUser.username}`);
        const chats = await response.json();
        renderChatsList(chats);
    } catch (err) {}
}

function renderChatsList(serverChats = []) {
    const container = document.getElementById("chats-list-container");
    container.innerHTML = "";
    if (serverChats.length === 0) {
        container.innerHTML = `<div class="no-chats">لا توجد محادثات. ابحث عن صديق لبدء دردشة!</div>`;
        return;
    }
    serverChats.forEach(chat => {
        const isActive = activeChatUser && activeChatUser.username === chat.username ? "active" : "";
        const chatItem = document.createElement("div");
        chatItem.className = `chat-item ${isActive}`;
        
        chatItem.onclick = () => {
            const imgEl = chatItem.querySelector('.avatar-circle img');
            openChat(chat.username, imgEl ? imgEl.src : "");
        };
        
        chatItem.innerHTML = `<div class="avatar-circle" id="chat-ava-${chat.username}"><i class="fas fa-user"></i></div><div class="chat-item-info"><h4>${chat.username}</h4><p>${chat.last_message}</p></div>`;
        container.appendChild(chatItem);

        // جلب الصور بطريقة آمنة منفصلة بدون تجميد الكود
        fetch(`${SERVER_URL}/api/user-profile?username=${chat.username}`)
            .then(r => r.json())
            .then(d => {
                if(d.status === "success" && d.user.avatar) {
                    const avaBox = document.getElementById(`chat-ava-${chat.username}`);
                    if(avaBox) avaBox.innerHTML = `<img src="${d.user.avatar}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
                }
            }).catch(()=>{});
    });
}

async function handleSearch(event) {
    if (event.key !== "Enter") return;
    const username = document.getElementById("search-username").value.trim();
    if (!username || username === currentUser.username) return;
    try {
        const response = await fetch(`${SERVER_URL}/api/search?username=${username}`);
        const data = await response.json();
        if (data.status === "success") {
            document.getElementById("search-username").value = ""; 
            openChat(data.user.username, data.user.avatar);
        } else { alert(data.message); }
    } catch (err) { alert("خطأ أثناء البحث"); }
}

async function fetchActiveChatMessages() {
    if (!activeChatUser) return;
    try {
        const response = await fetch(`${SERVER_URL}/api/messages?sender=${currentUser.username}&receiver=${activeChatUser.username}`);
        const messages = await response.json();
        renderMessages(messages);
    } catch (err) {}
}

function renderMessages(messages = []) {
    const box = document.getElementById("messages-box");
    box.innerHTML = "";
    messages.forEach(msg => {
        const isMe = msg.sender_username === currentUser.username;
        const bubble = document.createElement("div");
        bubble.className = `msg-bubble ${isMe ? 'sent' : 'received'}`;
        bubble.innerText = msg.message;
        if (!msg.deleted_for_all && isMe) {
            bubble.style.cursor = "pointer";
            bubble.onclick = () => {
                if(confirm("هل تريد حذف هذه الرسالة لدى الجميع؟")) { triggerDeleteMessage(msg.id); }
            };
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
    const messageText = input.value.trim();
    if (!messageText || !activeChatUser) return;

