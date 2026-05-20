import httpx
import re
import urllib.parse
from config.settings import logger

async def get_stock_code(keyword: str) -> tuple[str, str]:
    """
    通过新浪智能联想输入 API，将公司名称映射为股票代码 (例如: 比亚迪 -> sz002594)
    """
    clean_keyword = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]", "", keyword).strip()
    if not clean_keyword:
        return None, None
        
    encoded_key = urllib.parse.quote(clean_keyword)
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
            if match:
                parts = match.group(1).split(',')
                if len(parts) >= 4:
                    return parts[3], parts[0]
    except Exception as e:
        logger.error(f"个股映射转换异常: {e}")
    return None, None

async def fetch_stock_quote(code: str) -> str:
    """
    获取个股实时行情数据
    """
    url = f"https://hq.sinajs.cn/list={code}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://finance.sina.com.cn"
    }
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(url, headers=headers)
            content = resp.content.decode('gbk', errors='ignore')
            match = re.search(r'"([^"]+)"', content)
            if match:
                data = match.group(1).split(',')
                if len(data) >= 30:
                    return (
                        f"【{data[0]} ({code.upper()}) 实时行情】\n"
                        f"• 今日开盘价: {data[1]} 元\n"
                        f"• 昨日收盘价: {data[2]} 元\n"
                        f"• 当前最新价: {data[3]} 元\n"
                        f"• 今日最高价: {data[4]} 元\n"
                        f"• 今日最低价: {data[5]} 元\n"
                        f"• 成交量: {int(float(data[8])/100)} 手\n"
                        f"• 成交额: {float(data[9])/10000:.2f} 万元\n"
                        f"• 数据更新时间: {data[30]} {data[31]}"
                    )
    except Exception as e:
        return f"行情抓取异常: {e}"
    return "无交易盘面快照。"

async def fetch_stock_news(keyword: str) -> list[dict]:
    """
    从新浪财经搜索获取最新的个股新闻舆情
    """
    encoded_key = urllib.parse.quote(keyword)
    url = f"https://search.sina.com.cn/?q={encoded_key}&c=news&sort=time"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://finance.sina.com.cn"
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers=headers)
            text = resp.text
            pattern = r'<h2><a href="([^"]+)"[^>]*>(.*?)</a>'
            matches = re.findall(pattern, text)
            news_list = []
            for link, title in matches[:4]:
                clean_title = re.sub(r'<[^>]+>', '', title).strip()
                news_list.append({"title": clean_title, "link": link})
            return news_list
    except Exception as e:
        logger.error(f"金融头条舆情抓取异常: {e}")
        return []

async def get_financial_report(company_name: str) -> str:
    """
    金融终端主入口：一键生成个股画像数据包
    """
    code, matched_name = await get_stock_code(company_name)
    if not code:
        return f"抱歉，未能匹配到名为 '{company_name}' 的 A 股上市公司。"
    
    quote = await fetch_stock_quote(code)
    news = await fetch_stock_news(matched_name)
    
    report = f"{quote}\n\n📰 【最新相关新闻与财务公告】:\n"
    if news:
        for idx, item in enumerate(news, 1):
            report += f"{idx}. {item['title']}\n"
    else:
        report += "• 暂未检索到实时市场相关新闻。\n"
    return report
