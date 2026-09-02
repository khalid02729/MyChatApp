// الرابط المباشر الصحيح والجاهز لسيرفرك أنت بنسبة 100%
const SERVER_URL = "https://mychatapp-production-b225.up.railway.app"; 
let socket = null; 

let currentUser = null;
let activeChatUser = null;
let activeChats = {}; 
let temporaryUsername = ""; 

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
    document.getElementById("otp-form").classList.add("hidden");
}

function cancelOTP() {
    document.getElementById("otp-form").classList.add("hidden");
    document.getElementById("login-form").classList.remove("hidden");
    document.getElementById("register-form").classList.add("hidden");
}

// ================= إدارة الحسابات =================

async function handleRegister(event) {
    if (event) event.preventDefault(); 
    const username = document.getElementById("reg-username").value.trim();
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-pass").value.trim();

    if (!username || !email || !password) return alert("برجاء ملء جميع الحقول");

    try {
        const response = await fetch(`${SERVER_URL}/api/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, password })
        });
        const data = await response.json();
        if (data.status === "success") {
            alert(data.message);
            temporaryUsername = username;
            document.getElementById("register-form").classList.add("hidden");
            document.getElementById("otp-form").classList.remove("hidden");
        } else {
            alert(data.message);
        }
    } catch (err) {
        alert("مشكلة في الاتصال بالسيرفر");
    }
}

async function handleVerifyOTP(event) {
    if (event) event.preventDefault();
    const otp = document.getElementById("otp-input").value.trim();

    try {
        const response = await fetch(`${SERVER_URL}/api/verify-otp`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: temporaryUsername, otp: otp })
        });
        const data = await response.json();
        if (data.status === "success") {
            alert(data.message);
            cancelOTP();
        } else {
            alert(data.message);
        }
    } catch (err) {
        alert("خطأ أثناء تفعيل الكود");
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
        } else if (data.status === "unverified") {
            alert(data.message);
            temporaryUsername = username;
            document.getElementById("login-form").classList.add("hidden");
            document.getElementById("otp-form").classList.remove("hidden");
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
        fetchActiveChatMessages();
        loadActiveChatsFromServer();
    }, 3000);
}

function initSocketConnection() {
    if (typeof io === 'undefined') return;
    try {
        socket = io(SERVER_URL, { 
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: Infinity,
            reconnectionDelay: 1000
        });
        socket.on("connect", () => {
            socket.emit("join", { username: currentUser.username });
        });
        socket.on("receive_message", (data) => {
            handleIncomingMessage(data);
        });
    } catch (e) {
        console.log("Socket waiting...");
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
        console.log("Error loading active chats summary");
    }
}

function logout() {
    localStorage.removeItem("chat_user");
    window.location.reload();
}

// ================= البحث والمحادثات =================

async function handleSearch(event) {
    if (event.key !== "Enter") return;
    const username = document.getElementById("search-username").value.trim();
    if (!username) return;
    if (username === currentUser.username) return alert("لا يمكنك محادثة نفسك!");

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
        alert("خطأ أثناء البحث عن الاسم");
    }
}

function renderChatsList(serverChats = []) {
    const container = document.getElementById("chats-list-container");
    container.innerHTML = "";

    const displayChats = serverChats.length > 0 ? serverChats : Object.keys(activeChats).map(k => ({username: k, last_message: "اضغط لبدء المحادثة..."}));

    if (displayChats.length === 0) {
        container.innerHTML = `<div class="no-chats">لا توجد محادثات حالية. ابحث عن اسم مستخدم لبدء دردشة!</div>`;
        return;
    }

    displayChats.forEach(chat => {
        const isActive = activeChatUser && activeChatUser.username === chat.username ? "active" : "";
        const chatItem = document.createElement("div");
        chatItem.className = `chat-item ${isActive}`;
        chatItem.onclick = () => openChat(chat.username);
        chatItem.innerHTML = `
            <div class="avatar-circle"><i class="fas fa-user"></i></div>
            <div class="chat-item-info">
                <h4>${chat.username}</h4>
                <p>${chat.last_message}</p>
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
    fetchActiveChatMessages();
    loadActiveChatsFromServer();
}

async function fetchActiveChatMessages() {
    if (!activeChatUser) return;
    try {
        const response = await fetch(`${SERVER_URL}/api/messages?sender=${currentUser.username}&receiver=${activeChatUser.username}`);
        const messages = await response.json();
        if (activeChats[activeChatUser.username]) {
            activeChats[activeChatUser.username].messages = messages;
        }
        renderMessages();
    } catch (err) {
        console.log("Error syncing history");
    }
}

// ================= إرسال الرسائل =================

function handleSendMessage(event) {
    if (event.key === "Enter") sendMessage();
}

async function sendMessage() {
    const input = document.getElementById("message-input");
    const messageText = input.value.trim();
    if (!messageText || !activeChatUser) return;

    const messageData = {
        sender_username: currentUser.username,
        receiver_username: activeChatUser.username,
        message: messageText
    };

    input.value = ""; 

    try {
        await fetch(`${SERVER_URL}/api/send`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(messageData)
        });
        fetchActiveChatMessages(); 
        loadActiveChatsFromServer();
    } catch (err) {
        if (socket && socket.connected) {
            socket.emit("send_message", messageData);
        }
    }
}

function handleIncomingMessage(data) {
    const partnerName = data.sender_username === currentUser.username ? data.receiver_username : data.sender_username;
    if (activeChatUser && activeChatUser.username === partnerName) {
        fetchActiveChatMessages();
    }
    loadActiveChatsFromServer();
}

function renderMessages() {
    const box = document.getElementById("messages-box");
    box.innerHTML = "";
    if (!activeChatUser || !activeChats[activeChatUser.username]) return;


