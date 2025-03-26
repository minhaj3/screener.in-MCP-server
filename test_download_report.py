import asyncio
import logging
from server import download_report

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_download_report():
    symbol = "WIPRO"
    path = "./reports"
    await download_report(symbol, path)

if __name__ == "__main__":
    asyncio.run(test_download_report())