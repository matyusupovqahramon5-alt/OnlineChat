from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
import eventlet
from datetime import datetime
import json
import os

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Xabarlar faylda saqlanadi (server o‘chsa ham qoladi)
MESSAGE_FILE = "messages.json"

def load_messages():
    if os.path.exists(MESSAGE_FILE):
        try:
            with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_messages(msgs):
    with open(MESSAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(msgs[-1000:], f, ensure_ascii=False)  # oxirgi 1000 ta saqlanadi

messages = load_messages()
users = {}  # {sid: "Ism"}

HTML = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>UzChat 24/7</title>
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{background:#000;color:#fff;font-family:system-ui;height:100dvh;display:flex;flex-direction:column;overflow:hidden}
        header{background:#111;padding:16px;text-align:center;font-size:19px;font-weight:600;border-bottom:1px solid #333}
        #messages{flex:1;overflow-y:auto;padding:12px;-webkit-overflow-scrolling:touch}
        #messages::-webkit-scrollbar{display:none}
        .msg{max-width:82%;margin:8px 0;padding:12px 16px;border-radius:18px;word-wrap:break-word;position:relative;animation:a 0.3s}
        @keyframes a{from{opacity:0;transform:translateY(10px)}}
        .mine{background:#0d6efd;color:#fff;margin-left:auto;border-bottom-right-radius:4px}
        .other{background:#1e1e1e;color:#ddd;border-bottom-left-radius:4px}
        .name{font-size:13.5px;font-weight:600;margin-bottom:4px}
        .time{font-size:11.5px;opacity:0.7;position:absolute;bottom:5px;right:12px}
        form{display:flex;padding:10px 12px;background:#111;border-top:1px solid #333;gap:10px}
        input{flex:1;background:#222;color:#fff;border:none;border-radius:25px;padding:15px 18px;font-size:17px;outline:none}
        button{background:#0d6efd;color:#fff;border:none;border-radius:50%;width:54px;height:54px;font-size:24px}
        .welcome{height:100dvh;background:#000;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:25px;padding:20px;text-align:center}
        .welcome h1{font-size:28px;color:#58a6ff}
        .welcome input{width:85%;max-width:340px;padding:18px;font-size:19px;border-radius:16px;background:#222;color:#fff;text-align:center;border:none}
        .welcome button{padding:16px 50px;font-size:19px;background:#0d6efd;border-radius:16px;color:#fff;border:none}
    </style>
</head>
<body>

<div id="welcome" class="welcome">
    <h1>UzChat 24/7</h1>
    <p>Ismingizni kiriting<br><small>(keyin o‘zgartirib bo‘lmaydi)</small></p>
    <input id="nameInput" placeholder="Masalan: Feruzbek" maxlength="20" required autofocus>
    <button onclick="enter()">Kirish</button>
</div>

<div id="chat" style="display:none;flex-direction:column;height:100dvh">
    <header>UzChat 24/7</header>
    <div id="messages"></div>
    <form onsubmit="send();return false;">
        <input id="msg" placeholder="Xabar..." autocomplete="off" required>
        <button>Send</button>
    </form>
</div>

<script>
    const socket = io();
    let myName = localStorage.getItem("uzchat_name");

    // Eski xabarlarni yuklash
    fetch('/messages').then(r=>r.json()).then(d=> {
        d.forEach(m => addMsg(m));
        scroll();
    });

    if (myName) enter(myName);

    function enter(name=null) {
        if (!name) {
            name = document.getElementById("nameInput").value.trim();
            if (!name || name.length>20) return alert("Ism 1-20 belgi");
            localStorage.setItem("uzchat_name", name);
        }
        document.getElementById("welcome").style.display="none";
        document.getElementById("chat").style.display="flex";
        myName = name;
        socket.emit("join", name);
    }

    socket.on("msg", d => { addMsg(d); scroll(); });

    function addMsg(d) {
        let div = document.createElement("div");
        div.className = "msg " + (d.name===myName?"mine":"other");
        div.innerHTML = `<div class="name">${d.name}</div>${d.text}<div class="time">${d.time}</div>`;
        document.getElementById("messages").appendChild(div);
    }

    function scroll() {
        let m = document.getElementById("messages");
        m.scrollTop = m.scrollHeight;
    }

    function send() {
        let txt = document.getElementById("msg").value.trim();
        if (txt) {
            socket.emit("msg", txt);
            document.getElementById("msg").value = "";
        }
    }
</script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/messages")
def get_messages():
    return {"messages": messages}

@socketio.on("join")
def join(name):
    users[request.sid] = str(name)[:20]

@socketio.on("msg")
def handle(text):
    if request.sid not in users: return
    name = users[request.sid]
    msg = {
        "name": name,
        "text": str(text)[:800],
        "time": datetime.now().strftime("%d.%m %H:%M")
    }
    messages.append(msg)
    save_messages(messages)
    emit("msg", msg, broadcast=True)

@socketio.on("disconnect")
def dc():
    users.pop(request.sid, None)

if __name__ == "__main__":
    socketio.run(app)
