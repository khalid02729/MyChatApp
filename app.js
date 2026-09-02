// الربط التلقائي بالسيرفر المرفوع مع الواجهة في نفس مشروع Railway
const SERVER_URL = window.location.origin; 
const socket = io(SERVER_URL);

let currentUser = null;
let activeChatUser = null;
let activeChats = {}; 

// عند تحميل الصفحة، التأكد من حالة تسجيل الدخول السابقة
document.addEventListener("DOMContentLoaded", () => {
    const savedUser = localStorage.getItem("chat_user");
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        showChatScreen();
    }
});

// التنقل السلس بين شاشتي تسجيل الدخول والتسجيل
function toggleAuthForms() {
    document.getElementById("login-form").classList.toggle("hidden");
    document.getElementById("register-form").classList.toggle("hidden");
}

// ================= إدارة الحسابات =================

async function handleRegister(event) {
    if (event) event.preventDefault(); // منع الصفحة من إعادة التحميل والتعليق

    const username = document.getElementById("reg-name").value.trim();
    const phone = document.getElementById("reg-phone").value.trim();
    const password = document.getElementById("reg-pass").value.trim();

    if (!username || !phone || !password) return alert("برجاء ملء جميع الحقول");

    const response = await fetch(`${SERVER_URL}/api/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, phone, password })
    });
    
    const data = await response.json();
    if (data.status === "success") {
        alert("تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.");
        toggleAuthForms();
    } else {
        alert(data.message);
    }
}

async function handleLogin(event) {
    if (event) event.preventDefault(); // منع الصفحة من إعادة التحميل والتعليق

    const phone = document.getElementById("login-phone").value.trim();
    const password = document.getElementById("login-pass").value.trim();

    if (!phone || !password) return alert("برجاء ملء الحقول");

    const response = await fetch(`${SERVER_URL}/api/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone, password })
    });

    const data = await response.json();
    if (data.status === "success") {
        currentUser = data.user;
        localStorage.setItem("chat_user", JSON.stringify(currentUser));
        showChatScreen();
    } else {
        alert(data.message);
    }
}

function showChatScreen() {
    document.getElementById("auth-screen").classList.add("hidden");
    document.getElementById("chat-screen").classList.remove("hidden");
    document.getElementById("current-user-name").innerText = currentUser.username;

    // الانضمام لغرفة استقبال الرسائل عبر الـ Socket
    socket.emit("join", { phone: currentUser.phone });
}

function logout() {
    localStorage.removeItem("chat_user");
    window.location.reload();
}

// ================= البحث وبدء محادثة جديدة =================

async function handleSearch(event) {
    if (event.key !== "Enter") return;
    
    const phone = document.getElementById("search-phone").value.trim();
    if (!phone) return;
    if (phone === currentUser.phone) return alert("لا يمكنك محادثة نفسك!");

    const response = await fetch(`${SERVER_URL}/api/search?phone=${phone}`);
    const data = await response.json();

    if (data.status === "success") {
        const searchedUser = data.user;
        if (!activeChats[searchedUser.phone]) {
            activeChats[searchedUser.phone] = { username: searchedUser.username, messages: [] };
        }
        renderChatsList();
        openChat(searchedUser.phone);
        document.getElementById("search-phone").value = ""; 
    } else {
        alert(data.message);
    }
}

function renderChatsList() {
    const container = document.getElementById("chats-list-container");
    container.innerHTML = "";

    const keys = Object.keys(activeChats);
    if (keys.length === 0) {
        container.innerHTML = `<div class="no-chats">لا توجد محادثات حالية. ابحث عن رقم لبدء دردشة!</div>`;
        return;
    }

    keys.forEach(phone => {
        const chat = activeChats[phone];
        const lastMsg = chat.messages.length > 0 ? chat.messages[chat.messages.length - 1].message : "اضغط لبدء المحادثة...";
        const isActive = activeChatUser && activeChatUser.phone === phone ? "active" : "";

        const chatItem = document.createElement("div");
        chatItem.className = `chat-item ${isActive}`;
        chatItem.onclick = () => openChat(phone);
        chatItem.innerHTML = `
            <div class="avatar"><i class="fas fa-user"></i></div>
            <div class="chat-item-info">
                <h4>${chat.username}</h4>
                <p>${lastMsg}</p>
            </div>
        `;
        container.appendChild(chatItem);
    });
}

function openChat(phone) {
    activeChatUser = { phone: phone, username: activeChats[phone].username };
    
    document.getElementById("welcome-chat-view").classList.add("hidden");
    document.getElementById("active-chat-view").classList.remove("hidden");
    document.getElementById("active-chat-name").innerText = activeChatUser.username;
    
    renderMessages();
    renderChatsList(); 
}

// ================= إرسال واستقبال الرسائل =================

function handleSendMessage(event) {
    if (event.key === "Enter") sendMessage();
}

function sendMessage() {
    const input = document.getElementById("message-input");
    const messageText = input.value.trim();
    if (!messageText || !activeChatUser) return;

    const messageData = {
        sender_phone: currentUser.phone,
        receiver_phone: activeChatUser.phone,
        message: messageText
    };

    socket.emit("send_message", messageData);
    input.value = ""; 
}

socket.on("receive_message", (data) => {
    const partnerPhone = data.sender_phone === currentUser.phone ? data.receiver_phone : data.sender_phone;
    const partnerName = data.sender_phone === currentUser.phone ? activeChatUser.username : "مستخدم"; 

    if (!activeChats[partnerPhone]) {
        activeChats[partnerPhone] = { username: partnerName, messages: [] };
    }

    activeChats[partnerPhone].messages.push(data);

    if (activeChatUser && activeChatUser.phone === partnerPhone) {
        renderMessages();
    }

    renderChatsList();
});

function renderMessages() {
    const box = document.getElementById("messages-box");
    box.innerHTML = "";

    if (!activeChatUser || !activeChats[activeChatUser.phone]) return;

    const messages = activeChats[activeChatUser.phone].messages;
    messages.forEach(msg => {
        const isSent = msg.sender_phone === currentUser.phone;
        const bubble = document.createElement("div");
        bubble.className = `msg-bubble ${isSent ? 'sent' : 'received'}`;
        bubble.innerText = msg.message;
        box.appendChild(bubble);
    });

    box.scrollTop = box.scrollHeight;
}
