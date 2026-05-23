(function(){
var d=document,sc=d.currentScript,tenant=sc.getAttribute('data-tenant')||'demo',base=sc.src.replace(/\/chat-widget\.js.*/,'');
var vid=localStorage.getItem('scs_vid')||'v'+Math.random().toString(36).substr(2,8);
localStorage.setItem('scs_vid',vid);
var style=d.createElement('style');
style.textContent=[
'.scs-w{position:fixed;bottom:32px;right:32px;z-index:9999}',
'.scs-btn{width:52px;height:52px;background:#0A0A0A;color:#fff;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s}',
'.scs-btn:hover{background:#262626}',
'.scs-panel{display:none;position:fixed;bottom:100px;right:32px;width:380px;height:540px;background:#fff;border:1px solid #e5e5e5;flex-direction:column;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,.1)}',
'.scs-panel.open{display:flex}',
'.scs-hdr{background:#0A0A0A;color:#fff;padding:20px 24px;display:flex;justify-content:space-between;align-items:center}',
'.scs-hdr h4{margin:0;font-size:14px;font-weight:600;letter-spacing:.04em}',
'.scs-hdr button{background:none;border:none;color:rgba(255,255,255,.5);cursor:pointer;font-size:20px;line-height:1}',
'.scs-hdr button:hover{color:#fff}',
'.scs-body{flex:1;padding:20px;overflow-y:auto;display:flex;flex-direction:column;gap:12px}',
'.scs-msg{max-width:80%;padding:10px 14px;font-size:14px;line-height:1.6;border-radius:2px}',
'.scs-msg.visitor{align-self:flex-end;background:#f5f5f5}',
'.scs-msg.bot{align-self:flex-start;background:#0A0A0A;color:#fff}',
'.scs-msg .t{font-size:11px;opacity:.5;margin-top:4px;display:block}',
'.scs-ft{padding:16px 20px;border-top:1px solid #e5e5e5;display:flex;gap:10px}',
'.scs-ft input{flex:1;padding:10px 14px;border:1px solid #e5e5e5;font-size:14px;outline:none}',
'.scs-ft input:focus{border-color:#0A0A0A}',
'.scs-ft button{padding:10px 16px;background:#0A0A0A;color:#fff;border:none;font-size:13px;font-weight:500;cursor:pointer;white-space:nowrap}'
].join('');
d.head.appendChild(style);
var wrap=d.createElement('div');wrap.className='scs-w';
wrap.innerHTML='<button class="scs-btn" id="scsBtn"><svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 4h14v10H10L6 17V14H3V4z"/><line x1="7" y1="8" x2="13" y2="8"/><line x1="7" y1="11" x2="11" y2="11"/></svg></button>';
var panel=d.createElement('div');panel.className='scs-panel';
panel.innerHTML='<div class="scs-hdr"><h4>Customer Service</h4><button id="scsX">&times;</button></div><div class="scs-body" id="scsBody"><div class="scs-msg bot">Hello! How can I help you?<span class="t">now</span></div></div><div class="scs-ft"><input type="text" id="scsInput" placeholder="Type a message..."><button id="scsSend">Send</button></div>';
wrap.appendChild(panel);d.body.appendChild(wrap);
var convId=null;
document.getElementById('scsBtn').onclick=function(){panel.classList.toggle('open')};
document.getElementById('scsX').onclick=function(){panel.classList.remove('open')};
function sendMsg(){
var input=document.getElementById('scsInput'),msg=input.value.trim();
if(!msg)return;
var body=document.getElementById('scsBody');
body.innerHTML+='<div class="scs-msg visitor">'+msg.replace(/</g,'&lt;')+'<span class="t">now</span></div>';
input.value='';
body.scrollTop=body.scrollHeight;
var typing=d.createElement('div');typing.className='scs-msg bot';typing.textContent='...';body.appendChild(typing);
body.scrollTop=body.scrollHeight;
fetch(base+'/api/chat/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tenant_code:tenant,visitor_id:vid,message:msg,conversation_id:convId})}).then(function(r){return r.json()}).then(function(data){
typing.remove();
if(data.code===200){
convId=data.data.conversation_id;
body.innerHTML+='<div class="scs-msg bot">'+data.data.reply.replace(/</g,'&lt;')+'<span class="t">now</span></div>';
}else{body.innerHTML+='<div class="scs-msg bot">Sorry, please try again.<span class="t">now</span></div>';}
body.scrollTop=body.scrollHeight;
}).catch(function(){typing.remove();body.innerHTML+='<div class="scs-msg bot">Network error.<span class="t">now</span></div>';body.scrollTop=body.scrollHeight;});
}
document.getElementById('scsSend').onclick=sendMsg;
document.getElementById('scsInput').onkeydown=function(e){if(e.key==='Enter')sendMsg()};
})();
