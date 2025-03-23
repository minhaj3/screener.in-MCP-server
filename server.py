from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("Screener.in Server")

# Define Screener.in API base URL and headers
SCREENER_API_BASE = "https://www.screener.in/"
SCREENER_CSRF_TOKEN = ""
SCREENER_SESSION_ID = ""
SCREENER_CSRF_MIDDLEWARE_TOKEN = ""
cookies = {
    'theme': 'auto',
    'csrftoken': SCREENER_CSRF_TOKEN,
    'sessionid': SCREENER_SESSION_ID,
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'max-age=0',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://www.screener.in',
    'priority': 'u=0, i',
    'referer': 'https://www.screener.in/company/WIPRO/consolidated/',
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
# async def make_screener_request(endpoint: str, params: dict = None) -> dict[str, Any] | None:
#     async with httpx.AsyncClient() as client:
#         try:
#             response = await client.post(f"{SCREENER_API_BASE}/{endpoint}", cookies=cookies, headers=headers, data=data)
#             response.raise_for_status()
#             return response.json()
#         except Exception as e:
#             return {"error": str(e)}

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


async def download_multiple_reports(symbols, PATH, delay):
    for symbol in symbols:
        download_report(symbol)
        await asyncio.sleep(delay)


# Resource: Fetch company details and download report
@mcp.resource("company://{company_name}")
async def get_company_details_and_report(company_name: str) -> str:
    """Fetch company details and download report from Screener.in."""
    details = await make_screener_request(f"companies/{company_name}/")
    await scrape_and_download([company_name], './reports', 0)
    if "error" in details:
        return f"Error fetching details for {company_name}: {details['error']}"
    return f"Company: {details['name']}nSector: {details['sector']}nMarket Cap: {details['market_cap']}"



# Resource: Fetch company details
@mcp.resource("company://{company_name}")
async def get_company_details(company_name: str) -> str:
    """Fetch company details from Screener.in."""
    data = await make_screener_request(f"companies/{company_name}/")
    if "error" in data:
        return f"Error fetching details for {company_name}: {data['error']}"
    return f"Company: {data['name']}\nSector: {data['sector']}\nMarket Cap: {data['market_cap']}"


# Resource: Fetch Explore page
@mcp.resource("company://{company_name}")
async def get_company_details(company_name: str) -> str:
    """Fetch company details from Screener.in."""
    data = await make_screener_request(f"companies/{company_name}/")
    if "error" in data:
        return f"Error fetching details for {company_name}: {data['error']}"
    return f"Company: {data['name']}\nSector: {data['sector']}\nMarket Cap: {data['market_cap']}"


# Resource: Fetch screens page
@mcp.resource("company://{company_name}")
async def get_company_details(company_name: str) -> str:
    """Fetch company details from Screener.in."""
    data = await make_screener_request(f"companies/{company_name}/")
    if "error" in data:
        return f"Error fetching details for {company_name}: {data['error']}"
    return f"Company: {data['name']}\nSector: {data['sector']}\nMarket Cap: {data['market_cap']}"

# Tool: Fetch financial ratios
@mcp.tool()
async def fetch_ratios(company_name: str) -> dict:
    """Fetch financial ratios for a company."""
    data = await make_screener_request(f"companies/{company_name}/ratios/")
    if "error" in data:
        return {"error": f"Error fetching ratios for {company_name}: {data['error']}"}
    return {
        "PE Ratio": data.get("pe_ratio"),
        "Debt to Equity": data.get("debt_to_equity"),
        "Return on Equity": data.get("return_on_equity"),
    }

# Tool: Download financial report
@mcp.tool()
async def download_report(company_name: str) -> str:
    """Download the financial report for a company."""
    "user/company/export/{}/"
    data = await make_screener_request(f"user/company/export/{warehouseid}/")
    if "error" in data:
        return f"Error fetching report for {company_name}: {data['error']}"
    # Save the report locally
    report_path = f"{company_name}_report.pdf"
    with open(report_path, "wb") as f:
        f.write(data["report"])
    return f"Report saved as {report_path}"

# Prompt: Analyze company financials
@mcp.prompt()
def analyze_financials(company_name: str) -> str:
    return f"Analyze the financial health of {company_name}. Include key ratios and recent performance."

# Run the server
if __name__ == "__main__":
    mcp.run()
