import time
import random
import asyncio
import logging
from server import (download_report, get_warehouse_id, get_company_details, get_explore_page, get_screens_page,
                    read_stock_info)

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_download_report():
    symbol = "WIPRO"
    await download_report(symbol)

async def test_get_warehouse_id():
    symbol = "WIPRO"
    warehouse_id = await get_warehouse_id(symbol)
    print(f"Warehouse ID for {symbol}: {warehouse_id}")

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


def test_read_stock_info():
    url = "WIPRO"
    df1, df2, df3, df4, df5, df6, df = read_stock_info(url)
    print(df.head())
    print(df.tail())
    print(df.columns)
    print(df.index)
    print(df.shape)

if __name__ == "__main__":
    # asyncio.run(test_download_report())
    # time.sleep(random.randint(1, 5))

    # asyncio.run(test_get_warehouse_id())
    # time.sleep(random.randint(1, 5))

    # asyncio.run(test_get_company_details())
    # time.sleep(random.randint(1, 5))

    # test_read_stock_info()

    # asyncio.run(test_get_explore_page())
    # time.sleep(random.randint(1, 5))
    #
    asyncio.run(test_get_screens_page(page="1"))