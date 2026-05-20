<template>
  <div class="glow-bg glow-blue"></div>
  <div class="glow-bg glow-purple"></div>

  <div class="app-container">
    <!-- 头部品牌导航 -->
    <header class="main-header">
      <div class="logo-area">
        <span class="logo-icon">⚡</span>
        <h1>AEGIS <span class="logo-highlight">FINANCE AI</span></h1>
      </div>
      <div class="system-status">
        <span class="status-dot green"></span>
        <span class="status-text">通义千问大模型已就绪 (RAG)</span>
      </div>
    </header>

    <!-- 检索搜索中枢区 -->
    <section class="search-section">
      <div class="search-box-wrapper">
        <div class="search-input-container" :class="{ 'focused': isFocused }">
          <span class="search-icon">🔍</span>
          <input 
            type="text" 
            v-model="searchInput" 
            @input="onSearchInput"
            @focus="isFocused = true"
            @blur="onBlur"
            @keydown.enter="triggerSearch"
            placeholder="输入上市企业简称或股票代码 (例如: 贵州茅台 / 比亚迪 / 600519)..." 
            autocomplete="off"
          >
          <button v-if="searchInput" @click="clearSearch" class="clear-btn">✕</button>
        </div>
        <!-- 智能模糊搜索联想下拉框 -->
        <div v-if="showSuggestions && suggestions.length > 0" class="suggest-dropdown">
          <div 
            v-for="item in suggestions" 
            :key="item.code" 
            class="suggest-item"
            @mousedown="selectSuggestion(item)"
          >
            <span class="stock-name">{{ item.name }}</span>
            <span class="stock-code">{{ item.code.toUpperCase() }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 默认引导欢迎大卡片 -->
    <section v-if="!dashboardVisible" class="glass-card welcome-card">
      <div class="welcome-icon">🚀</div>
      <h2>开启您的 AI 股票数据洞察</h2>
      <p>在上方搜索框内输入任意 A 股上市企业名称或代码。Aegis 将通过云端金融探针实时调度行情报盘、爬取最新财经新闻舆情，并结合顶级大模型在毫秒内为您输出流式深度投资研报。</p>
      <div class="sample-tags">
        <span v-for="tag in ['比亚迪', '贵州茅台', '宁德时代', '腾讯控股']" :key="tag" class="sample-tag" @click="clickSampleTag(tag)">
          {{ tag }}
        </span>
      </div>
    </section>

    <!-- 主面板数据仪表盘 -->
    <main v-else class="dashboard-grid">
      
      <!-- 栏目一：行情交易面板 -->
      <div class="glass-card quote-card">
        <div class="card-header">
          <h3 class="card-title">📊 实时行情报盘</h3>
          <span class="badge">{{ quoteData.code }}</span>
        </div>
        
        <div class="price-display-section">
          <h2>{{ quoteData.name }}</h2>
          <div class="price-large-row">
            <span class="price-val" :style="{ color: quoteData.is_up ? 'var(--color-up)' : 'var(--color-down)' }">
              {{ quoteData.current }}
            </span>
            <div class="price-change-wrapper" :class="quoteData.is_up ? 'stock-up' : 'stock-down'">
              <span class="change-val">{{ quoteData.change_val }}</span>
              <span class="change-pct">{{ quoteData.change_pct }}</span>
            </div>
          </div>
        </div>

        <!-- 动态 Canvas 分时走势电波图 -->
        <div class="chart-container">
          <div class="chart-label">今日动态模拟分时电波图</div>
          <canvas ref="canvasRef" id="trend-canvas"></canvas>
        </div>

        <div class="quote-details-grid">
          <div class="detail-item">
            <span class="label">今日开盘价</span>
            <span class="value">{{ quoteData.open }} 元</span>
          </div>
          <div class="detail-item">
            <span class="label">昨日收盘价</span>
            <span class="value">{{ quoteData.prev_close }} 元</span>
          </div>
          <div class="detail-item">
            <span class="label">今日最高价</span>
            <span class="value">{{ quoteData.high }} 元</span>
          </div>
          <div class="detail-item">
            <span class="label">今日最低价</span>
            <span class="value">{{ quoteData.low }} 元</span>
          </div>
          <div class="detail-item">
            <span class="label">成交量(手)</span>
            <span class="value">{{ quoteData.volume }}</span>
          </div>
          <div class="detail-item">
            <span class="label">成交额(万元)</span>
            <span class="value">{{ quoteData.turnover }}</span>
          </div>
        </div>
        <div class="update-timestamp">更新时间: {{ quoteData.time }}</div>
      </div>

      <!-- 栏目二：深度智能研报面板 -->
      <div class="glass-card report-card">
        <div class="card-header">
          <h3 class="card-title">🧠 AI 智能深度研报</h3>
          <div class="generation-controls">
            <button @click="generateAIReport" class="glow-btn" :disabled="isGenerating">
              {{ isGenerating ? '⚡ 正在诊断分析...' : '⚡ 重新生成研报' }}
            </button>
          </div>
        </div>
        
        <div class="report-console">
          <div class="console-scan-line"></div>
          <div class="console-body">
            <div v-if="isGenerating && !reportContent" class="report-loading-wrapper">
              <span class="loader-spinner"></span>
              <p>{{ loadingText }}</p>
            </div>
            <!-- 大模型流式研报渲染框 -->
            <div 
              v-else 
              class="report-markdown" 
              v-html="formattedReport"
            ></div>
          </div>
        </div>
      </div>

      <!-- 栏目三：最新财经舆情头条 -->
      <div class="glass-card news-card">
        <div class="card-header">
          <h3 class="card-title">📰 实时财经舆情头条</h3>
        </div>
        <div class="news-list">
          <p v-if="newsList.length === 0" class="empty-news">该上市公司暂无最新相关舆情。</p>
          <a 
            v-else
            v-for="item in newsList" 
            :key="item.id" 
            :href="item.link" 
            target="_blank" 
            class="news-item"
          >
            <span class="news-item-title">{{ item.title }}</span>
            <span class="news-arrow">↗</span>
          </a>
        </div>
      </div>

    </main>
  </div>

  <!-- 全局 Toast 提示 -->
  <div v-if="toastVisible" class="toast">{{ toastMessage }}</div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted, nextTick } from 'vue'

// 1. 声明响应式变量
const searchInput = ref('')
const isFocused = ref(false)
const showSuggestions = ref(false)
const suggestions = ref<any[]>([])
const dashboardVisible = ref(false)

const quoteData = ref<any>({
  name: '',
  code: '',
  current: '',
  change_val: '',
  change_pct: '',
  is_up: true,
  open: '',
  prev_close: '',
  high: '',
  low: '',
  volume: '',
  turnover: '',
  time: ''
})

const newsList = ref<any[]>([])
const reportContent = ref('')
const isGenerating = ref(false)
const loadingText = ref('')
const toastMessage = ref('')
const toastVisible = ref(false)

const canvasRef = ref<HTMLCanvasElement | null>(null)
let debounceTimer: any = null
let chartAnimationId: any = null

// 2. 深度报告格式化计算
const formattedReport = computed(() => {
  if (!reportContent.value) {
    return '<p style="color: var(--text-muted);">等待生成实时投研报告...</p>'
  }
  return reportContent.value
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
})

// 3. 全局消息提示方法
function showToast(msg: string, duration = 3000) {
  toastMessage.value = msg;
  toastVisible.value = true;
  setTimeout(() => {
    toastVisible.value = false;
  }, duration);
}

// 4. 输入联想与防抖
function onSearchInput() {
  const val = searchInput.value.trim();
  if (val) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      fetchSuggestions(val);
    }, 200);
  } else {
    showSuggestions.value = false;
  }
}

function onBlur() {
  // 微小延迟，确保点击下拉项的时间优先执行
  setTimeout(() => {
    showSuggestions.value = false;
  }, 150);
}

function clearSearch() {
  searchInput.value = '';
  showSuggestions.value = false;
}

// 获取匹配词
async function fetchSuggestions(query: string) {
  try {
    const resp = await fetch(`/api/suggest?key=${encodeURIComponent(query)}`);
    const res = await resp.json();
    if (res.success && res.data.length > 0) {
      suggestions.value = res.data;
      showSuggestions.value = true;
    } else {
      showSuggestions.value = false;
    }
  } catch (err) {
    console.error('联想失效:', err);
  }
}

// 选中联想词
function selectSuggestion(item: any) {
  searchInput.value = item.name;
  showSuggestions.value = false;
  loadStockDashboard(item.code);
}

// 直接回车搜索
async function triggerSearch() {
  const val = searchInput.value.trim();
  if (!val) return;
  
  try {
    const resp = await fetch(`/api/suggest?key=${encodeURIComponent(val)}`);
    const res = await resp.json();
    if (res.success && res.data.length > 0) {
      loadStockDashboard(res.data[0].code);
    } else {
      showToast(`未能查找到有关“${val}”的企业匹配`);
    }
  } catch (err) {
    showToast('匹配服务网络故障');
  }
}

// 点击示例股票标签
function clickSampleTag(tag: string) {
  searchInput.value = tag;
  triggerSearch();
}

// 5. 行情与深度大盘加载
async function loadStockDashboard(codeStr: string) {
  showToast('正在实时抓取最新行情及新闻舆情...', 1500);
  dashboardVisible.value = true;
  isGenerating.value = true;
  loadingText.value = '正在拉取个股实时财务数据包...';
  reportContent.value = '';

  try {
    const resp = await fetch(`/api/stock?code=${codeStr}`);
    const res = await resp.json();
    if (res.success && res.quote && !res.quote.error) {
      quoteData.value = res.quote;
      newsList.value = res.news;
      
      // 开启 Canvas 分时动态电波动画
      nextTick(() => {
        initTrendChart(res.quote.is_up);
      });

      // 智能流式生成研报
      await generateAIReport();
    } else {
      showToast('行情数据抓取失败，请确认代码是否正确');
      isGenerating.value = false;
    }
  } catch (err) {
    showToast('获取个股综合数据网络异常');
    isGenerating.value = false;
  }
}

// 6. 流式生成 AI 分析研报 (SSE EventStream Reader)
async function generateAIReport() {
  isGenerating.value = true;
  loadingText.value = '正在连线通义千问大模型，进行深度投研诊断...';
  reportContent.value = '';

  const q = quoteData.value;
  const n = newsList.value;
  
  const price_info = `股票简称: ${q.name}, 最新价格: ${q.current}元, 今日开盘价: ${q.open}元, 最高价: ${q.high}元, 最低价: ${q.low}元, 涨跌幅: ${q.change_pct}`;
  const news_context = n.map((item, idx) => `${idx+1}. ${item.title}`).join('\n');

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: q.name,
        code: q.code,
        price_info: price_info,
        news_context: news_context || "无最新财经公告舆情"
      })
    });

    if (!response.ok) {
      throw new Error('服务器 AI 生成失败');
    }

    isGenerating.value = false;

    const reader = response.body?.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    if (!reader) return;

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const chunk = line.slice(6);
          if (chunk === '[DONE]') break;
          reportContent.value += chunk;
        }
      }
    }
  } catch (err: any) {
    isGenerating.value = false;
    reportContent.value = `❌ **研报解析失败**: ${err.message || '请确保后端 .env 中的 DASHSCOPE_API_KEY 已正确配置。'}`;
  }
}

// 7. Canvas 高阶股票行情波动曲线绘制
function initTrendChart(isUp: boolean) {
  const canvas = canvasRef.value;
  if (!canvas) return;
  
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const width = rect.width;
  const height = rect.height;

  // 模拟20个波动坐标数据
  const points: { x: number; y: number }[] = [];
  const baseOffset = height / 2;
  for (let i = 0; i <= 20; i++) {
    const x = (width / 20) * i;
    const noise = (Math.sin(i * 0.8) * 15) + (Math.cos(i * 1.5) * 8) + (Math.random() * 6 - 3);
    const trendFactor = isUp ? -(i * 1.2) : (i * 1.2);
    const y = baseOffset + noise + trendFactor;
    points.push({ x, y });
  }

  let frame = 0;

  function animate() {
    if (!ctx) return;
    ctx.clearRect(0, 0, width, height);
    
    // 背景极暗格栅线
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.02)';
    ctx.lineWidth = 1;
    for (let i = 20; i < height; i += 30) {
      ctx.beginPath();
      ctx.moveTo(0, i);
      ctx.lineTo(width, i);
      ctx.stroke();
    }

    // 绘制填充渐变区
    ctx.beginPath();
    ctx.moveTo(points[0].x, height);
    ctx.lineTo(points[0].x, points[0].y);
    for (let i = 0; i < points.length - 1; i++) {
      const xc = (points[i].x + points[i + 1].x) / 2;
      const yc = (points[i].y + points[i + 1].y) / 2;
      ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
    }
    const lastPoint = points[points.length - 1];
    ctx.lineTo(lastPoint.x, lastPoint.y);
    ctx.lineTo(width, height);
    ctx.closePath();

    const fillGrad = ctx.createLinearGradient(0, 0, 0, height);
    if (isUp) {
      fillGrad.addColorStop(0, 'rgba(16, 185, 129, 0.15)');
      fillGrad.addColorStop(1, 'rgba(16, 185, 129, 0.0)');
    } else {
      fillGrad.addColorStop(0, 'rgba(244, 63, 94, 0.15)');
      fillGrad.addColorStop(1, 'rgba(244, 63, 94, 0.0)');
    }
    ctx.fillStyle = fillGrad;
    ctx.fill();

    // 绘制霓虹高亮曲线边框
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 0; i < points.length - 1; i++) {
      const xc = (points[i].x + points[i + 1].x) / 2;
      const yc = (points[i].y + points[i + 1].y) / 2;
      ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
    }
    ctx.lineTo(lastPoint.x, lastPoint.y);
    ctx.strokeStyle = isUp ? 'var(--color-up)' : 'var(--color-down)';
    ctx.lineWidth = 2.5;
    ctx.shadowBlur = 10;
    ctx.shadowColor = isUp ? 'rgba(16, 185, 129, 0.5)' : 'rgba(244, 63, 94, 0.5)';
    ctx.stroke();
    ctx.shadowBlur = 0;

    // 行情圆点跳动脉冲
    frame++;
    const pulseRadius = 4 + Math.abs(Math.sin(frame * 0.15) * 4);
    const pulseAlpha = 0.8 - Math.abs(Math.sin(frame * 0.15) * 0.5);

    ctx.beginPath();
    ctx.arc(lastPoint.x - 2, lastPoint.y, pulseRadius, 0, 2 * Math.PI);
    ctx.fillStyle = isUp ? `rgba(16, 185, 129, ${pulseAlpha})` : `rgba(244, 63, 94, ${pulseAlpha})`;
    ctx.fill();

    ctx.beginPath();
    ctx.arc(lastPoint.x - 2, lastPoint.y, 3, 0, 2 * Math.PI);
    ctx.fillStyle = isUp ? 'var(--color-up)' : 'var(--color-down)';
    ctx.fill();

    chartAnimationId = requestAnimationFrame(animate);
  }

  if (chartAnimationId) cancelAnimationFrame(chartAnimationId);
  animate();
}

onUnmounted(() => {
  if (chartAnimationId) cancelAnimationFrame(chartAnimationId);
})
</script>

<style>
/* ==========================================
   🌐 AEGIS AI - 高奢极客证券投研终端设计系统
   ========================================== */
:root {
  --bg-primary: #03050d;         /* 深邃星空极暗色，对比度直接拉满 */
  --card-bg: rgba(9, 14, 32, 0.75); /* 提高卡片不透明度，阻挡背景多余毛玻璃杂音 */
  --card-border: rgba(255, 255, 255, 0.06);
  --card-border-hover: rgba(0, 210, 255, 0.35); /* 悬浮时呈现高亮科技蓝边框 */
  
  --accent-blue: #00d2ff;        /* 亮丽高饱和科技青蓝色 */
  --accent-purple: #d500f9;      /* 绚丽霓虹紫 */
  --accent-glow: rgba(0, 210, 255, 0.25);
  
  --text-main: #ffffff;          /* 纯白高亮字 */
  --text-secondary: #f3f4f6;     /* 极清灰白字 */
  --text-muted: #94a3b8;         /* 亮蓝灰字，用于次要说明，极易辨识 */
  
  --color-up: #10b981;
  --color-up-glow: rgba(16, 185, 129, 0.15);
  --color-down: #f43f5e;
  --color-down-glow: rgba(244, 63, 94, 0.15);
  
  --font-heading: 'Outfit', 'Inter', sans-serif;
  --font-body: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}

/* 全局重置与平滑渲染 */
html, body {
  background-color: var(--bg-primary);
  color: var(--text-main);
  margin: 0;
  padding: 0;
  min-height: 100vh;
  font-family: var(--font-body);
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 霓虹发光粒子背景层 */
.glow-bg {
  position: fixed;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  filter: blur(180px);
  opacity: 0.18;
  pointer-events: none;
  z-index: 0;
}
.glow-blue {
  background: radial-gradient(circle, var(--accent-blue) 0%, transparent 70%);
  top: -150px;
  left: -150px;
}
.glow-purple {
  background: radial-gradient(circle, var(--accent-purple) 0%, transparent 70%);
  bottom: -150px;
  right: -150px;
}

.app-container {
  width: 100%;
  max-width: 1440px;
  padding: 3rem 2rem;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
  margin: 0 auto;
  box-sizing: border-box;
}

.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding-bottom: 1.8rem;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}
.logo-icon {
  font-size: 2.2rem;
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 0 8px var(--accent-glow));
}
.logo-area h1 {
  font-family: var(--font-heading);
  font-size: 1.8rem;
  letter-spacing: 3px;
  font-weight: 800;
  color: var(--text-main);
  margin: 0;
}
.logo-highlight {
  background: linear-gradient(90deg, var(--accent-blue), #00ffcc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.system-status {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.9rem;
  color: var(--text-muted);
  font-weight: 500;
}
.status-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}
.status-dot.green {
  background-color: var(--color-up);
  box-shadow: 0 0 12px var(--color-up);
  animation: pulse 2s infinite;
}

/* 检索搜索中枢 */
.search-section {
  display: flex;
  justify-content: center;
  width: 100%;
}
.search-box-wrapper {
  width: 100%;
  max-width: 800px;
  position: relative;
}
.search-input-container {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--card-border);
  border-radius: 24px;
  padding: 0.8rem 1.8rem;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(12px);
}
.search-input-container.focused {
  border-color: var(--accent-blue);
  background: rgba(255, 255, 255, 0.05);
  box-shadow: 0 0 30px rgba(0, 210, 255, 0.3);
  transform: scale(1.01);
}
.search-icon {
  font-size: 1.3rem;
  margin-right: 1.2rem;
  color: var(--accent-blue);
  text-shadow: 0 0 8px var(--accent-glow);
}
.search-input-container input {
  width: 100%;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-main);
  font-size: 1.15rem;
  font-family: var(--font-body);
  font-weight: 500;
}
.search-input-container input::placeholder {
  color: var(--text-muted);
  opacity: 0.65;
}
.clear-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0 0.5rem;
  transition: color 0.2s;
}
.clear-btn:hover {
  color: var(--color-down);
}

/* 智能联想下拉 */
.suggest-dropdown {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  width: 100%;
  background: rgba(10, 16, 38, 0.96);
  border: 1px solid rgba(0, 210, 255, 0.25);
  border-radius: 20px;
  box-shadow: 0 20px 45px rgba(0, 0, 0, 0.6);
  z-index: 100;
  max-height: 350px;
  overflow-y: auto;
  padding: 0.6rem;
  backdrop-filter: blur(25px);
}
.suggest-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.9rem 1.4rem;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s ease;
  font-family: var(--font-heading);
}
.suggest-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-left: 3px solid var(--accent-blue);
  padding-left: 1.6rem;
}
.suggest-item .stock-name {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-main);
}
.suggest-item .stock-code {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  color: var(--accent-blue);
  background: rgba(0, 210, 255, 0.08);
  border: 1px solid rgba(0, 210, 255, 0.15);
  padding: 0.2rem 0.6rem;
  border-radius: 6px;
  font-weight: 600;
}

/* 玻璃态高级卡片底座 */
.glass-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 28px;
  padding: 2.2rem;
  backdrop-filter: blur(25px);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.35);
}
.glass-card:hover {
  border-color: var(--card-border-hover);
  box-shadow: 0 16px 50px rgba(0, 210, 255, 0.15);
  transform: translateY(-4px);
}

.welcome-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  max-width: 850px;
  margin: 3.5rem auto;
  padding: 4.5rem 3rem;
  gap: 1.8rem;
  background: radial-gradient(circle at top, rgba(0, 210, 255, 0.04), transparent 70%), var(--card-bg);
}
.welcome-icon {
  font-size: 4.5rem;
  animation: float 4s ease-in-out infinite;
  filter: drop-shadow(0 0 15px var(--accent-glow));
}
.welcome-card h2 {
  font-family: var(--font-heading);
  font-size: 2.2rem;
  font-weight: 800;
  margin: 0;
  background: linear-gradient(90deg, #ffffff, var(--text-muted));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.welcome-card p {
  color: var(--text-muted);
  line-height: 1.8;
  font-size: 1.1rem;
  margin: 0;
  max-width: 700px;
}
.sample-tags {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 1rem;
}
.sample-tag {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 24px;
  padding: 0.6rem 1.5rem;
  font-size: 0.95rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 500;
}
.sample-tag:hover {
  background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple));
  border-color: transparent;
  color: #fff;
  box-shadow: 0 0 25px rgba(0, 210, 255, 0.45);
  transform: translateY(-2px) scale(1.02);
}

/* 仪表盘多栏布局网格 */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1.3fr 1.7fr;
  grid-template-rows: auto auto;
  gap: 2.5rem;
  animation: fadeIn 0.7s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

.quote-card {
  grid-column: 1;
  grid-row: 1 / 3;
  display: flex;
  flex-direction: column;
  gap: 1.8rem;
}
.report-card {
  grid-column: 2;
  grid-row: 1;
}
.news-card {
  grid-column: 2;
  grid-row: 2;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}
.card-title {
  font-family: var(--font-heading);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: 0.5px;
  margin: 0;
}
.badge {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  background: rgba(0, 210, 255, 0.06);
  border: 1px solid rgba(0, 210, 255, 0.18);
  padding: 0.25rem 0.75rem;
  border-radius: 8px;
  color: var(--accent-blue);
  font-weight: 600;
}

.price-display-section h2 {
  font-family: var(--font-heading);
  font-size: 2rem;
  margin: 0 0 0.6rem 0;
  color: var(--text-main);
  font-weight: 800;
}
.price-large-row {
  display: flex;
  align-items: baseline;
  gap: 1.4rem;
}
.price-val {
  font-family: var(--font-heading);
  font-size: 3.6rem;
  font-weight: 800;
  letter-spacing: -1px;
  text-shadow: 0 0 20px rgba(255, 255, 255, 0.05);
}
.price-change-wrapper {
  display: flex;
  gap: 0.5rem;
  font-size: 1.15rem;
  font-weight: 700;
  padding: 0.3rem 0.8rem;
  border-radius: 10px;
}
.stock-up {
  color: var(--color-up);
  background: var(--color-up-glow);
  box-shadow: inset 0 0 8px rgba(16, 185, 129, 0.1);
}
.stock-down {
  color: var(--color-down);
  background: var(--color-down-glow);
  box-shadow: inset 0 0 8px rgba(244, 63, 94, 0.1);
}

.quote-details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.2rem;
  background: rgba(255, 255, 255, 0.015);
  border-radius: 20px;
  padding: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.025);
}
.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.detail-item .label {
  font-size: 0.85rem;
  color: var(--text-muted);
  font-weight: 500;
}
.detail-item .value {
  font-family: var(--font-heading);
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-main);
}
.update-timestamp {
  font-size: 0.8rem;
  color: var(--text-muted);
  text-align: right;
  font-weight: 500;
}

.chart-container {
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.025);
  border-radius: 20px;
  padding: 1.2rem;
  box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
}
.chart-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 0.6rem;
  font-weight: 500;
}
#trend-canvas {
  width: 100%;
  height: 140px;
  display: block;
}

.glow-btn {
  background: linear-gradient(95deg, var(--accent-blue), var(--accent-purple));
  border: none;
  border-radius: 14px;
  color: #fff;
  padding: 0.7rem 1.6rem;
  font-family: var(--font-heading);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 18px rgba(0, 210, 255, 0.3);
}
.glow-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(0, 210, 255, 0.55);
}
.glow-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* AI 投研研报渲染框（核心重构段，超高对比度） */
.report-console {
  background: rgba(3, 5, 15, 0.92);
  border: 1px solid rgba(0, 210, 255, 0.18);
  border-radius: 20px;
  position: relative;
  padding: 1.8rem;
  overflow: hidden;
  min-height: 250px;
  box-shadow: inset 0 0 30px rgba(0, 210, 255, 0.03);
}
.console-scan-line {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, transparent, rgba(0, 210, 255, 0.25), transparent);
  animation: scan 4s linear infinite;
  pointer-events: none;
}
.report-loading-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  gap: 1.2rem;
  color: var(--text-muted);
}
.loader-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255, 255, 255, 0.05);
  border-top: 3px solid var(--accent-blue);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  filter: drop-shadow(0 0 5px var(--accent-glow));
}
.report-markdown {
  line-height: 1.9;
  color: var(--text-secondary); /* 高亮度字，防虚防暗 */
  font-size: 1.05rem;           /* 略微调大字号，更适合阅读 */
}
.report-markdown p {
  margin-bottom: 1.2rem;
}
.report-markdown strong {
  color: var(--accent-blue);   /* 重点加粗词高亮显示科技青色 */
  font-weight: 700;
  text-shadow: 0 0 10px rgba(0, 210, 255, 0.2);
}

.news-list {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
  max-height: 320px;
  overflow-y: auto;
}
.empty-news {
  color: var(--text-muted);
  text-align: center;
  padding: 2.5rem 0;
  font-weight: 500;
}
.news-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.015);
  border: 1px solid rgba(255, 255, 255, 0.03);
  border-radius: 14px;
  padding: 1.1rem 1.3rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-decoration: none;
  color: inherit;
  gap: 1rem;
}
.news-item:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(0, 210, 255, 0.2);
  transform: translateX(6px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}
.news-item-title {
  font-size: 1.02rem;
  line-height: 1.6;
  color: var(--text-secondary); /* 升级亮色 */
  transition: color 0.25s ease;
  font-weight: 500;
}
.news-item:hover .news-item-title {
  color: var(--accent-blue);  /* 悬停时标题点亮为科技青色 */
}
.news-arrow {
  color: var(--text-muted);
  font-size: 1rem;
  transition: transform 0.25s ease;
}
.news-item:hover .news-arrow {
  transform: translate(2px, -2px);
  color: var(--accent-blue);
}

.toast {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(10, 16, 38, 0.95);
  border: 1px solid rgba(0, 210, 255, 0.35);
  border-radius: 14px;
  padding: 0.9rem 2.2rem;
  box-shadow: 0 15px 40px rgba(0,0,0,0.6);
  backdrop-filter: blur(15px);
  font-size: 0.95rem;
  font-weight: 600;
  z-index: 1000;
  animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: var(--text-main);
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.25); opacity: 0.45; }
  100% { transform: scale(1); opacity: 1; }
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-12px); }
  100% { transform: translateY(0px); }
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes slideUp {
  from { bottom: 0; opacity: 0; }
  to { bottom: 2rem; opacity: 1; }
}
@keyframes scan {
  0% { top: -3px; }
  50% { top: 100%; }
  100% { top: -3px; }
}
</style>
