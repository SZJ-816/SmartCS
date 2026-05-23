#!/usr/bin/env python3
import os, json, time, hashlib, uuid, re, logging, bcrypt
from datetime import datetime, timedelta
from functools import wraps
from logging.handlers import RotatingFileHandler
import jwt
import pymysql
from dbutils.pooled_db import PooledDB
from flask import Flask, request, jsonify, g, render_template, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["JSON_AS_ASCII"] = False

LOG_FILE = os.environ.get("SMARTCS_LOG", "/opt/smartcs/app.log")
handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "port": int(os.environ.get("DB_PORT", 3306)),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "root123"),
    "database": os.environ.get("DB_NAME", "smartcs"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

db_pool = PooledDB(
    creator=pymysql,
    maxconnections=20,
    mincached=2,
    **DB_CONFIG
)

JWT_SECRET = os.environ.get("JWT_SECRET", "SmartCS2026SecretKeyForPlatformAuth")
JWT_EXPIRATION = int(os.environ.get("JWT_EXPIRATION", 86400))

PLAN_PRICES = {"basic": 299.0, "pro": 999.0, "enterprise": 2999.0}
PLAN_LIMITS = {
    "free": {"max_agents": 1, "max_knowledge": 100, "max_conversations": 500},
    "basic": {"max_agents": 3, "max_knowledge": 500, "max_conversations": 2000},
    "pro": {"max_agents": 10, "max_knowledge": 2000, "max_conversations": 10000},
    "enterprise": {"max_agents": 50, "max_knowledge": 10000, "max_conversations": 50000},
}

limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["200 per minute"])

def get_db():
    if "db" not in g:
        g.db = db_pool.connection()
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db:
        try:
            db.close()
        except Exception:
            pass

def db_execute(sql, params=None, fetch=True):
    db = get_db()
    cur = db.cursor()
    cur.execute(sql, params or ())
    if fetch:
        if sql.strip().upper().startswith("SELECT"):
            return cur.fetchall()
    db.commit()
    return cur.lastrowid

def db_fetchone(sql, params=None):
    db = get_db()
    cur = db.cursor()
    cur.execute(sql, params or ())
    return cur.fetchone()

def create_token(user_id, tenant_id, username, role):
    payload = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"code": 401, "message": "unauthorized"}), 401
        payload = verify_token(auth[7:])
        if not payload:
            return jsonify({"code": 401, "message": "invalid or expired token"}), 401
        g.user_id = payload["user_id"]
        g.tenant_id = payload["tenant_id"]
        g.role = payload.get("role", "agent")
        return f(*args, **kwargs)
    return decorated

def ok(data=None):
    return jsonify({"code": 200, "message": "success", "data": data})

def fail(msg, code=500):
    return jsonify({"code": code, "message": msg}), code

def fmt_row(row):
    if not row:
        return row
    for k, v in row.items():
        if isinstance(v, datetime):
            row[k] = str(v)
    return row

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, password_hash):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return hashlib.sha256(password.encode()).hexdigest() == password_hash

@app.route("/api/auth/register", methods=["POST"])
@limiter.limit("5 per minute")
def auth_register():
    data = request.get_json() or {}
    company = data.get("company", "").strip()
    code = data.get("code", "").strip()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not all([company, code, username, email, password]) or len(password) < 6:
        return fail("invalid params", 400)
    if not re.match(r"^[a-z0-9_]+$", code):
        return fail("company code must be lowercase alphanumeric", 400)
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return fail("invalid email format", 400)

    if db_fetchone("SELECT id FROM tenant WHERE code = %s", (code,)):
        return fail("company code already exists", 400)

    tid = db_execute(
        "INSERT INTO tenant (name, code, plan, max_agents, max_knowledge, max_conversations) VALUES (%s,%s,%s,%s,%s,%s)",
        (company, code, "free", 1, 100, 500), fetch=False
    )
    pwd_hash = hash_password(password)
    uid = db_execute(
        "INSERT INTO user (tenant_id, username, email, password_hash, role) VALUES (%s,%s,%s,%s,%s)",
        (tid, username, email, pwd_hash, "admin"), fetch=False
    )
    token = create_token(uid, tid, username, "admin")
    app.logger.info("User registered: %s tenant: %s", username, code)
    return ok({"token": token, "tenant_id": tid, "role": "admin"})

@app.route("/api/auth/login", methods=["POST"])
@limiter.limit("10 per minute")
def auth_login():
    data = request.get_json() or {}
    code = data.get("code", "").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not all([code, username, password]):
        return fail("invalid params", 400)

    tenant = db_fetchone("SELECT * FROM tenant WHERE code = %s AND status = 1", (code,))
    if not tenant:
        return fail("company not found or disabled", 400)

    user = db_fetchone(
        "SELECT * FROM user WHERE tenant_id = %s AND username = %s AND status = 1",
        (tenant["id"], username)
    )
    if not user or not check_password(password, user["password_hash"]):
        app.logger.warning("Login failed for user: %s tenant: %s", username, code)
        return fail("invalid credentials", 400)

    token = create_token(user["id"], tenant["id"], username, user["role"])
    app.logger.info("User logged in: %s tenant: %s", username, code)
    return ok({
        "token": token,
        "tenant": fmt_row(tenant),
        "user": {"id": user["id"], "username": username, "role": user["role"]}
    })

@app.route("/api/auth/info")
@auth_required
def auth_info():
    tenant = db_fetchone("SELECT * FROM tenant WHERE id = %s", (g.tenant_id,))
    user = db_fetchone("SELECT id,username,email,role,status FROM user WHERE id = %s", (g.user_id,))
    return ok({"tenant": fmt_row(tenant), "user": fmt_row(user)})

@app.route("/api/knowledge")
@auth_required
def list_knowledge():
    page = int(request.args.get("page", 1))
    ps = int(request.args.get("pageSize", 20))
    cat = request.args.get("category", "")
    kw = request.args.get("keyword", "")

    sql = "SELECT * FROM knowledge WHERE tenant_id = %s AND status = 1"
    params = [g.tenant_id]
    if cat:
        sql += " AND category = %s"
        params.append(cat)
    if kw:
        sql += " AND (question LIKE %s OR answer LIKE %s)"
        params.extend([f"%{kw}%", f"%{kw}%"])

    count_sql = sql.replace("SELECT *", "SELECT COUNT(*) as total", 1)
    total = db_fetchone(count_sql, params)["total"]
    sql += " ORDER BY id DESC LIMIT %s OFFSET %s"
    params.extend([ps, (page - 1) * ps])
    rows = [fmt_row(r) for r in db_execute(sql, params)]
    return ok({"total": total, "page": page, "pageSize": ps, "records": rows})

@app.route("/api/knowledge/categories")
@auth_required
def knowledge_categories():
    rows = db_execute(
        "SELECT DISTINCT category FROM knowledge WHERE tenant_id=%s AND status=1",
        (g.tenant_id,)
    )
    return ok([r["category"] for r in rows])

@app.route("/api/knowledge", methods=["POST"])
@auth_required
def create_knowledge():
    data = request.get_json() or {}
    q = data.get("question", "").strip()
    a = data.get("answer", "").strip()
    cat = data.get("category", "general")
    kw = data.get("keywords", "")
    if not q or not a:
        return fail("question and answer required", 400)
    kid = db_execute(
        "INSERT INTO knowledge (tenant_id, category, question, answer, keywords) VALUES (%s,%s,%s,%s,%s)",
        (g.tenant_id, cat, q, a, kw), fetch=False
    )
    return ok({"id": kid})

@app.route("/api/knowledge/<int:kid>", methods=["GET"])
@auth_required
def get_knowledge(kid):
    row = db_fetchone(
        "SELECT * FROM knowledge WHERE id=%s AND tenant_id=%s AND status=1",
        (kid, g.tenant_id)
    )
    if not row:
        return fail("not found", 404)
    return ok(fmt_row(row))

@app.route("/api/knowledge/<int:kid>", methods=["PUT"])
@auth_required
def update_knowledge(kid):
    data = request.get_json() or {}
    q = data.get("question", "").strip()
    a = data.get("answer", "").strip()
    if not q or not a:
        return fail("question and answer required", 400)
    db_execute(
        "UPDATE knowledge SET question=%s, answer=%s, category=%s, keywords=%s WHERE id=%s AND tenant_id=%s",
        (q, a, data.get("category", "general"), data.get("keywords", ""), kid, g.tenant_id),
        fetch=False
    )
    return ok()

@app.route("/api/knowledge/<int:kid>", methods=["DELETE"])
@auth_required
def delete_knowledge(kid):
    db_execute(
        "UPDATE knowledge SET status=0 WHERE id=%s AND tenant_id=%s",
        (kid, g.tenant_id), fetch=False
    )
    return ok()

@app.route("/api/knowledge/batch", methods=["POST"])
@auth_required
def batch_knowledge():
    data = request.get_json() or {}
    items = data.get("items", [])
    if not items:
        return fail("no items provided", 400)
    count = 0
    for item in items:
        q = item.get("question", "").strip()
        a = item.get("answer", "").strip()
        if q and a:
            db_execute(
                "INSERT INTO knowledge (tenant_id, category, question, answer, keywords) VALUES (%s,%s,%s,%s,%s)",
                (g.tenant_id, item.get("category", "general"), q, a, item.get("keywords", "")),
                fetch=False
            )
            count += 1
    return ok({"count": count})

def ai_match_answer(tenant_id, question):
    rows = db_execute(
        "SELECT * FROM knowledge WHERE tenant_id=%s AND status=1 AND question LIKE %s LIMIT 5",
        (tenant_id, f"%{question}%")
    )
    if rows:
        db_execute("UPDATE knowledge SET view_count=view_count+1 WHERE id=%s", (rows[0]["id"],), fetch=False)
        return rows[0]["answer"]

    stop_words = set(list('\u7684\u4e86\u5417\u5462\u554a\u5427\u662f\u5728\u6709\u548c\u4e0e\u5417\u5427\u5462\u554a\u5417\u4e0d\u4e00\u4e2a\u8fd9\u4e2a\u90a3\u4e2a\u4ec0\u4e48\u600e\u4e48\u5982\u4f55\u80fd\u53ef\u4ee5\u8bf7\u95ee\u60f3\u8981\u8bf4\u544a\u8bc9\u77e5\u9053') + ['the','a','an','is','are','was','were','do','does','did','how','what','where','when','can','could','would','should','i','you','we','my','your','our','it','to','of','in','on','at','for','and','or','but'])
    chars = [c for c in question if c.strip() and c not in stop_words]
    chars = list(set(chars))

    if len(chars) >= 2:
        conditions = " AND keywords LIKE ".join(["%s"] * min(len(chars), 4))
        params = [tenant_id] + [f"%{c}%" for c in chars[:4]]
        rows = db_execute(
            "SELECT * FROM knowledge WHERE tenant_id=%s AND status=1 AND keywords LIKE " + conditions + " LIMIT 3",
            tuple(params)
        )
        if rows:
            db_execute("UPDATE knowledge SET view_count=view_count+1 WHERE id=%s", (rows[0]["id"],), fetch=False)
            return rows[0]["answer"]

    if len(chars) >= 1:
        for c in chars[:6]:
            rows = db_execute(
                "SELECT * FROM knowledge WHERE tenant_id=%s AND status=1 AND (keywords LIKE %s OR question LIKE %s) LIMIT 1",
                (tenant_id, f'%{c}%', f'%{c}%')
            )
            if rows:
                db_execute("UPDATE knowledge SET view_count=view_count+1 WHERE id=%s", (rows[0]["id"],), fetch=False)
                return rows[0]["answer"]

    segments = [question[i:i+2] for i in range(len(question) - 1) if len(question[i:i+2].strip()) == 2]
    best_match = None
    best_score = 0
    all_rows = db_execute("SELECT * FROM knowledge WHERE tenant_id=%s AND status=1", (tenant_id,))
    if all_rows:
        for row in all_rows:
            score = 0
            combined = (row.get('question', '') + ' ' + row.get('keywords', '') + ' ' + row.get('answer', '')).lower()
            for seg in segments:
                if seg in combined:
                    score += 1
            if score > best_score:
                best_score = score
                best_match = row
        if best_match and best_score >= 2:
            db_execute("UPDATE knowledge SET view_count=view_count+1 WHERE id=%s", (best_match["id"],), fetch=False)
            return best_match["answer"]

    return "sorry, I cannot find an answer to your question. Please try another way of asking or contact our support."

@app.route("/api/chat/send", methods=["POST"])
@limiter.limit("30 per minute")
def chat_send():
    data = request.get_json() or {}
    tenant_code = data.get("tenant_code", "").strip()
    visitor_id = data.get("visitor_id", str(uuid.uuid4())[:8])
    message_text = data.get("message", "").strip()
    conv_id = data.get("conversation_id")

    if not tenant_code or not message_text:
        return fail("invalid params", 400)

    tenant = db_fetchone("SELECT * FROM tenant WHERE code=%s AND status=1", (tenant_code,))
    if not tenant:
        return fail("tenant not found", 400)

    if not conv_id:
        conv_id = db_execute(
            "INSERT INTO conversation (tenant_id, visitor_id, status) VALUES (%s,%s,'bot')",
            (tenant["id"], visitor_id), fetch=False
        )

    db_execute(
        "INSERT INTO message (conversation_id, sender_type, content) VALUES (%s,'visitor',%s)",
        (conv_id, message_text), fetch=False
    )

    reply = ai_match_answer(tenant["id"], message_text)
    db_execute(
        "INSERT INTO message (conversation_id, sender_type, content) VALUES (%s,'bot',%s)",
        (conv_id, reply), fetch=False
    )

    return ok({"conversation_id": conv_id, "reply": reply, "visitor_id": visitor_id})

@app.route("/api/chat/history")
def chat_history():
    visitor_id = request.args.get("visitor_id", "")
    if not visitor_id:
        return fail("visitor_id required", 400)
    convs = db_execute(
        "SELECT * FROM conversation WHERE visitor_id=%s ORDER BY id DESC LIMIT 20",
        (visitor_id,)
    )
    return ok([fmt_row(c) for c in convs])

@app.route("/api/chat/messages/<int:conv_id>")
def chat_messages(conv_id):
    msgs = db_execute(
        "SELECT * FROM message WHERE conversation_id=%s ORDER BY id ASC",
        (conv_id,)
    )
    return ok([fmt_row(m) for m in msgs])

@app.route("/api/agent/conversations")
@auth_required
def agent_conversations():
    status = request.args.get("status", "")
    sql = "SELECT * FROM conversation WHERE tenant_id=%s"
    params = [g.tenant_id]
    if status:
        sql += " AND status=%s"
        params.append(status)
    sql += " ORDER BY id DESC LIMIT 50"
    return ok([fmt_row(c) for c in db_execute(sql, params)])

@app.route("/api/agent/takeover/<int:conv_id>", methods=["POST"])
@auth_required
def agent_takeover(conv_id):
    db_execute(
        "UPDATE conversation SET status='agent', agent_id=%s WHERE id=%s AND tenant_id=%s",
        (g.user_id, conv_id, g.tenant_id), fetch=False
    )
    db_execute(
        "INSERT INTO message (conversation_id, sender_type, sender_id, content) VALUES (%s,'agent',%s,%s)",
        (conv_id, g.user_id, "Agent joined the conversation"), fetch=False
    )
    return ok()

@app.route("/api/agent/reply", methods=["POST"])
@auth_required
def agent_reply():
    data = request.get_json() or {}
    conv_id = data.get("conversation_id")
    msg = data.get("message", "")
    if not conv_id or not msg:
        return fail("invalid params", 400)
    db_execute(
        "INSERT INTO message (conversation_id, sender_type, sender_id, content) VALUES (%s,'agent',%s,%s)",
        (conv_id, g.user_id, msg), fetch=False
    )
    return ok()

@app.route("/api/agent/close/<int:conv_id>", methods=["POST"])
@auth_required
def agent_close(conv_id):
    data = request.get_json() or {}
    db_execute(
        "UPDATE conversation SET status='closed', rating=%s WHERE id=%s AND tenant_id=%s",
        (data.get("rating"), conv_id, g.tenant_id), fetch=False
    )
    return ok()

@app.route("/api/stats/overview")
@auth_required
def stats_overview():
    total_conv = db_fetchone(
        "SELECT COUNT(*) as c FROM conversation WHERE tenant_id=%s",
        (g.tenant_id,)
    )["c"]
    today_conv = db_fetchone(
        "SELECT COUNT(*) as c FROM conversation WHERE tenant_id=%s AND DATE(created_at)=CURDATE()",
        (g.tenant_id,)
    )["c"]
    total_knowledge = db_fetchone(
        "SELECT COUNT(*) as c FROM knowledge WHERE tenant_id=%s AND status=1",
        (g.tenant_id,)
    )["c"]
    active_conv = db_fetchone(
        "SELECT COUNT(*) as c FROM conversation WHERE tenant_id=%s AND status IN ('bot','waiting','agent')",
        (g.tenant_id,)
    )["c"]
    return ok({
        "total_conversations": total_conv,
        "today_conversations": today_conv,
        "total_knowledge": total_knowledge,
        "active_conversations": active_conv
    })

@app.route("/api/stats/trend")
@auth_required
def stats_trend():
    rows = db_execute(
        "SELECT DATE(created_at) as dt, COUNT(*) as cnt FROM conversation WHERE tenant_id=%s AND created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) GROUP BY dt ORDER BY dt",
        (g.tenant_id,)
    )
    return ok([{"date": str(r["dt"]), "count": r["cnt"]} for r in rows])

@app.route("/api/subscription/plans")
def subscription_plans():
    plans = [
        {"key": "free", "name": "free", "price": 0, "features": ["1 agent", "100 FAQ", "500 chats/month"]},
        {"key": "basic", "name": "basic", "price": 299, "features": ["3 agents", "500 FAQ", "2000 chats/month", "basic analytics"]},
        {"key": "pro", "name": "pro", "price": 999, "features": ["10 agents", "2000 FAQ", "10000 chats/month", "advanced analytics", "custom branding"]},
        {"key": "enterprise", "name": "enterprise", "price": 2999, "features": ["50 agents", "unlimited FAQ", "unlimited chats", "custom AI training", "API access"]},
    ]
    return ok(plans)

@app.route("/api/subscription/subscribe", methods=["POST"])
@auth_required
def subscribe():
    data = request.get_json() or {}
    plan = data.get("plan", "")
    if plan not in PLAN_PRICES:
        return fail("invalid plan", 400)
    order_no = "SCS" + str(int(time.time() * 1000)) + uuid.uuid4().hex[:6]
    amount = PLAN_PRICES[plan]
    db_execute(
        "INSERT INTO subscription (tenant_id, order_no, plan, amount, status, paid_at) VALUES (%s,%s,%s,%s,'paid',%s)",
        (g.tenant_id, order_no, plan, amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        fetch=False
    )
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    expire = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    db_execute(
        "UPDATE tenant SET plan=%s, plan_expire_at=%s, max_agents=%s, max_knowledge=%s, max_conversations=%s WHERE id=%s",
        (plan, expire, limits["max_agents"], limits["max_knowledge"], limits["max_conversations"], g.tenant_id),
        fetch=False
    )
    app.logger.info("Subscription: tenant=%s plan=%s order=%s", g.tenant_id, plan, order_no)
    return ok({"order_no": order_no, "plan": plan, "amount": amount})

@app.route("/")
def index():
    lang = request.args.get('lang', 'en')
    if lang == 'zh':
        return render_template('index.zh.html')
    return render_template('index.html')

@app.route("/login")
def login_page():
    lang = request.args.get("lang", "en")
    tpl = "login.zh.html" if lang == "zh" else "login.html"
    return render_template(tpl)

@app.route("/register")
def register_page():
    lang = request.args.get("lang", "en")
    tpl = "register.zh.html" if lang == "zh" else "register.html"
    return render_template(tpl)

@app.route("/dashboard")
def dashboard_page():
    lang = request.args.get("lang", "en")
    tpl = "dashboard.zh.html" if lang == "zh" else "dashboard.html"
    return render_template(tpl)

@app.route("/knowledge")
def knowledge_page():
    lang = request.args.get("lang", "en")
    tpl = "knowledge.zh.html" if lang == "zh" else "knowledge.html"
    return render_template(tpl)

@app.route("/agent")
def agent_page():
    lang = request.args.get("lang", "en")
    tpl = "agent.zh.html" if lang == "zh" else "agent.html"
    return render_template(tpl)

@app.route("/pricing")
def pricing_page():
    lang = request.args.get("lang", "en")
    tpl = "pricing.zh.html" if lang == "zh" else "pricing.html"
    return render_template(tpl)

@app.route("/chat-widget.js")
def chat_widget():
    return send_from_directory("static", "widget.js")

@app.route("/api/health")
def health():
    return ok({"status": "running", "app": "SmartCS", "version": "1.1.0"})

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"code": 429, "message": "too many requests, please try again later"}), 429

@app.errorhandler(500)
def internal_error(e):
    app.logger.error("Internal error: %s", str(e))
    return jsonify({"code": 500, "message": "internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
