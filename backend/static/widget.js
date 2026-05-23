(function(){
var d=document,sc=d.currentScript,tenant=sc.getAttribute('data-tenant')||'demo',lang=sc.getAttribute('data-lang')||'zh',base=sc.src.replace(/\/chat-widget\.js.*/,'');
var vid=localStorage.getItem('scs_vid')||'v'+Math.random().toString(36).substr(2,8);
localStorage.setItem('scs_vid',vid);
var T={zh:{hello:'你好！有什么可以帮您？',send:'发送',placeholder:'输入消息...',error:'网络错误，请重试',sorry:'抱歉，请重试'},en:{hello:'Hello! How can I help you?',send:'Send',placeholder:'Type a message...',error:'Network error, please try again',sorry:'Sorry, please try again.'}};
var t=T[lang]||T.zh;
var style=d.createElement('style');
style.textContent=[
'.scs-w{position:fixed;bottom:24px;right:24px;z-index:9999;font-family:Inter,system-ui,sans-serif}',
'.scs-btn{width:56px;height:56px;background:#6750A4;color:#fff;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;border-radius:16px;transition:all .2s cubic-bezier(.2,0,0,1);box-shadow:0 4px 16px rgba(103,80,164,.3)}',
'.scs-btn:hover{background:#21005D;box-shadow:0 6px 24px rgba(103,80,164,.4);transform:translateY(-1px)}',
'.scs-panel{display:none;position:fixed;bottom:96px;right:24px;width:400px;max-width:calc(100vw - 32px);height:560px;max-height:calc(100vh - 120px);background:#FFFBFE;border:1px solid #CAC4D0;border-radius:20px;flex-direction:column;overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,.12)}',
'.scs-panel.open{display:flex}',
'.scs-hdr{background:linear-gradient(135deg,#6750A4,#21005D);color:#fff;padding:20px 24px;display:flex;justify-content:space-between;align-items:center}',
'.scs-hdr h4{margin:0;font-size:15px;font-weight:600;letter-spacing:.02em;display:flex;align-items:center;gap:8px}',
'.scs-hdr h4 svg{width:20px;height:20px}',
'.scs-hdr button{background:rgba(255,255,255,.12);border:none;color:rgba(255,255,255,.7);cursor:pointer;font-size:18px;line-height:1;width:28px;height:28px;border-radius:14px;display:flex;align-items:center;justify-content:center;transition:all .2s}',
'.scs-hdr button:hover{background:rgba(255,255,255,.2);color:#fff}',
'.scs-body{flex:1;padding:20px;overflow-y:auto;display:flex;flex-direction:column;gap:12px;background:#F7F2FA}',
'.scs-msg{max-width:80%;padding:12px 16px;font-size:14px;line-height:1.6;border-radius:16px}',
'.scs-msg.visitor{align-self:flex-end;background:#6750A4;color:#fff;border-bottom-right-radius:4px}',
'.scs-msg.bot{align-self:flex-start;background:#fff;color:#1C1B1F;border:1px solid #CAC4D0;border-bottom-left-radius:4px}',
'.scs-msg .t{font-size:11px;opacity:.5;margin-top:4px;display:block}',
'.scs-typing{align-self:flex-start;background:#fff;color:#49454F;border:1px solid #CAC4D0;padding:12px 16px;border-radius:16px;border-bottom-left-radius:4px;font-size:14px}',
'.scs-typing span{display:inline-block;animation:scsBounce 1.4s infinite both}',
'.scs-typing span:nth-child(2){animation-delay:.2s}',
'.scs-typing span:nth-child(3){animation-delay:.4s}',
'@keyframes scsBounce{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-4px)}}',
'.scs-ft{padding:16px 20px;border-top:1px solid #CAC4D0;display:flex;gap:10px;background:#FFFBFE}',
'.scs-ft input{flex:1;padding:12px 16px;border:1px solid #CAC4D0;font-size:14px;outline:none;border-radius:12px;font-family:inherit;transition:border-color .2s}',
'.scs-ft input:focus{border-color:#6750A4;box-shadow:0 0 0 2px rgba(103,80,164,.12)}',
'.scs-ft input::placeholder{color:#79747E}',
'.scs-ft button{padding:12px 20px;background:#6750A4;color:#fff;border:none;font-size:13px;font-weight:500;cursor:pointer;white-space:nowrap;border-radius:12px;transition:all .2s}',
'.scs-ft button:hover{background:#21005D}',
'@media(max-width:480px){.scs-panel{bottom:0;right:0;width:100%;height:100%;max-width:100%;max-height:100%;border-radius:0}.scs-btn{bottom:16px;right:16px}}'
].join('');
d.head.appendChild(style);
var wrap=d.createElement('div');wrap.className='scs-w';
wrap.innerHTML='<button class="scs-btn" id="scsBtn"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 5h18v12H12L7 21v-4H3V5z"/><line x1="8" y1="10" x2="16" y2="10"/><line x1="8" y1="13" x2="13" y2="13"/></svg></button>';
var panel=d.createElement('div');panel.className='scs-panel';
var initTime=new Date(),ih=(initTime.getHours()<10?'0':'')+initTime.getHours()+':'+(initTime.getMinutes()<10?'0':'')+initTime.getMinutes();
panel.innerHTML='<div class="scs-hdr"><h4><svg viewBox="0 0 20 20" fill="none"><rect width="20" height="20" rx="6" fill="rgba(255,255,255,.2)"/><path d="M6 10l3 3 5-6" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>SmartCS</h4><button id="scsX">&times;</button></div><div class="scs-body" id="scsBody"><div class="scs-msg bot">'+t.hello+'<span class="t">'+ih+'</span></div></div><div class="scs-ft"><input type="text" id="scsInput" placeholder="'+t.placeholder+'"><button id="scsSend">'+t.send+'</button></div>';
wrap.appendChild(panel);d.body.appendChild(wrap);
var convId=null;
function esc(s){var e=d.createElement('div');e.textContent=s;return e.innerHTML;}
function now(){var n=new Date(),h=n.getHours(),m=n.getMinutes();return (h<10?'0':'')+h+':'+(m<10?'0':'')+m;}
function addMsg(type,text){var body=document.getElementById('scsBody');var div=d.createElement('div');div.className='scs-msg '+type;div.innerHTML=esc(text)+'<span class="t">'+now()+'</span>';body.appendChild(div);body.scrollTop=body.scrollHeight;}
document.getElementById('scsBtn').onclick=function(){panel.classList.toggle('open')};
document.getElementById('scsX').onclick=function(){panel.classList.remove('open')};
function sendMsg(){
var input=document.getElementById('scsInput'),msg=input.value.trim();
if(!msg)return;
addMsg('visitor',msg);
input.value='';
var typing=d.createElement('div');typing.className='scs-typing';typing.innerHTML='<span>.</span><span>.</span><span>.</span>';document.getElementById('scsBody').appendChild(typing);document.getElementById('scsBody').scrollTop=document.getElementById('scsBody').scrollHeight;
fetch(base+'/api/chat/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tenant_code:tenant,visitor_id:vid,message:msg,conversation_id:convId})}).then(function(r){return r.json()}).then(function(data){
typing.remove();
if(data.code===200){convId=data.data.conversation_id;addMsg('bot',data.data.reply);}
else{addMsg('bot',t.sorry);}
}).catch(function(){typing.remove();addMsg('bot',t.error);});
}
document.getElementById('scsSend').onclick=sendMsg;
document.getElementById('scsInput').onkeydown=function(e){if(e.key==='Enter')sendMsg()};
})();
