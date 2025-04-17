from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import pandas as pd
import logging
import json
import re
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
import traceback
from aiocache import cached

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the MCP server
mcp = FastMCP("Screener.in Server")

# Define Screener.in API base URL and headers
SCREENER_API_BASE = "https://www.screener.in"
SCREENER_CSRF_TOKEN = os.getenv("SCREENER_CSRF_TOKEN")
SCREENER_SESSION_ID = os.getenv("SCREENER_SESSION_ID")
SCREENER_CSRF_MIDDLEWARE_TOKEN = os.getenv("SCREENER_CSRF_MIDDLEWARE_TOKEN")


cookies = {
    'theme': 'auto',
    'csrftoken': SCREENER_CSRF_TOKEN,
    'sessionid': SCREENER_SESSION_ID,
}

# content-type might not be needed in get request headers
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'max-age=0',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://www.screener.in',
    'priority': 'u=0, i',
    'referer': 'https://www.screener.in',
    'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    # 'cookie': 'theme=auto; csrftoken=qwe; sessionid=fgh',
}

data = {
    'csrfmiddlewaretoken': SCREENER_CSRF_MIDDLEWARE_TOKEN,
    'next': '/company/WIPRO/consolidated/',
}

# Helper function to make API requests
async def make_screener_request(endpoint: str, req_type: str = "get", params: dict[str, Any] = None) -> dict[str, Any] | None:
    async with httpx.AsyncClient() as client:
        try:
            response = None
            if req_type == "post":
                response = await client.post(f"{SCREENER_API_BASE}/{endpoint}", headers=headers, cookies=cookies, data=data)
            else:
                response = await client.get(f"{SCREENER_API_BASE}/{endpoint}", headers=headers, params=params)
            response.raise_for_status()
            return {"response": response}
        except Exception as e:
            logging.info(f"response: {type(response)}, {response}, {response.has_redirect_location}, {response.next_request}")
            logging.info(f"response.text: {response.text}")
            return {"error": str(e)}

# Helper function to get warehouse id for downloading excel report
async def get_warehouse_and_company_id(symbol):
    logging.info("Getting warehouse id: " + symbol)
    api = f"{SCREENER_API_BASE}/api/company/search/?q={symbol}"
    async with httpx.AsyncClient() as client:
        d = await client.get(api)
        j = json.loads(d.content)[0]
        html = await client.get('https://www.screener.in' + j['url'])
        # print(f"html: {html.text}")
        warehouse_id = re.findall('formaction=./user/company/export/(.*?)/.', html.text)
        company_id = re.findall('formaction=./api/company/(.*?)/add/.', html.text)
        return warehouse_id[0], company_id[0]


@mcp.tool()
async def download_report(symbol: str) -> str:
    """Download excel report for a stock from Screener.in."""
    path = "./reports"
    warehouseid, _ = await get_warehouse_and_company_id(symbol)
    url = f'{SCREENER_API_BASE}/user/company/export/{warehouseid}/'
    async with httpx.AsyncClient() as client:
        r = await client.post(url, cookies=cookies, headers=headers, data=data)
        logging.info(f"r.status_code: {r.status_code}")
        r.raise_for_status()
        path = f'{path}/{symbol.strip()}.xlsx'

        if r.status_code == 200:
            with open(path, 'wb') as f:
                f.write(r.content)
            logging.info(f"Excel file created for: {symbol}")
            return path
        else:
            logging.info(f"Error in downloading report for: {symbol}")
            return f"Error in downloading report for: {symbol}"

@cached(ttl=3600)  # Cache results for 1 hour
async def read_stock_info(stock: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Read detailed stock information from Screener.in."""
    url = f"{SCREENER_API_BASE}/company/{stock}/"
    df_list = pd.read_html(url)
    print(f"Number of tables: {len(df_list)}")
    df_list = [df for df in df_list if df.shape[1] > 1]
    print(f"Number of tables after filtering: {len(df_list)}")
    df_quarterly_results = df_list[0]
    df_quarterly_results.index = df_quarterly_results['Unnamed: 0']
    df_quarterly_results = df_quarterly_results.drop(columns=['Unnamed: 0'])
    df_quarterly_results.index.name = 'Quarter'
    df_profit_loss = df_list[1]
    df_profit_loss.index = df_profit_loss['Unnamed: 0']
    df_profit_loss = df_profit_loss.drop(columns=['Unnamed: 0'])
    df_profit_loss.index.name = 'Profit & Loss'
    df_balance_sheet = df_list[6]
    df_balance_sheet.index = df_balance_sheet['Unnamed: 0']
    df_balance_sheet = df_balance_sheet.drop(columns=['Unnamed: 0'])
    df_balance_sheet.index.name = 'Balance Sheet'
    df_cash_flow = df_list[7]
    df_cash_flow.index = df_cash_flow['Unnamed: 0']
    df_cash_flow = df_cash_flow.drop(columns=['Unnamed: 0'])
    df_cash_flow.index.name = 'Cash Flow'
    df_ratios = df_list[8]
    df_ratios.index = df_ratios['Unnamed: 0']
    df_ratios = df_ratios.drop(columns=['Unnamed: 0'])
    df_ratios.index.name = 'Ratios'
    df_shareholding_pattern_quarterly = df_list[9]
    df_shareholding_pattern_quarterly.index = df_shareholding_pattern_quarterly['Unnamed: 0']
    df_shareholding_pattern_quarterly = df_shareholding_pattern_quarterly.drop(columns=['Unnamed: 0'])
    df_shareholding_pattern_quarterly.index.name = 'Shareholding Pattern Quarterly'
    df_shareholding_pattern_yearly = df_list[10]
    df_shareholding_pattern_yearly.index = df_shareholding_pattern_yearly['Unnamed: 0']
    df_shareholding_pattern_yearly = df_shareholding_pattern_yearly.drop(columns=['Unnamed: 0'])
    df_shareholding_pattern_yearly.index.name = 'Shareholding Pattern Yearly'

    return (df_quarterly_results, df_profit_loss, df_balance_sheet, df_cash_flow, df_ratios, 
            df_shareholding_pattern_quarterly, df_shareholding_pattern_yearly)

# Multiple tool below which uses above func to get company details like quaterly results, pnl, etc
@mcp.tool()
async def get_quarterly_results(company_name: str) -> dict[str, Any]:
    """Fetch quarterly results for a company from Screener.in."""
    df_quarterly_results, _, _, _, _, _, _ = await read_stock_info(company_name)
    return df_quarterly_results.to_dict()

@mcp.tool()
async def get_profit_loss(company_name: str) -> dict[str, Any]:
    """Fetch profit and loss statement for a company from Screener.in."""
    _, df_profit_loss, _, _, _, _, _ = await read_stock_info(company_name)
    return df_profit_loss.to_dict()

@mcp.tool()
async def get_balance_sheet(company_name: str) -> dict[str, Any]:
    """Fetch balance sheet for a company from Screener.in."""
    _, _, df_balance_sheet, _, _, _, _ = await read_stock_info(company_name)
    return df_balance_sheet.to_dict()


@mcp.tool()
async def get_cash_flow(company_name: str) -> dict[str, Any]:
    """Fetch cash flow statement for a company from Screener.in."""
    _, _, _, df_cash_flow, _, _, _ = await read_stock_info(company_name)
    return df_cash_flow.to_dict()


@mcp.tool()
async def get_ratios(company_name: str) -> dict[str, Any]:
    """Fetch financial ratios for a company from Screener.in."""
    _, _, _, _, df_ratios, _, _ = await read_stock_info(company_name)
    return df_ratios.to_dict()


@mcp.tool()
async def get_shareholding_pattern_quarterly(company_name: str) -> dict[str, Any]:
    """Fetch quarterly shareholding pattern for a company from Screener.in."""
    _, _, _, _, _, df_shareholding_pattern_quarterly, _ = await read_stock_info(company_name)
    return df_shareholding_pattern_quarterly.to_dict()


@mcp.tool()
async def get_shareholding_pattern_yearly(company_name: str) -> dict[str, Any]:
    """Fetch yearly shareholding pattern for a company from Screener.in."""
    _, _, _, _, _, _, df_shareholding_pattern_yearly = await read_stock_info(company_name)
    return df_shareholding_pattern_yearly.to_dict()


@mcp.tool()
async def get_company_details(company_name: str) -> str:
    """Fetch company details from Screener.in."""
    result = await make_screener_request(f"company/{company_name}/", req_type='get')
    if "error" in result:
        return f"Error fetching details for {company_name}: {result['error']}"
    try:
        html = result["response"].text
        soup = BeautifulSoup(html, 'html.parser')
        modal_content = soup.find('div', class_='sub show-more-box about')
        all_p = modal_content.find_all('p')
        about_section = "\n".join(p.get_text(strip=True) for p in all_p)
    except Exception:
        # logging.info(f"HTML response: {result['response'].text}")
        return f"Error in details json for {company_name} for result: {result}: {traceback.format_exc()}"

    # extract relevant info from details page in some way like using beautiful soap etc
    return about_section


# Resource: Fetch Explore page
# @mcp.resource("company://explore")
# async def get_explore_page() -> str:
#     """Fetch explore page from Screener.in."""
#     result = await make_screener_request(f"explore/")
#     if "error" in result:
#         return f"Error fetching details for explore page: {result['error']}"
#     # extract relevent infor from explore page in some way like using beautiful soap etc
#     return "True"


@mcp.tool()
async def get_screens_page(page: int = None) -> str:
    """Fetch screens page from Screener.in."""
    if page:
        result = await make_screener_request(f"screens/?page={page}")
    else:
        result = await make_screener_request(f"screens")
    if "error" in result:
        return f"Error fetching details for screens page: {result['error']}"
    try:
        html = result["response"].text
        soup = BeautifulSoup(html, 'html.parser')
        header_content = soup.find('div', class_='flex-row flex-space-between')
        body_content = header_content.find_next('ul').find_all('li')
        # logging.info(f"body_content: {body_content}")
        # return json of all li element text and href
        return json.dumps([{"text": li.get_text(strip=True), "href": SCREENER_API_BASE+li.a['href']} for li in body_content])
    except Exception:
        # logging.info(f"HTML response: {result['response'].text}")
        return f"Error in get_screen_page func for page {page}: {traceback.format_exc()}"

@mcp.tool()
async def get_price_info(symbol: str, query: str = "Price-DMA50-DMA200-Volume", days: int = 365, consolidated: bool = True) -> dict[str, Any]:
    """Fetch price and related information for a company from Screener.in."""
    params = {
        "q": query,
        "days": str(days),
        "consolidated": str(consolidated).lower(),
    }
    _, company_id = await get_warehouse_and_company_id(symbol)
    print(f"company_id: {company_id}")
    if not company_id:
        return {"error": f"Company ID not found for symbol: {symbol}"}
    result = await make_screener_request(f"api/company/{company_id}/chart/", params=params)
    if "error" in result:
        return {"error": f"Error fetching price info for company {company_id}: {result['error']}"}
    try:
        return result["response"].json()
    except Exception as e:
        logging.info(f"Error parsing JSON response: {str(e)}")
        return {"error": f"Error parsing JSON response for company {company_id}: {str(e)}"}

@mcp.tool()
async def calculate_moving_average(symbol: str) -> dict[str, Any]:
    """
    Generate stock recommendations based on price, DMA50, DMA200, and volume.

    Args:
        symbol: The ticker symbol to analyze.

    Returns:
        Dictionary with stock analysis and recommendation.
    """
    # Fetch price info
    price_data = await get_price_info(symbol)
    if "error" in price_data:
        return {"error": f"Failed to fetch price info for {symbol}: {price_data['error']}"}

    # Extract datasets
    datasets = {dataset["metric"]: dataset for dataset in price_data.get("datasets", [])}

    # Ensure required metrics are available
    required_metrics = ["Price", "DMA50", "DMA200", "Volume"]
    if not all(metric in datasets for metric in required_metrics):
        return {"error": f"Missing required metrics for {symbol}: {required_metrics}"}

    # Get latest values
    latest_price = float(datasets["Price"]["values"][-1][1])
    latest_dma50 = float(datasets["DMA50"]["values"][-1][1])
    latest_dma200 = float(datasets["DMA200"]["values"][-1][1])
    latest_volume = datasets["Volume"]["values"][-1][1]
    avg_volume = sum(v[1] for v in datasets["Volume"]["values"]) / len(datasets["Volume"]["values"])

    # Determine signal
    if latest_price > latest_dma50 > latest_dma200:
        signal = "BULLISH"
    elif latest_price < latest_dma50 < latest_dma200:
        signal = "BEARISH"
    else:
        signal = "NEUTRAL"

    # Volume analysis
    unusual_volume = latest_volume > 1.5 * avg_volume

    # Recommendation
    if signal == "BULLISH" and unusual_volume:
        recommendation = "STRONG BUY"
    elif signal == "BULLISH":
        recommendation = "BUY"
    elif signal == "BEARISH" and unusual_volume:
        recommendation = "STRONG SELL"
    elif signal == "BEARISH":
        recommendation = "SELL"
    else:
        recommendation = "HOLD"

    return {
        "symbol": symbol,
        "latest_price": latest_price,
        "latest_dma50": latest_dma50,
        "latest_dma200": latest_dma200,
        "latest_volume": latest_volume,
        "average_volume": avg_volume,
        "signal": signal,
        "unusual_volume": unusual_volume,
        "recommendation": recommendation,
        "analysis": f"""Stock Analysis for {symbol}:
Latest Price: {latest_price}
50 DMA: {latest_dma50}
200 DMA: {latest_dma200}
Signal: {signal}
Unusual Volume: {"Yes" if unusual_volume else "No"}
Recommendation: {recommendation}
"""
    }

@mcp.tool()
async def calculate_rsi(symbol: str, period: int = 14) -> dict[str, Any]:
    """
    Calculate Relative Strength Index (RSI) for a symbol.

    Args:
        symbol: The ticker symbol to analyze.
        period: RSI calculation period.

    Returns:
        Dictionary with RSI data and analysis.
    """
    # Fetch price info
    price_data = await get_price_info(symbol, query="Price", days=365)
    if "error" in price_data:
        return {"error": f"Failed to fetch price info for {symbol}: {price_data['error']}"}

    # Extract price data
    datasets = {dataset["metric"]: dataset for dataset in price_data.get("datasets", [])}
    if "Price" not in datasets:
        return {"error": f"Price data not available for {symbol}"}

    # Convert price values to a DataFrame
    price_values = datasets["Price"]["values"]
    df = pd.DataFrame(price_values, columns=["date", "close"])
    df["close"] = df["close"].astype(float)

    # Calculate price changes
    delta = df["close"].diff()

    # Create gain and loss series
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Calculate average gain and loss
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # Get latest RSI
    latest_rsi = rsi.iloc[-1]

    # Determine signal
    if latest_rsi < 30:
        signal = "OVERSOLD (Potential buy opportunity)"
    elif latest_rsi > 70:
        signal = "OVERBOUGHT (Potential sell opportunity)"
    else:
        signal = "NEUTRAL"

    return {
        "symbol": symbol,
        "period": period,
        "rsi": latest_rsi,
        "signal": signal,
        "analysis": f"""RSI Analysis for {symbol}:
            {period}-period RSI: {latest_rsi:.2f}
            Signal: {signal}
            
            Recommendation: {
                "BUY" if latest_rsi < 30 else
                "SELL" if latest_rsi > 70 else
                "HOLD"
            }"""
    }

@mcp.tool()
async def trade_recommendation(symbol: str) -> dict[str, Any]:
    """
    Provide a comprehensive trade recommendation based on multiple indicators.

    Args:
        symbol: The ticker symbol to analyze.

    Returns:
        Dictionary with trading recommendation and supporting data.
    """
    # Calculate individual indicators
    ma_data = await calculate_moving_average(symbol)
    rsi_data = await calculate_rsi(symbol)

    # Check for errors in the data
    if "error" in ma_data:
        return {"error": f"Error in moving average data: {ma_data['error']}"}
    if "error" in rsi_data:
        return {"error": f"Error in RSI data: {rsi_data['error']}"}

    # Extract signals
    ma_signal = ma_data["signal"]
    rsi_value = rsi_data["rsi"]
    rsi_signal = rsi_data["signal"]

    # Determine overall signal strength
    signal_strength = 0

    # MA contribution
    if "BULLISH" in ma_signal:
        signal_strength += 1
    elif "BEARISH" in ma_signal:
        signal_strength -= 1

    # RSI contribution
    if "OVERSOLD" in rsi_signal:
        signal_strength += 1.5
    elif "OVERBOUGHT" in rsi_signal:
        signal_strength -= 1.5

    # Determine final recommendation
    if signal_strength >= 2:
        recommendation = "STRONG BUY"
    elif signal_strength > 0:
        recommendation = "BUY"
    elif signal_strength <= -2:
        recommendation = "STRONG SELL"
    elif signal_strength < 0:
        recommendation = "SELL"
    else:
        recommendation = "HOLD"

    # Calculate risk level
    risk_level = "MEDIUM"
    if abs(signal_strength) > 3:
        risk_level = "LOW"  # Strong signal, lower risk
    elif abs(signal_strength) < 1:
        risk_level = "HIGH"  # Weak signal, higher risk

    analysis = f"""# Trading Recommendation for {symbol}

        ## Summary
        Recommendation: {recommendation}
        Risk Level: {risk_level}
        Signal Strength: {signal_strength:.1f} / 4.5
        
        ## Technical Indicators
        Moving Averages: {ma_signal}
        RSI ({rsi_data["period"]}): {rsi_value:.2f} - {rsi_signal}
        
        ## Reasoning
        This recommendation is based on a combination of Moving Average analysis and RSI indicators.
        {
            f"The RSI indicates the stock is {rsi_signal.split(' ')[0].lower()}. " if "NEUTRAL" not in rsi_signal else ""
        }
        
        ## Action Plan
        {
            "Consider immediate entry with a stop loss at the recent low. Target the next resistance level." if recommendation == "STRONG BUY" else
            "Look for a good entry point on small dips. Set reasonable stop loss." if recommendation == "BUY" else
            "Consider immediate exit or setting tight stop losses to protect gains." if recommendation == "STRONG SELL" else
            "Start reducing position on strength or set trailing stop losses." if recommendation == "SELL" else
            "Monitor the position but no immediate action needed."
        }
        """

    return {
        "symbol": symbol,
        "recommendation": recommendation,
        "risk_level": risk_level,
        "signal_strength": signal_strength,
        "ma_signal": ma_signal,
        "rsi_signal": rsi_signal,
        "current_price": ma_data["latest_price"],
        "analysis": analysis
    }

@mcp.prompt()
def analyze_ticker(symbol: str) -> str:
    """
    Analyze a ticker symbol for trading opportunities
    """
    return f"""You are a professional stock market analyst. I would like you to analyze the stock {symbol} and provide trading insights.

        Start by examining the current market data and technical indicators. Here are the specific tasks:
        
        1. First, check the current market data for {symbol}
        2. Calculate the moving averages using the calculate_moving_averages tool
        3. Calculate the RSI using the calculate_rsi tool
        4. Generate a comprehensive trade recommendation using the trade_recommendation tool
        5. Based on all this information, provide your professional analysis, highlighting:
           - The current market position
           - Key technical indicators and what they suggest
           - Potential trading opportunities and risks
           - Your recommended action (buy, sell, or hold) with a brief explanation
        
        Please organize your response in a clear, structured format suitable for a professional trader."""


@mcp.prompt()
def compare_tickers(symbols: str) -> str:
    """
    Compare multiple ticker symbols for the best trading opportunity

    Args:
        symbols: Comma-separated list of ticker symbols
    """
    symbol_list = [s.strip() for s in symbols.split(",")]
    symbol_section = "\n".join([f"- {s}" for s in symbol_list])

    return f"""You are a professional stock market analyst. I would like you to compare these stocks and identify the best trading opportunity:

        {symbol_section}
        
        For each stock in the list, please:
        
        1. Check the current market data using the appropriate resource
        2. Generate a comprehensive trade recommendation using the trade_recommendation tool
        3. Compare all stocks based on:
           - Current trend direction and strength
           - Technical indicator signals
           - Risk/reward profile
           - Trading recommendation strength
        
        After analyzing each stock, rank them from most promising to least promising trading opportunity. Explain your ranking criteria and why you believe the top-ranked stock represents the best current trading opportunity.
        
        Conclude with a specific recommendation on which stock to trade and what action to take (buy, sell, or hold)."""

@mcp.prompt()
def intraday_strategy_builder(symbol: str) -> str:
    """
    Build a custom intraday trading strategy for a specific ticker
    """
    return f"""You are an expert algorithmic trader specializing in intraday strategies. I want you to develop a custom intraday trading strategy for {symbol}.

        Please follow these steps:
        
        1. First, analyze the current market data for {symbol} using the market-data resource
        2. Calculate relevant technical indicators:
           - Moving averages (short and long periods)
           - RSI
        3. Based on your analysis, design an intraday trading strategy that includes:
           - Specific entry conditions (technical setups that would trigger a buy/sell)
           - Exit conditions (both take-profit and stop-loss levels)
           - Position sizing recommendations
           - Optimal trading times during the day
           - Risk management rules
        
        Make your strategy specific to the current market conditions for {symbol}, not just generic advice. Include exact indicator values and price levels where possible.
        
        Conclude with a summary of the strategy and how a trader should implement it for today's trading session."""

@mcp.prompt()
def swing_trading_strategy(symbol: str) -> str:
    """
    Develop a swing trading strategy for a specific ticker symbol.
    """
    return f"""You are a professional swing trader. I want you to create a swing trading strategy for the stock {symbol}.

    Please follow these steps:

    1. Analyze the current market data for {symbol}.
    2. Use technical indicators such as:
       - Moving averages (e.g., 50 DMA and 200 DMA)
       - RSI
       - Volume trends
    3. Identify key support and resistance levels.
    4. Develop a swing trading strategy that includes:
       - Entry conditions (e.g., breakouts, pullbacks, or trend reversals)
       - Exit conditions (e.g., profit targets and stop-loss levels)
       - Risk/reward ratio for trades
       - Position sizing recommendations
    5. Highlight potential risks and how to mitigate them.

    Conclude with a summary of the strategy and provide actionable recommendations for swing trading {symbol} in the current market conditions."""

# Run the server
if __name__ == "__main__":
    mcp.run()
