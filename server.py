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
async def make_screener_request(endpoint: str, type: str = "get") -> dict[str, Any] | None:
    async with httpx.AsyncClient() as client:
        try:
            response = None
            if type == "post":
                response = await client.post(f"{SCREENER_API_BASE}/{endpoint}", headers=headers, cookies=cookies, data=data)
            else:
                response = await client.get(f"{SCREENER_API_BASE}/{endpoint}", headers=headers)
            response.raise_for_status()
            return {"response": response}
        except Exception as e:
            logging.info(f"response: {type(response)}, {response}")
            logging.info(f"response.text: {response.text}")
            return {"error": str(e)}

# Scraping and downloading reports
async def download_report(symbol, PATH):
    warehouseid = await get_warehouse_id(symbol)
    url = f'{SCREENER_API_BASE}/user/company/export/{warehouseid}/'
    async with httpx.AsyncClient() as client:
        r = await client.post(url, cookies=cookies, headers=headers, data=data)
        logging.info(f"r.status_code: {r.status_code}")
        r.raise_for_status()
        path = f'{PATH}/{symbol.strip()}.xlsx'

        if r.status_code == 200:
            with open(path, 'wb') as f:
                f.write(r.content)
            logging.info(f"Excel file created for: {symbol}")

async def get_warehouse_id(symbol):
    logging.info("Getting warehouse id: " + symbol)
    api = f"{SCREENER_API_BASE}/api/company/search/?q={symbol}"
    async with httpx.AsyncClient() as client:
        d = await client.get(api)
        j = json.loads(d.content)[0]
        html = await client.get('https://www.screener.in' + j['url'])
        results = re.findall('formaction=./user/company/export/(.*?)/.', html.text)
        return results[0]

# New func to read html tables from a link using pandas
def read_stock_info(url):
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




# async def download_multiple_reports(symbols, PATH, delay):
#     for symbol in symbols:
#         download_report(symbol)
#         await asyncio.sleep(delay)


# # Resource: Fetch company details and download report
# @mcp.resource("company://{company_name}")
# async def get_company_details_and_report(company_name: str) -> str:
#     """Fetch company details and download report from Screener.in."""
#     details = await make_screener_request(f"companies/{company_name}/")
#     await scrape_and_download([company_name], './reports', 0)
#     if "error" in details:
#         return f"Error fetching details for {company_name}: {details['error']}"
#     return f"Company: {details['name']}nSector: {details['sector']}nMarket Cap: {details['market_cap']}"



# Resource: Fetch company details
@mcp.resource("company://{company_name}")
async def get_company_details(company_name: str) -> str:
    """Fetch company details from Screener.in."""
    result = await make_screener_request(f"company/{company_name}/", type='get')
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
@mcp.resource("company://explore")
async def get_explore_page() -> str:
    """Fetch explore page from Screener.in."""
    result = await make_screener_request(f"explore")
    if "error" in result:
        return f"Error fetching details for explore page: {result['error']}"
    # extract relevent infor from explore page in some way like using beautiful soap etc
    return "True"

# Resource: Fetch screens page
@mcp.resource("company://screens/{page}")
async def get_screens_page(page: str = None) -> str:
    """Fetch screens page from Screener.in."""
    if page:
        result = await make_screener_request(f"screens/?page={page}")
    else:
        result = await make_screener_request(f"screens")
    if "error" in result:
        return f"Error fetching details for screens page: {result['error']}"
    # extract relevent infor from screens page in some way like using beautiful soap etc
    return "True"




# def read_excel_sheets(file_path: str) -> dict[str, pd.DataFrame]:
#     """Read all sheets from an Excel file and return a dictionary of DataFrames."""
#     xls = pd.ExcelFile(file_path)
#     sheets = {sheet_name: xls.parse(sheet_name) for sheet_name in xls.sheet_names}
#     return sheets
#
# @mcp.tool()
# async def analyze_profit_and_loss(df: pd.DataFrame) -> str:
#     """Analyze the Profit and Loss DataFrame."""
#     # Perform analysis on the Profit and Loss data
#     net_profit_margin = df['Net Profit'] / df['Revenue'] * 100
#     suggestions = f"Net Profit Margin: {net_profit_margin.mean():.2f}%"
#     return suggestions
#
# @mcp.tool()
# async def analyze_quarters(df: pd.DataFrame) -> str:
#     """Analyze the Quarters DataFrame."""
#     # Perform analysis on the Quarters data
#     quarterly_growth = df['Revenue'].pct_change().mean() * 100
#     suggestions = f"Average Quarterly Growth: {quarterly_growth:.2f}%"
#     return suggestions
#
# @mcp.tool()
# async def analyze_balance_sheet(df: pd.DataFrame) -> str:
#     """Analyze the Balance Sheet DataFrame."""
#     # Perform analysis on the Balance Sheet data
#     debt_to_equity_ratio = df['Total Liabilities'] / df['Total Equity']
#     suggestions = f"Debt to Equity Ratio: {debt_to_equity_ratio.mean():.2f}"
#     return suggestions
#
# @mcp.tool()
# async def analyze_cash_flow(df: pd.DataFrame) -> str:
#     """Analyze the Cash Flow DataFrame."""
#     # Perform analysis on the Cash Flow data
#     free_cash_flow = df['Operating Cash Flow'] - df['Capital Expenditure']
#     suggestions = f"Free Cash Flow: {free_cash_flow.mean():.2f}"
#     return suggestions
#
# @mcp.tool()
# async def analyze_data_sheet(df: pd.DataFrame) -> str:
#     """Analyze the DataSheet DataFrame."""
#     # Perform analysis on the DataSheet data
#     key_metrics = df[['Metric1', 'Metric2', 'Metric3']].mean()
#     suggestions = f"Key Metrics: {key_metrics.to_dict()}"
#     return suggestions
#
# file_path = 'path/to/your/excel/file.xlsx'
# sheets = read_excel_sheets(file_path)
#
# # Example usage
# profit_and_loss_suggestions = await analyze_profit_and_loss(sheets['Profit and Loss'])
# quarters_suggestions = await analyze_quarters(sheets['Quarters'])
# balance_sheet_suggestions = await analyze_balance_sheet(sheets['Balance Sheet'])
# cash_flow_suggestions = await analyze_cash_flow(sheets['Cash Flow'])
# data_sheet_suggestions = await analyze_data_sheet(sheets['DataSheet'])



# # Resource: Fetch screens page
# @mcp.resource("company://{company_name}")
# async def get_company_details(company_name: str) -> str:
#     """Fetch company details from Screener.in."""
#     data = await make_screener_request(f"companies/{company_name}/")
#     if "error" in data:
#         return f"Error fetching details for {company_name}: {data['error']}"
#     return f"Company: {data['name']}\nSector: {data['sector']}\nMarket Cap: {data['market_cap']}"

# # Tool: Fetch financial ratios
# @mcp.tool()
# async def fetch_ratios(company_name: str) -> dict:
#     """Fetch financial ratios for a company."""
#     data = await make_screener_request(f"companies/{company_name}/ratios/")
#     if "error" in data:
#         return {"error": f"Error fetching ratios for {company_name}: {data['error']}"}
#     return {
#         "PE Ratio": data.get("pe_ratio"),
#         "Debt to Equity": data.get("debt_to_equity"),
#         "Return on Equity": data.get("return_on_equity"),
#     }

# # Tool: Download financial report
# @mcp.tool()
# async def download_report(company_name: str) -> str:
#     """Download the financial report for a company."""
#     "user/company/export/{}/"
#     data = await make_screener_request(f"user/company/export/{warehouseid}/")
#     if "error" in data:
#         return f"Error fetching report for {company_name}: {data['error']}"
#     # Save the report locally
#     report_path = f"{company_name}_report.pdf"
#     with open(report_path, "wb") as f:
#         f.write(data["report"])
#     return f"Report saved as {report_path}"

# Prompt: Analyze company financials
@mcp.prompt()
def analyze_financials(company_name: str) -> str:
    return f"Analyze the financial health of {company_name}. Include key ratios and recent performance."

# Run the server
if __name__ == "__main__":
    mcp.run()
