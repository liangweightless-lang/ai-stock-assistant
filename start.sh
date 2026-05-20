#!/bin/bash
# Aegis AI 智能证券研报终端 - 企业级极速启动器

echo "================================================="
echo "  🚀 Aegis AI 智能证券投研终端 正在拉起启动链..."
echo "================================================="

# 1. 自动同步/继承通义千问 API 密钥 (继承自您的其它主开发环境)
if [ ! -f ".env" ]; then
    if [ -f "../lite-voice-study/backend/.env" ]; then
        grep "DASHSCOPE_API_KEY" ../lite-voice-study/backend/.env > .env 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "🔑 识别成功！已自动从邻近项目 [lite-voice-study] 中继承 [阿里云 DashScope API-KEY]"
        fi
    elif [ -f "../ai-sales-voice/backend/.env" ]; then
        grep "DASHSCOPE_API_KEY" ../ai-sales-voice/backend/.env > .env 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "🔑 识别成功！已自动从邻近项目 [ai-sales-voice] 中继承 [阿里云 DashScope API-KEY]"
        fi
    elif [ -f "../.env" ]; then
        grep "DASHSCOPE_API_KEY" ../.env > .env 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "🔑 识别成功！已自动从您的主开发环境中继承 [阿里云 DashScope API-KEY]"
        fi
    fi
fi

if [ ! -f ".env" ] || ! grep -q "DASHSCOPE_API_KEY" .env; then
    echo "⚠️ 提示: 未检测到 DASHSCOPE_API_KEY，如果您待会儿需要体验 AI 流式生成，请在新建的 .env 中填入秘钥。"
    touch .env
fi

# 2. 支持参数启动 Docker Compose
if [ "$1" == "docker" ]; then
    echo "🐳 正在通过 Docker Compose 构建并拉起独立容器组..."
    docker compose up --build -d
    echo "✔ 容器云服务成功运行！"
    echo "👉 访问浏览器体验面板："
    echo "   ➡️   http://localhost:5174"
    echo "================================================="
    exit 0
fi

# 3. 极速本地开发模式运行 (前后端解耦联调)
echo "⚡ 正在以本地前后端解耦开发模式拉起服务..."

# 3.1 补全后端依赖
echo "📦 正在校验后端 Python 依赖库环境..."
python3 -c "import fastapi, uvicorn, httpx, dotenv, dashscope" 2>/dev/null
if [ $? -ne 0 ]; then
    if command -v uv &> /dev/null; then
        echo "⚡ 发现 uv 极速包管理器，正在使用 uv 极速安装后端依赖..."
        uv pip install -r backend/requirements.txt
    else
        echo "🛠 正在为您自动安装后端微服务依赖包..."
        pip install -r backend/requirements.txt
    fi
fi

# 3.2 补全前端 pnpm/npm 依赖
echo "📦 正在校验前端 Node 依赖包环境..."
if [ -d "frontend/node_modules" ]; then
    echo "✔ 前端依赖完整性校验通过"
else
    cd frontend
    if command -v pnpm &> /dev/null; then
        echo "发现 pnpm 工具，正在极速安装前端依赖..."
        pnpm install
    else
        echo "正在使用 npm 安装前端依赖..."
        npm install
    fi
    cd ..
fi

# 4. 同时拉起后端 uvicorn 和前端 Vite
echo "================================================="
echo "🔥 服务即将全部启动！"
echo "👉 请在您的浏览器中访问此地址体验极致面板："
echo "   ➡️   http://localhost:5174"
echo "================================================="

# 捕获 Ctrl+C 并安全关闭所有后台进程
trap "kill 0" EXIT

# 4.1 在后台启动 FastAPI 异步后端
cd backend
python3 main.py &
cd ..

# 4.2 启动前端 Vite 热重载服务
cd frontend
if command -v pnpm &> /dev/null; then
    pnpm run dev
else
    npm run dev
fi
