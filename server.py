// 🔌 لقط الرابط أونلاين تلقائيًا مهما تغير على Railway
const SERVER_URL = window.location.origin;
let socket = null;

let currentUser = null;
let activeChatUser = null;
let activeChats = {};

document.addEventListener("DOMContentLoaded", () => {
    const savedUser = localStorage.getItem("chat_user");
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        showChatScreen();
    }
});

function toggleAuthForms() {
    document.getElementById("login-form").classList.toggle("hidden");
    document.getElementById("register-form").classList.toggle("hidden");
}

// ==========================================
// 🔐 إدارة الحسابات (تسجيل ودخول) بنفس كودك القديم
// ==========================================
async function handleRegister(event) {
    if (event) event.preventDefault();
    const username = document.getElementById("reg-username").value.trim();
    const password = document.getElementById("reg-pass").value.trim();

    if (!username || !password) return alert("برجاء ملء جميع الحقول!");

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

    if (!username || !password) return alert("برجاء ملء جميع الحقول!");

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

// ==========================================
// 📱 تشغيل الشات والاتصالات بنفس كودك القديم
// ==========================================
function showChatScreen() {
    document.getElementById("auth-screen").classList.add("hidden");
    document.getElementById("chat-screen").classList.remove("hidden");
    document.getElementById("current-user-name").innerText = currentUser.username;

    initSocketConnection();
    loadActiveChatsFromServer();

    // التحديث التلقائي كل 3 ثواني للرسائل والقائمة والحالات
    setInterval(() => {
        fetchActiveChatMessages();
        loadActiveChatsFromServer();
        loadStoriesFromServer(); // ميزة الحالات الجديدة
    }, 3000);
}

function initSocketConnection() {
    if (typeof io === 'undefined') return;
    try {
        socket = io(SERVER_URL, { transports: ['websocket', 'polling'] });
        socket.on("connect", () => {
            socket.emit("join", { username: currentUser.username });
        });

        // لقطة الحذف الفوري لدى الجميع عبر السوكت لسرعة الشات
        socket.on("message_deleted_for_everyone", (data) => {
            if (activeChatUser && (activeChatUser.username == data.sender || activeChatUser.username == data.receiver)) {
                fetchActiveChatMessages();
            }
        });
    } catch (e) {
        console.log("Socket holding...");
    }
}

async function loadActiveChatsFromServer() {
    if (!currentUser) return;
    try {
        const response = await fetch(`${SERVER_URL}/api/active-chats?username=${currentUser.username}`);
        const chats = await response.json();
        chats.forEach(c => {
            if (!activeChats[c.username]) {
                activeChats[c.username] = { username: c.username, messages: [] };
            }
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

// ==========================================
// 🔎 البحث والمحادثات والرسائل بنفس أساميك
// ==========================================
async function handleSearch(event) {
    if (event.key !== "Enter") return;
    const username = document.getElementById("search-username").value.trim();
    if (!username || username === currentUser.username) return;

    try {
        const response = await fetch(`${SERVER_URL}/api/search?username=${username}`);
        const data = await response.json();
        if (data.status === "success") {
            const searchedUser = data.user;
            if (!activeChats[searchedUser.username]) {
                activeChats[searchedUser.username] = { username: searchedUser.username, messages: [] };
            }
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
        chatItem.innerHTML = `
            <div class="avatar-circle"><i class="fas fa-user"></i></div>
            <div class="chat-item-info">
                <h4>${chat.username}</h4>
                <p>${chat.last_message || ""}</p>
            </div>
        `;
        container.appendChild(chatItem);
    });
}

function openChat(username) {
    activeChatUser = { username: username };
    document.getElementById("welcome-chat-view").classList.add("hidden");
    document.getElementById("active-chat-view").classList.remove("hidden");
    document.getElementById("active-chat-name").innerText = activeChatUser.username;
    
    // 📱 دعم الموبايل حتة واحدة
    if (window.innerWidth <= 768) {
        document.querySelector('.chat-app-container').classList.add('active-chat-mobile');
    }
    
    fetchActiveChatMessages();
}

function backToSidebar() {
    document.querySelector('.chat-app-container').classList.remove('active-chat-mobile');
}

async function fetchActiveChatMessages() {
    if (!activeChatUser) return;
    try {
        const response = await fetch(`${SERVER_URL}/api/messages?sender=${currentUser.username}&receiver=${activeChatUser.username}`);
        const messages = await response.json();
        activeChats[activeChatUser.username].messages = messages;
        renderMessages();
    } catch (err) {
        console.log("Error loading messages");
    }
}

// 💬 رص الرسائل المطور المبني بالملي على صورتك الأخيرة الحقيقية
function renderMessages() {
    const box = document.getElementById("messages-box");
    box.innerHTML = "";
    if (!activeChatUser || !activeChats[activeChatUser.username]) return;

    const messages = activeChats[activeChatUser.username].messages;
    messages.forEach(msg => {
        // فحص "حذف لدي" محلياً قبل الرص عشان تختفي من شاشتك
        if (msg.deleted_for && msg.deleted_for.includes(currentUser.username)) return;

        // المتغير بتاعك القديم بالملي للحفاظ على اللوجيك
        const isMe = msg.sender_username === currentUser.username;
        const bubble = document.createElement("div");
        bubble.className = `msg-bubble ${isMe ? 'sent' : 'received'}`;
        
        // بناء محتوى الفقاعة مع الحفاظ على طريقتك وإضافة السهم وقائمة خيارات الحذف
        bubble.innerHTML = `
            <p class="message-text">${msg.message}</p>
            <span class="message-time">${msg.time || ""}</span>
            <div class="message-options" onclick="toggleMessageMenu(event, '${msg.id}')">
                <i class="fas fa-chevron-down"></i>
                <div id="menu-${msg.id}" class="options-menu hidden">
                    <button onclick="deleteMessage('${msg.id}', 'me')">حذف لدي</button>
                    ${isMe && msg.message !== "🚫 تم حذف هذه الرسالة" ? `<button onclick="deleteMessage('${msg.id}', 'everyone')">حذف لدى الجميع</button>` : ''}
                </div>
            </div>
        `;
        box.appendChild(bubble);
    });
    box.scrollTop = box.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById("message-input");
    const messageText = input.value.trim();
    if (!messageText || !activeChatUser) return;

    const messageData = {
        id: 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5), // توليد ID فريد للحذف لدى الجميع
        sender_username: currentUser.username,
        receiver_username: activeChatUser.username,
        message: messageText,
        time: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' })
    };
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

// ==========================================
// 😀 ميزة لوحة الإيموجي الجديدة


