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
from functools import lru_cache

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
async def make_screener_request(endpoint: str, req_type: str = "get") -> dict[str, Any] | None:
    async with httpx.AsyncClient() as client:
        try:
            response = None
            if req_type == "post":
                response = await client.post(f"{SCREENER_API_BASE}/{endpoint}", headers=headers, cookies=cookies, data=data)
            else:
                response = await client.get(f"{SCREENER_API_BASE}/{endpoint}", headers=headers)
            response.raise_for_status()
            return {"response": response}
        except Exception as e:
            logging.info(f"response: {type(response)}, {response}, {response.has_redirect_location}, {response.next_request}")
            logging.info(f"response.text: {response.text}")
            return {"error": str(e)}

# Helper function to get warehouse id for downloading excel report
async def get_warehouse_id(symbol):
    logging.info("Getting warehouse id: " + symbol)
    api = f"{SCREENER_API_BASE}/api/company/search/?q={symbol}"
    async with httpx.AsyncClient() as client:
        d = await client.get(api)
        j = json.loads(d.content)[0]
        html = await client.get('https://www.screener.in' + j['url'])
        results = re.findall('formaction=./user/company/export/(.*?)/.', html.text)
        return results[0]


@mcp.tool()
async def download_report(symbol: str) -> str:
    """Download excel report for a stock from Screener.in."""
    path = "./reports"
    warehouseid = await get_warehouse_id(symbol)
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

@lru_cache(maxsize=32)
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


# Run the server
if __name__ == "__main__":
    mcp.run()
