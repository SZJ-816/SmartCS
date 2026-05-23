# SmartCS — AI 智能客服 SaaS 平台

<p align="center">
  <strong>5 分钟部署 · AI 自动回复 80% 常见问题 · 复杂问题无缝转人工</strong>
</p>

<p align="center">
  <a href="#功能特性">功能</a> · <a href="#快速开始">快速开始</a> · <a href="#技术架构">架构</a> · <a href="#定价">定价</a> · <a href="#部署">部署</a> · <a href="#license">License</a>
</p>

---

## 功能特性

- **AI 智能回复** — 基于知识库训练，自然语言理解自动回复常见问题，准确率 95%+
- **智能知识库** — 支持 FAQ、产品文档批量导入，AI 持续学习优化
- **无缝人工转接** — 复杂问题即时人工接管，携带完整对话上下文
- **深度分析** — 对话趋势、知识缺口、满意度监控，数据驱动优化
- **多端聊窗** — 一行代码嵌入任意网站，PC/移动自适应
- **中英双语** — 完整 i18n 支持，EN/中文一键切换
- **企业安全** — 多租户隔离，数据加密，GDPR 合规

## 快速开始

### 环境要求

- Python 3.7+
- MySQL 5.7+ / 8.0
- Docker (可选，用于 MySQL)

### 1. 克隆项目

```bash
git clone https://github.com/SZJ-816/SmartCS.git
cd SmartCS
```

### 2. 初始化数据库

```bash
# 启动 MySQL (Docker 方式)
docker run -d --name smartcs-mysql \
  -e MYSQL_ROOT_PASSWORD=smartcs123 \
  -e MYSQL_DATABASE=smartcs \
  -p 3306:3306 \
  mysql:8.0

# 导入初始化 SQL
mysql -h 127.0.0.1 -u root -psmartcs123 smartcs < sql/init.sql
```

### 3. 启动后端

```bash
cd backend
pip install -r requirements.txt

# 修改 app.py 中的数据库配置
# DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

python3 app.py
```

访问 http://localhost:8080 即可看到首页。

### 4. 嵌入聊窗

在你的网站 HTML 中添加一行代码：

```html
<script src="//your-domain/chat-widget.js" data-tenant="YOUR_CODE"></script>
```

## 技术架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   浏览器      │────▶│   Flask API   │────▶│   MySQL     │
│  (前端页面)   │◀────│  (Python)     │◀────│  (多租户)    │
└─────────────┘     └──────────────┘     └─────────────┘
       │                    │
       │                    ▼
       │             ┌──────────────┐
       └────────────▶│  Chat Widget │
                     │  (嵌入组件)   │
                     └──────────────┘
```

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | HTML5 + CSS3 + Vanilla JS |
| 样式 | 自定义 CSS (轻奢黑金风格) |
| 后端 | Python Flask |
| 数据库 | MySQL 8.0 |
| 部署 | Docker + Nginx + cpolar |

### 项目结构

```
SmartCS/
├── backend/
│   ├── app.py                 # Flask 主应用 (API + 路由)
│   ├── requirements.txt       # Python 依赖
│   ├── static/
│   │   ├── luxury.css         # 全局样式 (轻奢风格)
│   │   └── widget.js          # 嵌入式聊窗组件
│   └── templates/
│       ├── index.html         # 首页 (EN)
│       ├── index.zh.html      # 首页 (ZH)
│       ├── login.html         # 登录 (EN)
│       ├── login.zh.html      # 登录 (ZH)
│       ├── register.html      # 注册 (EN)
│       ├── register.zh.html   # 注册 (ZH)
│       ├── dashboard.html     # 管理面板 (EN)
│       ├── dashboard.zh.html  # 管理面板 (ZH)
│       ├── knowledge.html     # 知识库 (EN)
│       ├── knowledge.zh.html  # 知识库 (ZH)
│       ├── agent.html         # 客服对话 (EN)
│       ├── agent.zh.html      # 客服对话 (ZH)
│       ├── pricing.html       # 订阅管理 (EN)
│       └── pricing.zh.html    # 订阅管理 (ZH)
└── sql/
    └── init.sql               # 数据库初始化脚本
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 企业注册 |
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/knowledge` | 查询知识库 |
| POST | `/api/knowledge` | 添加知识条目 |
| PUT | `/api/knowledge/<id>` | 更新知识条目 |
| DELETE | `/api/knowledge/<id>` | 删除知识条目 |
| POST | `/api/chat/start` | 开启对话 |
| POST | `/api/chat/message` | 发送消息 (AI 回复) |
| GET | `/api/chat/messages/<id>` | 获取对话记录 |
| GET | `/api/agent/conversations` | 人工客服对话列表 |
| POST | `/api/agent/reply` | 人工客服回复 |
| POST | `/api/agent/close/<id>` | 关闭对话 |
| GET | `/api/stats/overview` | 数据概览 |
| POST | `/api/subscription/subscribe` | 订阅套餐 |

## 定价

| 方案 | 月费 | 坐席 | 知识条目 | 月对话量 |
|------|------|------|---------|---------|
| 免费版 | ¥0 | 1 | 100 | 500 |
| 基础版 | ¥299 | 3 | 500 | 2,000 |
| 专业版 | ¥999 | 10 | 2,000 | 10,000 |
| 企业版 | ¥2,999 | 50 | 无限 | 无限 |

## 部署

### Docker 部署 (推荐)

```bash
# 1. 启动 MySQL
docker run -d --name smartcs-mysql \
  -e MYSQL_ROOT_PASSWORD=smartcs123 \
  -e MYSQL_DATABASE=smartcs \
  -p 3306:3306 mysql:8.0

# 2. 初始化数据库
docker exec -i smartcs-mysql mysql -uroot -psmartcs123 smartcs < sql/init.sql

# 3. 启动应用
cd backend
pip install -r requirements.txt
python3 app.py
```

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /opt/smartcs/backend/static/;
    }
}
```

### 内网穿透 (cpolar)

```bash
cpolar http 8080
```

## 国际化

所有页面支持中英文双语，通过 URL 参数 `?lang=en` / `?lang=zh` 切换：

- 首页: `/?lang=zh`
- 登录: `/login?lang=zh`
- 注册: `/register?lang=zh`
- 管理面板: `/dashboard?lang=zh`
- 知识库: `/knowledge?lang=zh`
- 客服对话: `/agent?lang=zh`
- 订阅管理: `/pricing?lang=zh`

## 测试账号

| 字段 | 值 |
|------|------|
| 公司代码 | `smartcs` |
| 用户名 | `admin` |
| 密码 | `123456` |

## License

MIT License

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/SZJ-816">SZJ-816</a>
</p>
