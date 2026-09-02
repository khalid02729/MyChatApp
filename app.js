
const SERVER_URL = 'https://railway.app';

let currentUserPhone = '';
let currentUserName = '';
let activeChatReceiver = '';
let chatInterval = null;

// زر الدخول والتسجيل
document.getElementById('login-btn').addEventListener('click', async () => {
    const name = document.getElementById('login-name').value.trim();
    const phone = document.getElementById('login-phone').value.trim();
    const password = document.getElementById('login-pass').value.trim();

    if (!phone || !password) {
        alert('من فضلك اكتب رقم الموبايل وكلمة السر لتأمين حسابك!');
        return;
    }

    const formData = new URLSearchParams();
    formData.append('name', name);
    formData.append('phone', phone);
    formData.append('password', password);

    try {
        const response = await fetch(`${SERVER_URL}/login`, {
            method: 'POST',
            body: formData
        });

        const result = await response.text();

        if (response.status === 200) {
            currentUserPhone = phone;
            currentUserName = name || phone;
            
            document.getElementById('current-user-display').innerText = `المستخدم: ${currentUserName}`;
            document.getElementById('login-screen').style.display = 'none';
            document.getElementById('chat-screen').style.display = 'flex';
        } else if (response.status === 401) {
            alert('كلمة السر خاطئة! هذا الرقم محمي ومسجل لشخص آخر.');
        } else {
            alert('خطأ في البيانات أو الرقم مسجل مسبقاً، يرجى كتابة البasورد الصحيحة.');
        }
    } catch (error) {
        alert('فشل الاتصال بالسيرفر السحابي، تأكد أن السيرفر يعمل في موقع Railway!');
    }
});

// زر البحث عن صديق وبدء التمكين
document.getElementById('search-btn').addEventListener('click', async () => {
    const phone = document.getElementById('search-phone').value.trim();
    if (!phone) return;

    if (phone === currentUserPhone) {
        alert('لا يمكنك الشات مع نفسك!');
        return;
    }

    try {
        const response = await fetch(`${SERVER_URL}/search?phone=${phone}`);
        const result = await response.text();

        if (result.startsWith('Found:')) {
            activeChatReceiver = phone;
            const friendName = result.replace('Found:', '').trim();
            document.querySelector('.identity-text h3').innerText = `المحادثة مع: ${friendName}`;
            document.getElementById('chat-box').innerHTML = ''; 
            
            // تمكين أزرار الكتابة والإرسال بعد العثور على الصديق
            document.getElementById('message-input').disabled = false;
            document.getElementById('send-btn').disabled = false;
            document.getElementById('message-input').focus();
            
            if (chatInterval) clearInterval(chatInterval);
            fetchMessages();
            chatInterval = setInterval(fetchMessages, 2000);
        } else {
            alert('هذا الرقم غير مسجل في خالد شات حتى الآن!');
        }
    } catch (error) {
        alert('حدث خطأ أثناء البحث!');
    }
});

// زر إرسال الرسالة
document.getElementById('send-btn').addEventListener('click', async () => {
    const msg = document.getElementById('message-input').value.trim();
    if (!msg || !activeChatReceiver) return;

    try {
        await fetch(`${SERVER_URL}/send?sender=${currentUserPhone}&receiver=${activeChatReceiver}&message=${encodeURIComponent(msg)}`);
        document.getElementById('message-input').value = '';
        fetchMessages();
    } catch (error) {
        console.error('فشل إرسال الرسالة');
    }
});

// دعم الإرسال عن طريق زر الإنتر في الكيبورد
document.getElementById('message-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('send-btn').click();
    }
});

// دالة جلب الرسائل وعرضها بفقاعات شيك
async function fetchMessages() {
    if (!activeChatReceiver) return;
    try {
        const response = await fetch(`${SERVER_URL}/get_messages?sender=${currentUserPhone}&receiver=${activeChatReceiver}`);
        const messages = await response.json();
        
        const chatBox = document.getElementById('chat-box');
        chatBox.innerHTML = '';

        if(messages.length === 0) {
            chatBox.innerHTML = '<div class="empty-state"><h4>لا توجد رسائل بينكم بعد</h4><p>اكتب رسالة بالأسفل لبدء الكلام الحين.</p></div>';
            return;
        }

        messages.forEach(m => {
            const msgDiv = document.createElement('div');
            msgDiv.classList.add('message');
            if (m.sender === currentUserPhone) {
                msgDiv.classList.add('sent');
            } else {
                msgDiv.classList.add('received');
            }
            msgDiv.innerText = m.message;
            chatBox.appendChild(msgDiv);
        });
        chatBox.scrollTop = chatBox.scrollHeight;
    } catch (error) {
        console.error('خطأ في جلب الرسائل');
    }
}

// زر تسجيل الخروج
document.getElementById('logout-btn').addEventListener('click', () => {
    location.reload();
});
