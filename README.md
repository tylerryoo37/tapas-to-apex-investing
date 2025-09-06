# Tapas to Apex Investing
## A Complete Stock Analysis and Portfolio Evaluation Workflow

This repository provides a systematic approach to stock screening, fundamental analysis, and portfolio evaluation using Python and financial data APIs. The workflow progresses from data extraction through analysis to portfolio performance measurement.

## 📋 Repository Structure

The project follows a numbered workflow structure for easy execution:

```
tapas-to-apex-investing/
├── 01_data_extraction_fundamentals.py    # Extract comprehensive stock metrics
├── 02_ticker_selection.ipynb             # Filter stocks by investment criteria  
├── 03_fundamentals_analysis.ipynb        # Analyze individual stock fundamentals
├── 04_quarterly_analysis_wip.ipynb       # Deep-dive quarterly analysis (WIP)
├── 05_portfolio_evaluation.py            # Comprehensive portfolio performance analysis
├── data/
│   ├── stock_data_current_20250906_012221.csv    # Raw extracted stock data
│   └── financial_data_for_analysis.csv           # Processed financial data
└── README.md
```

## 🚀 Workflow Overview

### Step 1: Data Extraction (`01_data_extraction_fundamentals.py`)
**Purpose**: Extract comprehensive fundamental metrics from Yahoo Finance for multiple stocks

**Key Features**:
- Fetches 40+ financial metrics per stock including P/E ratios, margins, cash flow, debt metrics
- Supports manual ticker selection or programmatic selection from S&P 500/NASDAQ-100
- Includes data quality checks and error handling
- Exports timestamped CSV files for analysis

**Key Metrics Extracted**:
- **Valuation**: P/E, P/B, P/S ratios, market cap, enterprise value
- **Profitability**: ROE, ROA, gross/operating/profit margins
- **Financial Health**: Current ratio, debt-to-equity, free cash flow, cash position
- **Growth**: Revenue growth (YoY and QoQ), analyst targets
- **Market Data**: 52-week range, beta, analyst recommendations

**Usage**:
```python
# Modify ticker list in the script
my_tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
# Run script to generate stock_data_current_[timestamp].csv
```

### Step 2: Stock Screening (`02_ticker_selection.ipynb`)
**Purpose**: Filter stocks using customizable investment criteria

**Key Features**:
- `filter_stocks_by_criteria()`: Multi-criteria filtering engine
- `get_good_pe_stocks()`: Quick P/E ratio screening
- `get_value_stocks()`: Comprehensive value investing screen
- Detailed filtering results with pass/fail breakdown

**Example Filters**:
- **Value Stocks**: P/E ≤ 15, P/B ≤ 3.3, ROE ≥ 12%, Current Ratio ≥ 1.2
- **Growth Stocks**: Revenue growth ≥ 20%, Operating margins improving
- **Quality Stocks**: Low debt-to-equity, positive free cash flow

### Step 3: Individual Analysis (`03_fundamentals_analysis.ipynb`)
**Purpose**: Deep-dive analysis of selected stocks with Claude Code integration

**Key Features**:
- `show_analysis_data()`: Formatted display for AI analysis
- Single-stock focus with comprehensive metrics view
- Ready for Claude Code MCP integration for automated analysis
- Traffic light indicators (🟢🟡🔴) for quick assessment

**Analysis Framework**:
1. Company overview (sector, industry, market cap)
2. Financial health dashboard with traffic light indicators
3. Valuation metrics analysis
4. Growth and profitability assessment
5. Investment recommendation with score (0-100)
6. Risk analysis and position sizing guidance

### Step 4: Quarterly Deep-Dive (`04_quarterly_analysis_wip.ipynb`)
**Purpose**: Quarterly financial statement analysis (Work in Progress)

**Current Features**:
- Quarterly data loading and preparation
- Historical trend analysis setup
- Seasonal pattern identification framework

### Step 5: Portfolio Evaluation (`05_portfolio_evaluation.py`)
**Purpose**: Comprehensive portfolio performance analysis and risk assessment

**Key Features**:
- **Performance Metrics**: Returns, volatility, Sharpe ratio, alpha, beta
- **Risk Analysis**: Individual stock analysis, correlation analysis
- **Benchmark Comparison**: Against SPY, QQQ, or custom benchmarks
- **Recent Performance**: 30-day rolling analysis
- **Individual Stock Breakdown**: Per-stock contribution analysis

**Core Capabilities**:
- Historical performance analysis (customizable date ranges)
- Alpha/beta calculation using two methods (mathematical and regression-based)
- Risk-adjusted returns using Treasury rates
- Portfolio optimization insights
- Statistical significance testing for alpha generation

**Usage Example**:
```python
tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
weights = [0.3, 0.25, 0.2, 0.15, 0.1]  # Must sum to 1.0
analyzer = PortfolioAnalyzer(tickers, weights, benchmark='SPY')
analyzer.fetch_data()
results = analyzer.generate_report()
```

## 🔧 Installation & Dependencies

```bash
pip install yfinance pandas numpy matplotlib statsmodels requests beautifulsoup4
```

**Required Libraries**:
- `yfinance`: Financial data extraction
- `pandas`: Data manipulation and analysis  
- `numpy`: Numerical computations
- `matplotlib`: Data visualization
- `statsmodels`: Statistical analysis and regression
- `requests`: Web scraping for index constituents

## 📊 Data Sources

- **Stock Data**: Yahoo Finance API via yfinance
- **Risk-Free Rate**: 3-Month Treasury Bill (^IRX)
- **Index Constituents**: Wikipedia (S&P 500, NASDAQ-100)
- **Benchmarks**: SPY (S&P 500 ETF), QQQ (NASDAQ-100 ETF)

## 💡 Usage Examples

### Quick Value Stock Screen
```python
# Run 01_data_extraction_fundamentals.py first
# Then in 02_ticker_selection.ipynb:
criteria = {
    'P/E Ratio TTM': {'max': 15, 'min': 1},
    'ROE TTM': {'min': 0.15},
    'Current Ratio MRQ': {'min': 1.5}
}
results = filter_stocks_by_criteria(df, criteria)
```

### Portfolio Analysis
```python
tickers = ['AAPL', 'MSFT', 'GOOGL']
weights = [0.4, 0.4, 0.2]
analyzer = PortfolioAnalyzer(tickers, weights)
analyzer.fetch_data()
analyzer.generate_report()
```

### Claude Code Integration
The notebooks are designed for seamless integration with Claude Code MCP:
1. Load data in notebook
2. Run `show_analysis_data(df, ticker, single_df)`
3. Ask Claude Code: "Analyze the stock in this notebook"

## 📈 Key Features

- **Comprehensive Screening**: 40+ financial metrics with customizable filters
- **Statistical Analysis**: Alpha/beta calculation, Sharpe ratios, statistical significance
- **Risk Assessment**: Volatility analysis, correlation studies, position sizing
- **Benchmarking**: Performance comparison against major indices
- **Data Quality**: Built-in validation, error handling, and warning systems
- **Flexible Analysis**: Support for individual stocks or portfolio-level analysis
- **Export Capabilities**: CSV outputs with timestamps for record keeping

## 🎯 Investment Philosophy

This toolkit supports multiple investment approaches:
- **Value Investing**: P/E, P/B screening with profitability filters
- **Growth Investing**: Revenue growth and margin expansion focus
- **Quality Investing**: Financial strength and competitive moat analysis
- **Portfolio Theory**: Risk-adjusted returns and efficient frontier concepts

## ⚠️ Disclaimers

- This tool is for educational and research purposes only
- Not financial advice - conduct your own due diligence
- Historical performance does not guarantee future results
- Market data may have delays or inaccuracies
- Always verify critical data points independently
- This is only a beta version, your contribution will be important to make this tool better!

## 🔮 Future Enhancements

- [ ] Complete quarterly analysis notebook
- [ ] Add macro/sector indicators to enhance analysis
- [ ] Add/modify value metrics (i.e., momentum) that could be useful for picking stocks
- [ ] Implement backtesting framework
- [ ] Add sector rotation analysis
- [ ] Create automated reporting dashboard

---

**Happy Investing! 📈**