// الرابط المباشر الصحيح والجاهز لسيرفرك أنت بنسبة 100%
const SERVER_URL = "https://mychatapp-production-b225.up.railway.app"; 
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

// ================= إدارة الحسابات =================

async function handleRegister(event) {
    if (event) event.preventDefault(); 
    const username = document.getElementById("reg-name").value.trim();
    const phone = document.getElementById("reg-phone").value.trim();
    const password = document.getElementById("reg-pass").value.trim();

    if (!username || !phone || !password) return alert("برجاء ملء جميع الحقول");

    try {
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
    } catch (err) {
        alert("مشكلة في الاتصال بالسيرفر");
    }
}

async function handleLogin(event) {
    if (event) event.preventDefault(); 
    const phone = document.getElementById("login-phone").value.trim();
    const password = document.getElementById("login-pass").value.trim();

    if (!phone || !password) return alert("برجاء ملء الحقول");

    try {
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
    } catch (err) {
        alert("خطأ في الاتصال بالشبكة");
    }
}

function showChatScreen() {
    document.getElementById("auth-screen").classList.add("hidden");
    document.getElementById("chat-screen").classList.remove("hidden");
    document.getElementById("current-user-name").innerText = currentUser.username;
    setTimeout(initSocketConnection, 1000);
    
    // تشغيل جلب تلقائي للرسائل كل 3 ثواني كدعم إضافي لضمان وصول الرسايل للطرفين فوراً
    setInterval(fetchActiveChatMessages, 3000);
}

function initSocketConnection() {
    if (typeof io === 'undefined') return;
    try {
        socket = io(SERVER_URL, { transports: ['polling', 'websocket'] });
        socket.on("connect", () => {
            socket.emit("join", { phone: currentUser.phone });
        });
        socket.on("receive_message", (data) => {
            handleIncomingMessage(data);
        });
    } catch (e) {
        console.log("Socket connection backup waiting...");
    }
}

function logout() {
    localStorage.removeItem("chat_user");
    window.location.reload();
}

// ================= البحث والمحادثات =================

async function handleSearch(event) {
    if (event.key !== "Enter") return;
    const phone = document.getElementById("search-phone").value.trim();
    if (!phone) return;
    if (phone === currentUser.phone) return alert("لا يمكنك محادثة نفسك!");

    try {
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
    } catch (err) {
        alert("خطأ أثناء البحث");
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
        chatItem.innerHTML = `<div class="chat-item-info"><h4>${chat.username}</h4><p>${lastMsg}</p></div>`;
        container.appendChild(chatItem);
    });
}

function openChat(phone) {
    activeChatUser = { phone: phone, username: activeChats[phone].username };
    document.getElementById("welcome-chat-view").classList.add("hidden");
    document.getElementById("active-chat-view").classList.remove("hidden");
    document.getElementById("active-chat-name").innerText = activeChatUser.username;
    fetchActiveChatMessages();
}

// جلب وتحديث الرسائل من السيرفر بشكل مضمون للطرفين
async function fetchActiveChatMessages() {
    if (!activeChatUser) return;
    try {
        const response = await fetch(`${SERVER_URL}/api/messages?sender=${currentUser.phone}&receiver=${activeChatUser.phone}`);
        const messages = await response.json();
        activeChats[activeChatUser.phone].messages = messages;
        renderMessages();
    } catch (err) {
        console.log("Error syncing messages...");
    }
}

// ================= إرسال وعرض الرسائل =================

function handleSendMessage(event) {
    if (event.key === "Enter") sendMessage();
}

async function sendMessage() {
    const input = document.getElementById("message-input");
    const messageText = input.value.trim();
    if (!messageText || !activeChatUser) return;

    const messageData = {
        sender_phone: currentUser.phone,
        receiver_phone: activeChatUser.phone,
        message: messageText
    };

    input.value = ""; 

    try {
        // إرسال للسيرفر عبر الـ API لضمان الحفظ الفوري وقرأتها عند الطرفين
        await fetch(`${SERVER_URL}/api/send`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(messageData)
        });
        fetchActiveChatMessages(); // تحديث الشاشة فوراً بعد الإرسال
    } catch (err) {
        alert("فشل إرسال الرسالة");
    }
}

function handleIncomingMessage(data) {
    const partnerPhone = data.sender_phone === currentUser.phone ? data.receiver_phone : data.sender_phone;
    if (activeChatUser && activeChatUser.phone === partnerPhone) {
        fetchActiveChatMessages();
    }
}

function renderMessages() {
    const box = document.getElementById("messages-box");
    box.innerHTML = "";
    if (!activeChatUser || !activeChats[activeChatUser.phone]) return;

    const messages = activeChats[activeChatUser.phone].messages;
    messages.forEach(msg => {
        const isMe = msg.sender_phone === currentUser.phone;
        const bubble = document.createElement("div");
        
        // تفريق الاتجاهات والألوان
        bubble.className = `msg-bubble ${isMe ? 'sent' : 'received'}`;
        bubble.innerText = msg.message;
        box.appendChild(bubble);
    });
    box.scrollTop = box.scrollHeight;
}

