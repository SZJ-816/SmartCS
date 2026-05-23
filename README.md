# SmartCS - AI 智能客服 SaaS 平台

## 简介

SmartCS 是一个开源的 AI 智能客服 SaaS 平台，让您能够快速构建和部署 AI 驱动的客户服务。

## 功能特性

- ✨ **AI 智能回复** - 基于知识库的智能匹配
- 📚 **知识库管理** - 轻松导入和管理 FAQ
- 💬 **人工接管** - 复杂问题无缝转接人工客服
- 📊 **数据分析** - 对话趋势、满意度分析
- 📱 **多渠道组件** - 一键部署到任意网站
- 🔐 **企业级安全** - 数据加密、租户隔离

## 快速开始

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python app.py
```

### 部署到服务器

参考 `smartcs.service` 配置 systemd 服务。

## 技术栈

- **后端**: Flask + PyJWT + PyMySQL + DBUtils
- **前端**: 原生 HTML/CSS/JS + Material You 设计
- **数据库**: MySQL 8.0
- **部署**: Docker + Cpolar 内网穿透

## 目录结构

```
smartcs_new/
├── backend/
│   ├── app.py              # 主应用
│   ├── requirements.txt    # Python 依赖
│   ├── templates/          # 页面模板
│   └── static/             # 静态资源
└── docker/                # Docker 配置
```

## 测试账号

- 用户名: `demo@smartcs.io`
- 密码: `demo123`

## License

MIT License
