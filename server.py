from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("Screener Server")

# Define Screener.in API base URL and headers
SCREENER_API_BASE = "https://www.screener.in/api/v1"
HEADERS = {
    "Authorization": "Token YOUR_API_TOKEN",  # Replace with your Screener.in API token
    "User-Agent": "ScreenerMCP/1.0",
}

# Helper function to make API requests
async def make_screener_request(endpoint: str, params: dict = None) -> dict[str, Any] | None:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SCREENER_API_BASE}/{endpoint}", headers=HEADERS, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

# Resource: Fetch company details
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
    data = await make_screener_request(f"companies/{company_name}/report/")
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
