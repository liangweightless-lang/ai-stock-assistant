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

class AnalysisRequest(BaseModel):
    name: str
    code: str
    price_info: str
    news_context: str

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
                        results.append({
                            "name": parts[0],
                            "code": parts[3].lower(),
                            "short_code": parts[2]
                        })
            return {"success": True, "data": results[:8]}
    except Exception as e:
        logger.error(f"Suggest 接口网络联想发生错误: {e}")
        return {"success": False, "message": str(e)}


# 2. 个股行情盘面舆情抓取 API
@router.get("/stock")
async def get_stock_data(code: str = Query(..., regex=r"^(sh|sz)\d{6}$")):
    """
    一键抓取个股报盘与关联的 5 条新闻
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
                if len(data) >= 30:
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
    except Exception as e:
        logger.error(f"实时行情接口异常: {e}")
        quote_data = {"error": f"行情调取失败: {str(e)}"}

    # 抓取新闻头条
    news_list = []
    if "name" in quote_data:
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
    触发 AI 深度智能投研分析
    """
    provider = LLMFactory.get_provider()
    
    prompt = (
        f"你是一个资深的华尔街证券分析师。请针对以下实时获取的股票行情和舆情进行深度研报总结。\n\n"
        f"📊 【股票行情速递】:\n{req.price_info}\n\n"
        f"📰 【最新财经资讯】:\n{req.news_context}\n\n"
        f"请从以下三个维度输出分析结果（使用专业、客观、高水平的文笔，字数控制在250字左右）：\n"
        f"1. **今日盘面简评**\n"
        f"2. **舆情异动解析**\n"
        f"3. **投资决策与风险提示**"
    )

    async def event_generator():
        messages = [{'role': 'user', 'content': prompt}]
        stop_event = asyncio.Event()
        
        async for chunk in provider.generate_stream(messages, stop_event):
            # 以标准的 Server-Sent Events 格式吐出文本流
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
