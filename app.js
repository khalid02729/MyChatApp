let myP='', myName='', myEmail='', targetP='', targetN='', targetE='', sync=null;

document.getElementById('to-r').addEventListener('click', ()=>{ document.getElementById('login-view').classList.add('hidden'); document.getElementById('register-view').classList.remove('hidden'); });
document.getElementById('to-l').addEventListener('click', ()=>{ document.getElementById('register-view').classList.add('hidden'); document.getElementById('login-view').classList.remove('hidden'); });

document.getElementById('b-login').addEventListener('click', async()=>{
    const p=document.getElementById('l-phone').value.trim(), o=document.getElementById('l-pass').value.trim(); 
    if(!p||!o) { alert('اكتب الرقم والباسورد!'); return; }
    const fd=new URLSearchParams(); fd.append('phone',p); fd.append('password',o);
    try {
        const res=await fetch('/login',{method:'POST',body:fd}); const txt=await res.text();
        if(res.status===200){ myP=p; myName=txt.split(':')[1] || p; myEmail=txt.split(':')[2] || '---'; enter(); } else { alert(txt); }
    } catch(e) { alert('خطأ في الاتصال بالسيرفر!'); }
});

document.getElementById('b-reg').addEventListener('click', async()=>{
    const n=document.getElementById('r-name').value.trim(), e=document.getElementById('r-email').value.trim(), p=document.getElementById('r-phone').value.trim(), o=document.getElementById('r-pass').value.trim(); 
    if(!n||!p||!o) { alert('املأ البيانات المطلوبة!'); return; }
    const fd=new URLSearchParams(); fd.append('name',n); fd.append('phone',p); fd.append('password',o); fd.append('email',e);
    try {
        const res=await fetch('/login',{method:'POST',body:fd}); const txt=await res.text();
        if(res.status===200){ myP=p; myName=n; myEmail=e||'---'; alert('تم حفظ حسابك وتأمينه!'); enter(); } else { alert(txt); }
    } catch(e) { alert('خطأ في الاتصال بالسيرفر!'); }
});

function enter(){ 
    document.getElementById('login-view').classList.add('hidden'); 
    document.getElementById('register-view').classList.add('hidden'); 
    document.getElementById('main-view').style.display='flex'; 
    document.getElementById('main-view').classList.remove('hidden'); 
    loadStatuses(); 
    setInterval(loadStatuses, 5000); 
}

document.getElementById('b-find').addEventListener('click', async()=>{
    const p=document.getElementById('f-phone').value.trim(); if(!p || p===myP) return;
    const res=await fetch('/search?phone='+p); const t=await res.text();
    if(t.startsWith('Found:')){ 
        targetP=p; targetN=t.split(':')[1]; targetE=t.split(':')[2] || '---'; 
        document.getElementById('h-title').innerText=targetN; 
        document.getElementById('top-pfp').innerText=targetN.charAt(0).toUpperCase(); 
        document.getElementById('m-input').disabled=false; 
        document.getElementById('b-send').disabled=false; 
        document.getElementById('b-clear-all').style.display='block'; 
        if(sync) clearInterval(sync); syncMsg(); sync=setInterval(syncMsg,2000); 
    } else { alert('هذا الرقم غير مسجل!'); }
});

document.getElementById('b-send').addEventListener('click', async()=>{
    const m=document.getElementById('m-input').value.trim(); if(!m||!targetP) return;
    await fetch('/send?sender='+myP+'&receiver='+targetP+'&message='+encodeURIComponent(m)); 
    document.getElementById('m-input').value=''; syncMsg();
});

async function syncMsg(){
    if(!targetP) return; const res=await fetch('/get_messages?sender='+myP+'&receiver='+targetP); const list=await res.json(); const box=document.getElementById('v-box'); box.innerHTML='';
    list.forEach(m=>{
        const d=document.createElement('div'); d.className='msg '+(m.sender===myP?'sent':'received'); d.innerText=m.message;
        d.addEventListener('contextmenu', async(e)=>{ e.preventDefault(); if(confirm('مسح الرسالة لدى الجميع؟')){ await fetch(`/delete_msg?id=${m.id}`); syncMsg(); }}); box.appendChild(d);
    }); box.scrollTop=box.scrollHeight;
}

document.getElementById('add-status').addEventListener('click', async()=>{ const txt = prompt('اكتب حالتك الجديدة الحين:'); if(!txt) return; await fetch(`/send_status?phone=${myP}&name=${encodeURIComponent(myName)}&text=${encodeURIComponent(txt)}`); loadStatuses(); });

async function loadStatuses() {
    const res = await fetch('/get_statuses'); const list = await res.json(); const sBox = document.getElementById('status-list'); sBox.innerHTML = '';
    list.forEach(s => {
        const div = document.createElement('div'); div.className = 'status-item'; div.innerHTML = `<div class="status-circle">${s.name.charAt(0).toUpperCase()}</div><span>${s.name}</span>`;
        div.addEventListener('click', () => { alert(`حالة ${s.name}:\n\n"${s.text}"`); }); sBox.appendChild(div);
    });
}

document.getElementById('header-profile-trigger').addEventListener('click', ()=>{ if(!targetP) return; document.getElementById('modal-name').innerText = targetN; document.getElementById('modal-phone').innerText = `الرقم: ${targetP}`; document.getElementById('modal-email').innerText = `البريد: ${targetE}`; document.getElementById('modal-pfp-img').innerText = targetN.charAt(0).toUpperCase(); document.getElementById('profile-modal').classList.remove('hidden'); });
document.getElementById('close-modal').addEventListener('click', ()=>{ document.getElementById('profile-modal').classList.add('hidden'); });
document.getElementById('b-clear-all').addEventListener('click', async()=>{ if(confirm('مسح الشات بالكامل؟')){ await fetch(`/clear_chat?sender=${myP}&receiver=${targetP}`); syncMsg(); }});
document.getElementById('b-out').addEventListener('click', ()=>{ location.reload(); });
