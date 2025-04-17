import time
import random
import asyncio
import logging
from server import (download_report, get_warehouse_and_company_id, get_company_details, get_screens_page,
                    read_stock_info)
from server import (
    get_quarterly_results,
    get_profit_loss,
    get_balance_sheet,
    get_cash_flow,
    get_ratios,
    get_shareholding_pattern_quarterly,
    get_shareholding_pattern_yearly,
    get_price_info
)

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_download_report():
    symbol = "WIPRO"
    await download_report(symbol)

async def test_get_warehouse_and_company_id():
    symbol = "WIPRO"
    warehouse_id, company_id = await get_warehouse_and_company_id(symbol)
    print(f"Warehouse and Company ID for {symbol}: {warehouse_id}, {company_id}")

async def test_get_company_details():
    company_name = "WIPRO"
    details = await get_company_details(company_name)
    print(f"Company details for {company_name}: {details}")

# async def test_get_explore_page():
#     explore_page = await get_explore_page()
#     print(f"Explore page details: {explore_page}")

async def test_get_screens_page(page="1"):
    screens_page = await get_screens_page(page)
    print(f"Screens page details for page {page}: {screens_page}")

# def test_read_stock_info():
#     url = "WIPRO"
#     df1, df2, df3, df4, df5, df6, df = read_stock_info(url)
#     print(df.head())
#     print(df.tail())
#     print(df.columns)
#     print(df.index)
#     print(df.shape)

# add new unit test of all remaining functions after and including get_quarterly_results
async def test_get_quarterly_results():
    company_name = "WIPRO"
    results = await get_quarterly_results(company_name)
    print(f"Quarterly Results for {company_name}: {results}")

async def test_get_profit_loss():
    company_name = "WIPRO"
    results = await get_profit_loss(company_name)
    print(f"Profit & Loss for {company_name}: {results}")

async def test_get_balance_sheet():
    company_name = "WIPRO"
    results = await get_balance_sheet(company_name)
    print(f"Balance Sheet for {company_name}: {results}")

async def test_get_cash_flow():
    company_name = "WIPRO"
    results = await get_cash_flow(company_name)
    print(f"Cash Flow for {company_name}: {results}")

async def test_get_ratios():
    company_name = "WIPRO"
    results = await get_ratios(company_name)
    print(f"Ratios for {company_name}: {results}")

async def test_get_shareholding_pattern_quarterly():
    company_name = "WIPRO"
    results = await get_shareholding_pattern_quarterly(company_name)
    print(f"Quarterly Shareholding Pattern for {company_name}: {results}")

async def test_get_shareholding_pattern_yearly():
    company_name = "WIPRO"
    results = await get_shareholding_pattern_yearly(company_name)
    print(f"Yearly Shareholding Pattern for {company_name}: {results}")

async def test_get_price_info():
    symbol = "TCS"
    query = "Price-DMA50-DMA200-Volume"
    days= 365
    consolidated= True
    results = await get_price_info(symbol, query, days, consolidated)
    print(f"Price Info for {symbol}: {results}")

if __name__ == "__main__":
    # asyncio.run(test_download_report())
    # time.sleep(random.randint(1, 5))
    #
    # asyncio.run(test_get_warehouse_and_company_id())
    # time.sleep(random.randint(1, 5))
    #
    # asyncio.run(test_get_company_details())
    # time.sleep(random.randint(1, 5))
    #
    # # test_read_stock_info()
    # asyncio.run(test_get_quarterly_results())
    # asyncio.run(test_get_profit_loss())
    # asyncio.run(test_get_balance_sheet())
    # asyncio.run(test_get_cash_flow())
    # asyncio.run(test_get_ratios())
    # asyncio.run(test_get_shareholding_pattern_quarterly())
    # asyncio.run(test_get_shareholding_pattern_yearly())
    # time.sleep(random.randint(1, 5))
    #
    # # asyncio.run(test_get_explore_page())
    # # time.sleep(random.randint(1, 5))
    #
    # asyncio.run(test_get_screens_page(page="1"))
    # time.sleep(random.randint(1, 5))

    asyncio.run(test_get_price_info())