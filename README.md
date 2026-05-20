# ⚡ Aegis AI - 智能证券投研数据终端 (Aegis Finance AI)

[![Platform](https://img.shields.io/badge/Platform-Docker%20%7C%20Local-blue?logo=docker)](https://www.docker.com/)
[![Tech Stack](https://img.shields.io/badge/Tech%20Stack-FastAPI%20%2B%20Vue%203%20%2B%20TS%20%2B%20Vite-green?logo=vue.js)](https://vuejs.org/)
[![Model](https://img.shields.io/badge/LLM-Qwen--Plus%20(DashScope)-orange?logo=alibabacloud)](https://help.aliyun.com/zh/dashscope/)

Aegis AI 智能证券投研数据终端是一款专为证券从业人员、投研机构打造的**超轻量、高性能智能决策辅助沙盘**。项目采用企业级前后端解耦（Client-Server）微服务架构，提供毫秒级个股输入联想、实时行情爬取、财经新闻舆情监测，并融合阿里云通义千问大模型进行 SSE 字节流极速投研报告生成。

---

## 📂 企业级微服务目录结构

项目深度借鉴并复刻了企业级标杆项目 `lite-voice-study` 的核心设计模式：

```
ai-stock-assistant/
├── backend/                  # FastAPI 异步高性能网关微服务
│   ├── config/               # 集中式配置模块 (Settings & logger)
│   ├── providers/            # 面向对象的多态大模型驱动套件 (Qwen)
│   ├── tools/                # 金融数据爬虫与解析引擎
│   ├── routers/              # 解耦控制器路由组 (suggest / stock / analyze)
│   ├── requirements.txt      # 依赖描述清单
│   └── main.py               # 后端服务主入口网关
│
├── frontend/                 # 顶配现代化 Vite 前端 SPA 容器
│   ├── src/                  # 前端核心源码 (Vue 3 setup + TS)
│   │   ├── App.vue           # 霓虹磨砂玻璃拟态面板 (Canvas电波图、SSE打字流)
│   │   └── main.ts           # Vue 挂载总入口
│   ├── vite.config.ts        # Vite 反向开发代理配置 (开发环境防跨域)
│   ├── nginx.conf            # 生产环境 Nginx (彻底关闭 buffering，透传 SSE 流)
│   └── Dockerfile            # 前端多阶段极速构建描述
│
├── docker-compose.yml        # 生产容器云一键编排描述
├── .env                      # 阿里云通义千问等全局 API-KEY 配置 (自动继承)
└── start.sh                  # 自适应极速开发/容器云启动脚本 (chmod +x)
```

---

## 🌐 端口共享共存规划 (非常重要)

为了满足在**同一台云服务器**上，将本系统与 **`lite-voice-study`** 以及 **`blog_server`** 进行完美并排无冲突部署，各服务对外端口规划如下（请勿占用）：

| 应用/系统名称 | 绑定组件服务 | 容器内网络 | 宿主机外网映射端口 | 状态与冲突规避 |
| :--- | :--- | :--- | :--- | :--- |
| **lite-voice-study** | 网页控制前端 | 80 | **`5173`** | ✅ 完美兼容，互不干扰 |
| | 交互语音后端 | 9090 | **`9090`** | ✅ 完美兼容，互不干扰 |
| **blog_server** | 博客主服务 | 80 / 8080 | **`80` / `8080`等** | ✅ 完美兼容，互不干扰 |
| **ai-stock-assistant** | **投研数据前端** | **80** | **`5174`** | 🚀 **全新顺延独占** |
| | **智能投研后端** | **9091** | **`9091`** | 🚀 **全新顺延独占** |

---

## ⚙️ 核心技术特性解析

### 1. Nginx 代理缓冲区穿透 (Buffering Bypass)
由于投研研报采用大模型流式传输（Server-Sent Events），若开启代理缓存，Nginx 将拦截传输块导致打字效果卡顿。因此我们在生产 `nginx.conf` 中显式设置了：
```nginx
proxy_buffering off;
```
这一配置使得 AI 吐出的每个字符都能够实现毫秒级零延迟渲染。

### 2. 智能联想与接口防抖 (Debounce Search)
前端输入框内置防抖拦截器（200ms），用户在连续输入个股拼音或中文时，会自动阻止高频网络震荡，并在下拉框中毫秒级映射出 A 股标准交易代码。

---

## 🚦 极速部署运行说明

本工程提供了本地极速开发与 Docker 容器化两种拉起方式，并已为您编写了自适应启动链。

### 方式一：🚀 本地解耦开发调试模式 (推荐)
此模式适合本地进行代码修改与热重载调试，无需构建容器镜像，速度最快：
```bash
# 1. 切换到项目目录
cd /Users/weightless/Documents/Project/ai-stock-assistant

# 2. 一键拉起启动脚本 (脚本会自动从您已有项目中继承复制 API-KEY，并自动配齐前后端包依赖)
./start.sh
```
* **浏览器访问地址**：👉 **`http://localhost:5174`**
* **本地开发反代**：Vite 自动将前端 `/api` 的数据交互无感反代至后端的 `9091` 端口。

### 方式二：🐳 生产级 Docker Compose 一键部署
在云服务器中进行独立容器化镜像部署：
```bash
# 1. 切换到项目目录
cd /Users/weightless/Documents/Project/ai-stock-assistant

# 2. 传递 docker 参数，一键构建并后台运行容器集群
./start.sh docker
```
* **浏览器访问地址**：👉 **`http://localhost:5174`**
* **容器运行状态监控**：`docker compose ps`
* **容器日志实时查看**：`docker compose logs -f`
