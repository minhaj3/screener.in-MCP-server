# MCP Server for Screener.in

## Overview
This repository provides an open-source implementation of an MCP (Market Capitalization to Profit) server that integrates with screener.in. The server is designed to fetch, process, and serve financial data, enabling users to calculate and analyze the MCP ratio for companies listed on screener.in.

The MCP ratio is a crucial metric for evaluating a company's valuation relative to its profitability. This project is aimed at empowering developers, analysts, and financial enthusiasts with an easy-to-use and customizable tool for financial data analysis.

## Features
- Fetches financial data from screener.in.
- Calculates the Market Capitalization to Profit (MCP) ratio.
- Provides tools for technical analysis, including:
  - Moving Average (MA) analysis.
  - Relative Strength Index (RSI) calculation.
  - Comprehensive trade recommendations.
  - Swing trading and intraday strategy prompts.
- Open-source and customizable for additional financial metrics.
- Lightweight and easy to deploy on local or cloud servers.

## Prerequisites
- Python 3.8+
- MCP Inspector CLI tool.
- Access to middleware token from screener.in.
- Basic knowledge of financial metrics and their significance.

## Installation
1. Clone the repository:
```
git clone https://github.com/yourusername/mcp-server-screener.git
cd mcp-server-screener
```
2. Create and activate a virtual environment:
```
python -m venv venv 
source venv/bin/activate # On macOS/Linux 
venv\Scripts\activate # On Windows
```
3. Install the required dependencies:
```
pip install -r requirements.txt
```
4. Set up environment variables for screener.in in .env file:
```
SCREENER_CSRF_TOKEN=''
SCREENER_SESSION_ID=''
SCREENER_CSRF_MIDDLEWARE_TOKEN=''
```
5. Test the server with MCP Inspector:
```
mcp dev server.py
```
6. Access the server at **http://localhost:6274** (or the configured port).

## Usage
### API Endpoints
- **GET /mcp**  
  Fetches the MCP ratio for a given company.  
  - **Parameters**:
    - `symbol`: The stock symbol of the company (e.g., RELIANCE, TCS).  
  - **Example Request**:
    ```
    curl http://localhost:5000/mcp?symbol=RELIANCE
    ```
  - **Example Response**:
    ```json
    {
      "symbol": "RELIANCE",
      "market_cap": 1500000000000,
      "profit": 50000000000,
      "mcp_ratio": 30
    }
    ```

### Tools
The MCP server includes the following tools for technical analysis and trading strategies:
1. **Moving Average Analysis**:
   - Calculates short and long moving averages.
   - Provides signals like bullish, bearish, and crossover detection.

2. **RSI Calculation**:
   - Computes the Relative Strength Index (RSI) for a stock.
   - Identifies oversold and overbought conditions.

3. **Trade Recommendations**:
   - Combines MA and RSI signals to generate actionable trading recommendations.
   - Includes risk level and signal strength.

4. **Swing Trading Strategy**:
   - Generates a swing trading strategy based on technical indicators, support/resistance levels, and volume trends.

5. **Intraday Strategy Builder**:
   - Creates a custom intraday trading strategy with entry/exit conditions, position sizing, and risk management.

6. **Ticker Analysis**:
   - Provides a detailed analysis of a stock using MA, RSI, and trade recommendations.

7. **Ticker Comparison**:
   - Compares multiple stocks to identify the best trading opportunity.


## Customization
You can modify the logic in mcp_calculator.py to include additional metrics or customize the MCP calculation.

## Contributing
Contributions are welcome! To contribute:
- Fork the repository.
- Create a new branch for your feature or bug fix.
- Submit a pull request with a detailed explanation of your changes.

## License
This project is licensed under the MIT License.

## Contact
For questions or suggestions, feel free to reach out:
- Email: minhajuddin3@gmail.com
- GitHub Issues: Open an issue

## Acknowledgments
- screener.in for providing a robust platform for financial data.
- The open-source community for their support and contributions.
