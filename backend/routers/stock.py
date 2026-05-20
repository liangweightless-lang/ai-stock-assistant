import asyncio
import re
import urllib.parse
import httpx
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from config.settings import logger
from providers.factory import LLMFactory

router = APIRouter(prefix="/api")

from typing import List, Optional, Dict

class AnalysisRequest(BaseModel):
    name: str
    code: str
    price_info: str
    news_context: str
    question: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None

# 1. 智能股票自动联想 API
@router.get("/suggest")
async def suggest_stock(key: str = Query(..., min_length=1)):
    """
    智能联想股票代码与中文名
    """
    encoded_key = urllib.parse.quote(key)
    url = f"https://suggest3.sinajs.cn/suggest/key={encoded_key}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://finance.sina.com.cn"
    }
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(url, headers=headers)
            text = resp.text
            match = re.search(r'"([^"]+)"', text)
            results = []
            if match:
                items = match.group(1).split(';')
                for item in items:
                    if not item:
                        continue
                    parts = item.split(',')
                    if len(parts) >= 4:
                        asset_type = parts[1]
                        raw_code = parts[3].lower()
                        # 智能前缀规整：针对港股和美股补充新浪所需要的行情前缀
                        if asset_type == "31":
                            final_code = f"hk{raw_code}"
                        elif asset_type == "41":
                            final_code = f"gb_{raw_code}"
                        else:
                            final_code = raw_code

                        results.append({
                            "name": parts[0],
                            "code": final_code,
                            "short_code": parts[2]
                        })
                # 智能排序优化：优先把代表 A 股 (sh 或 sz 开头) 的股票排到前面！
                results.sort(key=lambda x: 0 if x["code"].startswith(("sh", "sz")) else 1)
            return {"success": True, "data": results[:8]}
    except Exception as e:
        logger.error(f"Suggest 接口网络联想发生错误: {e}")
        return {"success": False, "message": str(e)}


# 2. 个股行情盘面舆情抓取 API
@router.get("/stock")
async def get_stock_data(code: str = Query(..., regex=r"^[a-zA-Z0-9_]+$")):
    """
    一键抓取个股报盘与关联的 5 条新闻 (支持 A股、港股、美股多态解析)
    """
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://finance.sina.com.cn"
    }
    
    # 抓取个股报价
    quote_data = {}
    quote_url = f"https://hq.sinajs.cn/list={code}"
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(quote_url, headers=headers)
            content = resp.content.decode('gbk', errors='ignore')
            match = re.search(r'"([^"]+)"', content)
            if match:
                data = match.group(1).split(',')
                if code.startswith(("sh", "sz")) and len(data) >= 30:
                    # 1. 经典 A 股解析器
                    open_p = float(data[1])
                    prev_close = float(data[2])
                    current = float(data[3])
                    change_val = current - prev_close if current > 0 else 0
                    change_pct = (change_val / prev_close) * 100 if prev_close > 0 else 0
                    quote_data = {
                        "name": data[0],
                        "code": code.upper(),
                        "open": f"{open_p:.2f}",
                        "prev_close": f"{prev_close:.2f}",
                        "current": f"{current:.2f}",
                        "high": f"{float(data[4]):.2f}",
                        "low": f"{float(data[5]):.2f}",
                        "volume": f"{int(float(data[8])/100):,}",
                        "turnover": f"{float(data[9])/10000:.2f}",
                        "change_val": f"{change_val:+.2f}",
                        "change_pct": f"{change_pct:+.2f}%",
                        "is_up": change_val >= 0,
                        "time": f"{data[30]} {data[31]}"
                    }
                elif code.startswith("hk") and len(data) >= 15:
                    # 2. 跨国港股解析器
                    open_p = float(data[2])
                    prev_close = float(data[3])
                    current = float(data[6])
                    change_val = float(data[7])
                    change_pct = float(data[8])
                    quote_data = {
                        "name": data[1],
                        "code": code.upper(),
                        "open": f"{open_p:.2f}",
                        "prev_close": f"{prev_close:.2f}",
                        "current": f"{current:.2f}",
                        "high": f"{float(data[4]):.2f}",
                        "low": f"{float(data[5]):.2f}",
                        "volume": f"{int(float(data[12])/100):,}",
                        "turnover": f"{float(data[11])/10000:.2f}",
                        "change_val": f"{change_val:+.2f}",
                        "change_pct": f"{change_pct:+.2f}%",
                        "is_up": change_val >= 0,
                        "time": f"{data[17]} {data[18]}"
                    }
                elif code.startswith("gb_") and len(data) >= 27:
                    # 3. 跨国美股解析器
                    current = float(data[1])
                    change_pct = float(data[2])
                    open_p = float(data[5])
                    high_p = float(data[6])
                    low_p = float(data[7])
                    volume = float(data[10])
                    prev_close = float(data[26])
                    change_val = current - prev_close
                    quote_data = {
                        "name": data[0],
                        "code": code.upper(),
                        "open": f"{open_p:.2f}",
                        "prev_close": f"{prev_close:.2f}",
                        "current": f"{current:.2f}",
                        "high": f"{high_p:.2f}",
                        "low": f"{low_p:.2f}",
                        "volume": f"{int(volume):,}",
                        "turnover": "暂无",
                        "change_val": f"{change_val:+.2f}",
                        "change_pct": f"{change_pct:+.2f}%",
                        "is_up": change_val >= 0,
                        "time": data[3]
                    }
    except Exception as e:
        logger.error(f"实时行情接口异常: {e}")
 
    # 极佳的兜底保障机制，防范前端 JSON.stringify 抹除 undefined 从而导致 POST analyze 422 报错
    if not quote_data or "error" in quote_data:
        quote_data = {
            "name": "未知股票",
            "code": code.upper(),
            "open": "0.00",
            "prev_close": "0.00",
            "current": "0.00",
            "high": "0.00",
            "low": "0.00",
            "volume": "0",
            "turnover": "0.00",
            "change_val": "+0.00",
            "change_pct": "+0.00%",
            "is_up": True,
            "time": "暂无数据"
        }

    # 抓取新闻头条
    news_list = []
    if "name" in quote_data and quote_data["name"] != "未知股票":
        encoded_name = urllib.parse.quote(quote_data["name"])
        news_url = f"https://search.sina.com.cn/?q={encoded_name}&c=news&sort=time"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(news_url, headers=headers)
                text = resp.text
                pattern = r'<h2><a href="([^"]+)"[^>]*>(.*?)</a>'
                matches = re.findall(pattern, text)
                for idx, (link, title) in enumerate(matches[:5]):
                    clean_title = re.sub(r'<[^>]+>', '', title).strip()
                    news_list.append({
                        "id": idx + 1,
                        "title": clean_title,
                        "link": link
                    })
        except Exception as e:
            logger.error(f"金融舆情获取失败: {e}")
 
    return {
        "success": True,
        "quote": quote_data,
        "news": news_list
    }


# 3. AI 智能研报生成 API (SSE 事件流)
@router.post("/analyze")
async def analyze_stock(req: AnalysisRequest):
    """
    触发 AI 深度智能投研分析 & 支持多轮深度追问交互
    """
    provider = LLMFactory.get_provider()
    
    # 基础投研研报 Prompt
    base_report_prompt = (
        f"你是一个资深的华尔街证券分析师。请针对以下实时获取的股票行情和舆情进行深度研报总结。\n\n"
        f"📊 【股票行情速递】:\n{req.price_info}\n\n"
        f"📰 【最新财经资讯】:\n{req.news_context}\n\n"
        f"请从以下三个维度输出分析结果（使用专业、客观、高水平的文笔，字数控制在250字左右）：\n"
        f"1. **今日盘面简评**\n"
        f"2. **舆情异动解析**\n"
        f"3. **投资决策与风险提示**"
    )

    messages = []
    
    # 判断是否有历史对话，进行多轮追问上下文组装
    if req.history and len(req.history) > 0:
        # 首先注入带有盘口背景的首轮 Prompt 充当系统设定
        messages.append({'role': 'user', 'content': base_report_prompt})
        # 依次读入历史对话气泡，排除可能重复的第一条
        for msg in req.history:
            role = 'user' if msg.get('role') == 'user' else 'assistant'
            # 略过我们手动硬编码进 messages 的首轮 base prompt 结果（第一条 assistant）
            if len(messages) == 1 and role == 'assistant':
                messages.append({'role': 'assistant', 'content': msg.get('content', '')})
            else:
                messages.append({'role': role, 'content': msg.get('content', '')})
        
        # 追入最新提问
        if req.question:
            messages.append({'role': 'user', 'content': req.question})
    else:
        # 首次生成，或者直接提问
        if req.question:
            chat_prompt = (
                f"你是一个资深的华尔街证券分析师。当前分析的股票背景信息如下：\n"
                f"📊 【股票最新行情】:\n{req.price_info}\n"
                f"📰 【最新舆情头条】:\n{req.news_context}\n\n"
                f"请结合以上股票盘口及新闻背景，专业且深刻地解答用户的追问问题：\n"
                f"👉 **{req.question}**"
            )
            messages.append({'role': 'user', 'content': chat_prompt})
        else:
            messages.append({'role': 'user', 'content': base_report_prompt})

    async def event_generator():
        stop_event = asyncio.Event()
        async for chunk in provider.generate_stream(messages, stop_event):
            # 以标准的 Server-Sent Events 格式吐出文本流
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
