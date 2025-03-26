import time
import random
import asyncio
import logging
from server import (download_report, get_warehouse_id, get_company_details, get_explore_page, get_screens_page,
                    convert_excel_sheet_to_dataframe, read_excel_sheets)

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_download_report():
    symbol = "WIPRO"
    path = "./reports"
    await download_report(symbol, path)

async def test_get_warehouse_id():
    symbol = "WIPRO"
    warehouse_id = await get_warehouse_id(symbol)
    print(f"Warehouse ID for {symbol}: {warehouse_id}")

async def test_get_company_details():
    company_name = "WIPRO"
    details = await get_company_details(company_name)
    print(f"Company details for {company_name}: {details}")

async def test_get_explore_page():
    explore_page = await get_explore_page()
    print(f"Explore page details: {explore_page}")

async def test_get_screens_page():
    page = "1"
    screens_page = await get_screens_page(page)
    print(f"Screens page details for page {page}: {screens_page}")

def test_convert_excel_sheet_to_dataframe():
    file_path = "reports/WIPRO.xlsx"
    sheet_name = "Profit & Loss"
    df = convert_excel_sheet_to_dataframe(file_path, sheet_name, skiprows=3)
    print(df.columns)
    print(df.index)
    print(df)

def test_read_excel_sheets():
    file_path = "reports/WIPRO.xlsx"
    sheets = read_excel_sheets(file_path)
    print(sheets)

if __name__ == "__main__":
    # asyncio.run(test_download_report())
    # time.sleep(random.randint(1, 5))

    # asyncio.run(test_get_warehouse_id())
    # time.sleep(random.randint(1, 5))

    # asyncio.run(test_get_company_details())
    # time.sleep(random.randint(1, 5))

    test_convert_excel_sheet_to_dataframe()

    # asyncio.run(test_get_explore_page())
    # time.sleep(random.randint(1, 5))
    #
    # asyncio.run(test_get_screens_page())