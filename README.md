# MCP Server for Screener.in
## Overview
This repository provides an open-source implementation of an MCP (Market Capitalization to Profit) server that integrates with screener.in. The server is designed to fetch, process, and serve financial data, enabling users to calculate and analyze the MCP ratio for companies listed on screener.in.

The MCP ratio is a crucial metric for evaluating a company's valuation relative to its profitability. This project is aimed at empowering developers, analysts, and financial enthusiasts with an easy-to-use and customizable tool for financial data analysis.

## Features
- Fetches financial data from screener.in.
- Calculates the Market Capitalization to Profit (MCP) ratio.
- Provides an API endpoint for serving MCP data.
- Open-source and customizable for additional financial metrics.
- Lightweight and easy to deploy on local or cloud servers.

## Prerequisites
- Python 3.8+
- Flask or any other web framework (if applicable).
- API credentials or access to screener.in (if required).
- Basic knowledge of financial metrics and their significance.

## Installation
- Clone the repository:
```
git clone https://github.com/yourusername/mcp-server-screener.git
cd mcp-server-screener
```
- Install the required dependencies:
```
pip install -r requirements.txt
```
- Set up environment variables for screener.in API credentials (if applicable):
```
export SCREENER_API_KEY="your_api_key"
export SCREENER_API_SECRET="your_api_secret"
```
- Run the server:
```
python app.py
```
- Access the server at **http://localhost:5000** (or the configured port).

## Usage
### API Endpoints
- GET /mcp
    Fetches the MCP ratio for a given company.
    - Parameters:
        - symbol: The stock symbol of the company (e.g., RELIANCE, TCS).
- Example Request:
```
curl http://localhost:5000/mcp?symbol=RELIANCE
```
Example Response:
```
{
  "symbol": "RELIANCE",
  "market_cap": 1500000000000,
  "profit": 50000000000,
  "mcp_ratio": 30
}
```

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
