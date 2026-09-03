

// 🔌 ربط السيرفر أونلاين برابط تطبيقك على Railway
const socket = io("https://mychatapp-production-b225.up.railway.app"); 

// 📁 المتغيرات العامة لحفظ حالة المستخدم والشات الحالي
let currentUser = "";
let activeChatPartner = "";

// ==========================================
// 🔐 1. واجهات الدخول والتسجيل (القديمة)
// ==========================================
function toggleAuthForms() {
    document.getElementById('login-form').classList.toggle('hidden');
    document.getElementById('register-form').classList.toggle('hidden');
}

function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById('login-username').value.trim();
    const pass = document.getElementById('login-pass').value;
    
    if(username && pass) {
        socket.emit('login_request', { username: username, password: pass });
    }
}

function handleRegister(event) {
    event.preventDefault();
    const username = document.getElementById('reg-username').value.trim();
    const pass = document.getElementById('reg-pass').value;
    
    if(username && pass) {
        socket.emit('register_request', { username: username, password: pass });
    }
}

// الاستماع لرد السيرفر بعد تسجيل الدخول الناجح
socket.on('login_success', (data) => {
    currentUser = data.username;
    document.getElementById('current-user-name').innerText = currentUser;
    
    // إخفاء شاشة الدخول وإظهار شاشة الواتساب المنظمة
    document.getElementById('auth-screen').classList.add('hidden');
    document.getElementById('chat-screen').classList.remove('hidden');
    
    // طلب قائمة المحادثات والحالات من السيرفر فوراً
    socket.emit('get_chats_and_stories', { username: currentUser });
});

socket.on('login_error', (msg) => { alert(msg); });
socket.on('register_success', () => { alert('تم تسجيل الحساب بنجاح! يمكنك الدخول الآن.'); toggleAuthForms(); });
socket.on('register_error', (msg) => { alert(msg); });

// ==========================================
// 🔎 2. ميزة البحث واختيار شخص لفتح الشات (حتة واحدة)
// ==========================================
function handleSearch(event) {
    if (event.key === 'Enter') {
        const searchName = document.getElementById('search-username').value.trim();
        if (searchName && searchName !== currentUser) {
            openChatWith(searchName);
            document.getElementById('search-username').value = ""; // تفريغ خانة البحث
        }
    }
}

function openChatWith(partnerName) {
    activeChatPartner = partnerName;
    
    document.getElementById('active-chat-name').innerText = partnerName;
    document.getElementById('welcome-chat-view').classList.add('hidden');
    document.getElementById('active-chat-view').classList.remove('hidden');
    
    // 📱 دعم الموبايل: لو الشاشة صغيرة، نخفي الجنب ونملأ الشاشة بالشات
    if (window.innerWidth <= 768) {
        document.querySelector('.chat-app-container').classList.add('active-chat-mobile');
    }
    
    document.getElementById('messages-box').innerHTML = ""; // تفريغ القديم
    socket.emit('load_chat_history', { user: currentUser, partner: activeChatPartner });
}

function backToSidebar() {
    document.querySelector('.chat-app-container').classList.remove('active-chat-mobile');
}

// ==========================================
// 💬 3. ميزة إرسال واستقبال الرسائل والـ Layout
// ==========================================
function handleSendMessage(event) {
    if (event.key === 'Enter') { sendMessage(); }
}

function sendMessage() {
    const input = document.getElementById('message-input');
    const text = input.value.trim();
    
    if (text && activeChatPartner) {
        const msgData = {
            id: 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5), // توليد ID فريد للرسالة للحذف
            sender: currentUser,
            receiver: activeChatPartner,
            message: text,
            time: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' })
        };
        
        appendMessageBubble(msgData, 'sent'); // عرضها عندك يمين
        socket.emit('new_private_message', msgData); // إرسالها للسيرفر فوراً
        input.value = ""; // تفريغ الحقل
    }
}

// استقبال الرسائل في الوقت الحقيقي
socket.on('receive_private_message', (msgData) => {
    if (msgData.sender === activeChatPartner) {
        appendMessageBubble(msgData, 'received'); // عرضها شمال
    }
});

// بناء فقاعة الرسالة وسهم الحذف الذكي
function appendMessageBubble(msg, type) {
    const box = document.getElementById('messages-box');
    const bubble = document.createElement('div');
    bubble.className = `msg-bubble ${type}`;
    bubble.id = msg.id; 
    
    bubble.innerHTML = `
        <p class="message-text">${msg.message}</p>
        <span class="message-time">${msg.time}</span>
        <!-- سهم الخيارات الذكي للحذف يظهر عند الـ Hover -->
        <div class="message-options" onclick="toggleMessageMenu(event, '${msg.id}')">
            <i class="fas fa-chevron-down"></i>
            <div id="menu-${msg.id}" class="options-menu hidden">
                <button onclick="deleteMessage('${msg.id}', 'me')">حذف لدي</button>
                ${type === 'sent' ? `<button onclick="deleteMessage('${msg.id}', 'everyone')">حذف لدى الجميع</button>` : ''}
            </div>
        </div>
    `;
    
    box.appendChild(bubble);
    box.scrollTop = box.scrollHeight; // سحب الشات لأسفل تلقائياً
}

// ==========================================
// 😀 4. لوحة الإيموجي السحرية
// ==========================================
function toggleEmojiPicker() {
    document.getElementById('emoji-picker').classList.toggle('hidden');
}

function appendEmoji(emoji) {
    const input = document.getElementById('message-input');
    input.value += emoji; 
    input.focus(); 
    document.getElementById('emoji-picker').classList.add('hidden'); 
}

// ==========================================
// 🗑️ 5. منطق ميزات حذف الرسائل (لدي ولدى الجميع)
// ==========================================
function toggleMessageMenu(event, msgId) {
    event.stopPropagation(); 
    document.querySelectorAll('.options-menu').forEach(menu => {
        if(menu.id !== `menu-${msgId}`) menu.classList.add('hidden');
    });
    document.getElementById(`menu-${msgId}`).classList.toggle('hidden');
}

document.addEventListener('click', () => {
    document.querySelectorAll('.options-menu').forEach(menu => menu.classList.add('hidden'));
});

function deleteMessage(msgId, deleteType) {
    if (deleteType === 'me') {
        const bubble = document.getElementById(msgId);
        if (bubble) bubble.remove(); // تختفي من شاشتك فوراً
        socket.emit('delete_message_for_me', { msg_id: msgId, user: currentUser });
    } 
    else if (deleteType === 'everyone') {
        socket.emit('delete_message_for_everyone', { msg_id: msgId, sender: currentUser, receiver: activeChatPartner });
    }
}

// استقبال أمر الحذف لدى الجميع من السيرفر في الوقت الحقيقي
socket.on('message_deleted_for_everyone', (data) => {
    const bubble = document.getElementById(data.msg_id);
    if (bubble) {
        bubble.querySelector('.message-text').innerText = "🚫 تم حذف هذه الرسالة";
        bubble.querySelector('.message-text').style.fontStyle = "italic";
        bubble.querySelector('.message-text').style.color = "#8696a0";
        const options = bubble.querySelector('.message-options');
        if (options) options.remove(); // حذف سهم التحكم تماماً
    }
});

// ==========================================
// 🌟 6. ميزة الحالات (الستوري) وتحديث القائمة الجانبية
// ==========================================
function addNewStory() {
    const storyText = prompt("اكتب حالتك النصية الجديدة:");
    if(storyText) {
        socket.emit('post_new_story', { username: currentUser, content: storyText });
    }
}

// استقبال وتحديث الحالات وقائمة المحادثات من السيرفر
socket.on('update_chats_and_stories_view', (data) => {
    const chatsContainer = document.getElementById('chats-list-container');
    chatsContainer.innerHTML = "";
    
    if(data.chats.length === 0) {
        chatsContainer.innerHTML = `<div class="no-chats">لا توجد محادثات نشطة حالياً. ابحث عن صديق لبدء الشات!</div>`;
    } else {
        data.chats.forEach(chat => {
            const item = document.createElement('div');
            item.className = `chat-item ${chat.name === activeChatPartner ? 'active' : ''}`;
            item.onclick = () => openChatWith(chat.name);
            item.innerHTML = `
                <div class="avatar-circle"><i class="fas fa-user"></i></div>
                <div class="chat-item-info">
                    <h4>${chat.name}</h4>
                    <p>${chat.lastMessage}</p>
                </div>
            `;
            chatsContainer.appendChild(item);
        });
    }
});

function logout() { window.location.reload(); }
