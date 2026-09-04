const SERVER_URL = "https://railway.app"; 
let socket = null; 

let currentUser = null;
let activeChatUser = null;
let activeChats = {}; 

// تم ربط الفورم برمجياً هنا لضمان عمل الأزرار داخل الموبايل بدون مشاكل وتجميد
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

function toggleAuthForms() {
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    if (loginForm && registerForm) {
        loginForm.classList.toggle("hidden");
        registerForm.classList.toggle("hidden");
    }
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
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        if (data.status === "success") {
            alert(data.message);
            toggleAuthForms();
        } else {
            alert(data.message);
        }
    } catch (err) {
        alert("مشكلة في الاتصال بالسيرفر");
    }
}

async function handleLogin(event) {
    if (event) event.preventDefault(); 
    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-pass").value.trim();

    if (!username || !password) return alert("برجاء ملء الحقول");

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
        } else {
            alert(data.message);
        }
    } catch (err) {
        alert("خطأ في الاتصال بالشبكة");
    }
}

function showChatScreen() {
    document.getElementById("auth-screen").classList.add("hidden");
    document.getElementById("chat-screen").classList.remove("hidden");
    document.getElementById("current-user-name").innerText = currentUser.username;
    
    initSocketConnection();
    loadActiveChatsFromServer();
    
    setInterval(() => {
        if (currentUser) loadActiveChatsFromServer();
    }, 4000);
}

function initSocketConnection() {
    if (typeof io === 'undefined') return;
    try {
        socket = io(SERVER_URL, { transports: ['websocket', 'polling'] });
        socket.on("connect", () => {
            socket.emit("join", { username: currentUser.username });
        });

        // استقبال الرسائل الفورية فوراً عبر الـ Socket دون تأخير
        socket.on("receive_message", (data) => {
            if (activeChatUser && (data.sender_username === activeChatUser.username || data.receiver_username === activeChatUser.username)) {
                fetchActiveChatMessages();
            }
            loadActiveChatsFromServer();
        });
    } catch (e) {
        console.log("Socket connection waiting...");
    }
}

async function loadActiveChatsFromServer() {
    if (!currentUser) return;
    try {
        const response = await fetch(`${SERVER_URL}/api/active-chats?username=${currentUser.username}`);
        const chats = await response.json();
        chats.forEach(c => {
            if (!activeChats[c.username]) activeChats[c.username] = { username: c.username, messages: [] };
        });
        renderChatsList(chats);
    } catch (err) {
        console.log("Sync error");
    }
}

function logout() {
    localStorage.removeItem("chat_user");
    window.location.reload();
}

async function handleSearch(event) {
    if (event.key !== "Enter") return;
    const username = document.getElementById("search-username").value.trim();
    if (!username || username === currentUser.username) return;

    try {
        const response = await fetch(`${SERVER_URL}/api/search?username=${username}`);
        const data = await response.json();
        if (data.status === "success") {
            const searchedUser = data.user;
            if (!activeChats[searchedUser.username]) activeChats[searchedUser.username] = { username: searchedUser.username, messages: [] };
            document.getElementById("search-username").value = ""; 
            openChat(searchedUser.username);
        } else {
            alert(data.message);
        }
    } catch (err) {
        alert("خطأ أثناء البحث");
    }
}

function renderChatsList(serverChats = []) {
    const container = document.getElementById("chats-list-container");
    container.innerHTML = "";
    if (serverChats.length === 0) {
        container.innerHTML = `<div class="no-chats">لا توجد محادثات. ابحث عن اسم مستخدم لبدء دردشة!</div>`;
        return;
    }
    serverChats.forEach(chat => {
        const isActive = activeChatUser && activeChatUser.username === chat.username ? "active" : "";
        const chatItem = document.createElement("div");
        chatItem.className = `chat-item ${isActive}`;
        chatItem.onclick = () => openChat(chat.username);
        chatItem.innerHTML = `<div class="avatar-circle"><i class="fas fa-user"></i></div><div class="chat-item-info"><h4>${chat.username}</h4><p>${chat.last_message}</p></div>`;
        container.appendChild(chatItem);
    });
}

function openChat(username) {
    activeChatUser = { username: username };
    document.getElementById("welcome-chat-view").classList.add("hidden");
    document.getElementById("active-chat-view").classList.remove("hidden");
    document.getElementById("active-chat-name").innerText = activeChatUser.username;
    fetchActiveChatMessages();
}

async function fetchActiveChatMessages() {
    if (!activeChatUser) return;
    try {
        const response = await fetch(`${SERVER_URL}/api/messages?sender=${currentUser.username}&receiver=${activeChatUser.username}`);
        const messages = await response.json();
        if (activeChats[activeChatUser.username]) activeChats[activeChatUser.username].messages = messages;
        renderMessages();
    } catch (err) {}
}

async function sendMessage() {
    const input = document.getElementById("message-input");
    const messageText = input.value.trim();
    if (!messageText || !activeChatUser) return;

    const messageData = { sender_username: currentUser.username, receiver_username: activeChatUser.username, message: messageText };
    input.value = ""; 

    try {
        await fetch(`${SERVER_URL}/api/send`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(messageData)
        });
        fetchActiveChatMessages(); 
    } catch (err) {}
}

function handleSendMessage(event) {
    if (event.key === "Enter") sendMessage();
}

function renderMessages() {
    const box = document.getElementById("messages-box");
    box.innerHTML = "";
    if (!activeChatUser || !activeChats[activeChatUser.username]) return;

    const messages = activeChats[activeChatUser.username].messages;
    messages.forEach(msg => {
        const isMe = msg.sender_username === currentUser.username;
        const bubble = document.createElement("div");
        bubble.className = `msg-bubble ${isMe ? 'sent' : 'received'}`;
        bubble.innerText = msg.message;
        box.appendChild(bubble);
    });
    box.scrollTop = box.scrollHeight;
}

