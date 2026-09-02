let currentSender = "";   
let currentReceiver = ""; 
let lastMessageCount = 0;

function loginOrRegister() {
    const name = document.getElementById("regName").value.trim();
    const phone = document.getElementById("regPhone").value.trim();

    if (name === "" || phone === "") {
        alert("من فضلك أدخل الاسم ورقم الهاتف أولاً!");
        return;
    }

    currentSender = phone;
    document.getElementById("userDisplay").textContent = `${name} (${phone})`;
    
    document.getElementById("loginScreen").style.display = "none";
    document.getElementById("chatScreen").style.display = "flex";
}

function sendMessage() {
    const input = document.getElementById("messageInput");
    const text = input.value.trim();

    if (text === "" || currentReceiver === "") {
        alert("من فضلك ابحث عن مستخدم أولاً لبدء الشات!");
        return;
    }

    fetch(`/send?sender=${currentSender}&receiver=${currentReceiver}&message=${encodeURIComponent(text)}`)
        .then(response => response.text())
        .then(() => {
            input.value = "";
            loadMessages();
        })
        .catch(() => {
            alert("فشل في إرسال الرسالة!");
        });
}

function searchUser() {
    const phone = document.getElementById("phoneSearch").value.trim();

    if (phone === "") {
        alert("من فضلك أدخل رقم هاتف للبحث!");
        return;
    }

    fetch("/search?phone=" + encodeURIComponent(phone))
        .then(response => response.text())
        .then(result => {
            alert(result);
            if (result.startsWith("Found:")) {
                currentReceiver = phone;
                loadMessages();
            }
        })
        .catch(() => {
            alert("حدث خطأ أثناء الاتصال بالسيرفر!");
        });
}

function loadMessages() {
    if (currentReceiver === "" || currentSender === "") return;

    fetch(`/get_messages?sender=${currentSender}&receiver=${currentReceiver}`)
        .then(response => response.json())
        .then(messages => {
            if (messages.length !== lastMessageCount) {
                const messagesContainer = document.getElementById("messages");
                messagesContainer.innerHTML = "";

                messages.forEach(msg => {
                    const messageDiv = document.createElement("div");
                    if (msg.sender === currentSender) {
                        messageDiv.className = "message sent";
                    } else {
                        messageDiv.className = "message received";
                    }
                    messageDiv.textContent = msg.message;
                    messagesContainer.appendChild(messageDiv);
                });

                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                lastMessageCount = messages.length;
            }
        });
}

setInterval(loadMessages, 2000);
