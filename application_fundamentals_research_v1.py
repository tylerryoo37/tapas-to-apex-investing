import yfinance as yf
import pandas as pd
from datetime import datetime
import time

def get_stock_metrics(tickers):
    """
    Get key financial metrics for a list of stock tickers
    Returns DataFrame with metrics as rows, tickers as columns
    
    FIXED VERSION - No custom sessions, let yfinance handle it
    """
    all_stock_data = {}
    
    for ticker in tickers:
        try:
            print(f"🔍 Fetching data for {ticker}...")
            
            # Simple ticker creation - let yfinance handle sessions
            stock = yf.Ticker(ticker)
            
            # Get basic info
            info = stock.info
            q_info = stock.quarterly_financials
            
            # Get recent price for current data
            recent_data = stock.history(period="5d")
            current_price = recent_data['Close'].iloc[-1] if not recent_data.empty else info.get('currentPrice', 'N/A')
            
            # Get cash flow data 
            free_cash_flow_row = stock.quarterly_cashflow.loc['Free Cash Flow'] 
            ttm_fcf = free_cash_flow_row.dropna().head(4).sum() if 'Free Cash Flow' in stock.quarterly_cashflow.index else 'N/A'
            free_cash_flow_row_year = stock.cashflow.loc['Free Cash Flow'] if 'Free Cash Flow' in stock.quarterly_cashflow.index else 'N/A'
            recent_fcf = free_cash_flow_row_year.dropna().iloc[0]
            
            # Get Ebitda data
            ttm_ebitda = q_info.loc['EBITDA'].dropna().head(4).sum() if 'EBITDA' in q_info.index else 'N/A'
            
            # Get Operating Margin
            ttm_op_income = q_info.loc['Operating Income'].dropna().head(4).sum() if 'Operating Income' in q_info.index else 'N/A'
            ttm_total_revenue = q_info.loc['Total Revenue'].dropna().head(4).sum() if 'Total Revenue' in q_info.index else 'N/A'
            ttm_operating_margin = ttm_op_income / ttm_total_revenue if ttm_total_revenue > 0 else 'N/A'
            
            # Get Quarterly Revenue Growth
            revenue_quarters = q_info.loc['Total Revenue'].dropna().head(2) if 'Total Revenue' in q_info.index else 'N/A'
            quarterly_revenue_growth = ((revenue_quarters.iloc[0] - revenue_quarters.iloc[1]) / revenue_quarters.iloc[1]) if len(revenue_quarters) == 2 and revenue_quarters.iloc[1] != 0 else 'N/A'
            
            # Get Gross Margin
            ttm_gross_profit = q_info.loc['Gross Profit'].dropna().head(4).sum() if 'Gross Profit' in q_info.index else 'N/A'
            ttm_total_revenue = q_info.loc['Total Revenue'].dropna().head(4).sum() if 'Total Revenue' in q_info.index else 'N/A'
            ttm_gross_margin = ttm_gross_profit / ttm_total_revenue if ttm_total_revenue > 0 else 'N/A'

            # Get Profit Margin
            ttm_net_income = q_info.loc['Net Income'].dropna().head(4).sum() if 'Net Income' in q_info.index else 'N/A'
            ttm_profit_margin = ttm_net_income / ttm_total_revenue if ttm_total_revenue > 0 else 'N/A'
            
            # Try to get quarterly data for more recent metrics
            try:
                quarterly_financials = stock.quarterly_financials
                quarterly_balance_sheet = stock.quarterly_balance_sheet
            except:
                quarterly_financials = pd.DataFrame()
                quarterly_balance_sheet = pd.DataFrame()
            
            # Extract key metrics with fallbacks
            metrics = {
                'Company Name': info.get('longName', 'N/A'),
                'Last Updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
                
                # BUSINESS INFO
                'Ticker': ticker,
                'Sector': info.get('sector', 'N/A'),
                'Industry': info.get('industry', 'N/A'),
                'Business Summary': info.get('longBusinessSummary', 'N/A') if info.get('longBusinessSummary') else 'N/A',
                
                # CURRENT METRICS
                'Current Price': round(current_price, 2) if current_price != 'N/A' else info.get('currentPrice', 'N/A'),
                'Current Market Cap': info.get('marketCap', 'N/A'), # Total market value of the company's outstanding shares
                'P/E Ratio TTM': info.get('trailingPE', 'N/A'), # Current Stock Price / Earnings Per Share (last 12 months): how many years it would take to get your money back based on last year's profit
                'P/E Ratio LFQ (Calculated)': current_price / (ttm_net_income / info.get('sharesOutstanding', 1)) if ttm_net_income > 0 else 'N/A', # Current Stock Price / Earnings Per Share (last 4 quarters): how many years it would take to get your money back based on last year's profit
                'Forward P/E': info.get('forwardPE', 'N/A'),  # Current Stock Price / Projected Earnings Per Share (next 12 months): how many years it would take based on what you THINK it will make next year
                'Current P/B Ratio': info.get('priceToBook', 'N/A'), # how much investors are paying relative to a company's book value (net worth on the balance sheet)
                'Current Ratio MRQ': info.get('currentRatio', 'N/A'), # Current Assets / Current Liabilities: how easily a company can pay its short-term obligations
                'Debt to Equity MRQ': info.get('debtToEquity', 'N/A'), # Total Debt / Shareholder's Equity: how much debt a company has compared to its equity
                'ROE TTM': info.get('returnOnEquity', 'N/A'),  # Return on Equity: how efficiently a company uses shareholder equity to generate profit
                'Revenue Growth YOY': info.get('revenueGrowth', 'N/A'), # Year-over-year revenue growth: how much a company's revenue has increased compared to the same quarter last year
                'Quarterly Revenue Growth (Calculated)': quarterly_revenue_growth,  # Quarterly revenue growth: how much a company's revenue has increased compared to the previous quarter
                
                # VALUATION METRICS
                'P/FCF TTM (Calculated)': info.get('marketCap', 'N/A') / recent_fcf if recent_fcf > 0 else 'N/A', # Price / Free Cash Flow: how much investors are paying for each dollar of free cash flow
                'P/FCF LFQ (Calculated)': info.get('marketCap', 'N/A') / ttm_fcf if ttm_fcf > 0 else 'N/A', # Price / Free Cash Flow: how much investors are paying for each dollar of free cash flow
                'TEV/EBITDA LFQ (Calculated)': info.get('enterpriseValue', 'N/A') / ttm_ebitda if ttm_ebitda > 0 else 'N/A', # Total Enterprise Value / Earnings Before Interest, Taxes, Depreciation, and Amortization: how much investors are paying for each dollar of EBITDA
                'Operating Margin MRQ': info.get('operatingMargins', 'N/A'), # Operating Income / Revenue: how much profit a company makes from its operations before interest and taxes
                'Operating Margin LFQ (Calculated)': ttm_operating_margin,
                'Gross Margin': info.get('grossMargins', 'N/A'), # Gross Profit / Revenue: how much profit a company makes after deducting the cost of goods sold
                'Gross Margin LFQ (Calculated)': ttm_gross_margin, # Gross Profit / Revenue: how much profit a company makes after deducting the cost of goods sold
                'Profit Margin': info.get('profitMargins', 'N/A'), # Net Income / Revenue: how much profit a company makes after all expenses, taxes, and interest
                'Profit Margin LFQ (Calculated)': ttm_profit_margin, # Net Income / Revenue: how much profit a company makes after all expenses, taxes, and interest
                
                # FINANCIAL HEALTH
                'Free Cash Flow LFQ (Calculated)': "; ".join([f"{date}: ${value/1e6:.0f}M" for date, value in free_cash_flow_row.dropna().head(4).items()]), # Free Cash Flow: cash generated after capital expenditures, available for distribution to investors
                'Total Cash MRQ': format_scale(info.get('totalCash', 'N/A')), # Total Cash: cash and cash equivalents on the balance sheet
                'Total Debt MRQ': format_scale(info.get('totalDebt', 'N/A')), # Total Debt: total interest-bearing debt on the balance sheet
                
                # ADDITIONAL METRICS  
                'P/S Ratio TTM': info.get('priceToSalesTrailing12Months', 'N/A'), # Price / Sales: how much investors are paying for each dollar of sales
                'ROA': info.get('returnOnAssets', 'N/A'), # Return on Assets: how efficiently a company uses its assets to generate profit
                'EPS TTM': info.get('trailingEps', 'N/A'), # Earnings Per Share: how much profit a company makes per share of stock
                'Dividend Yield': info.get('dividendYield', 'N/A'), # Dividend Yield: annual dividend payment divided by stock price, expressed as a percentage
                'Shares Outstanding': info.get('sharesOutstanding', 'N/A'), # total number of shares of stock currently held by all shareholders
                
                # ANALYST DATA
                'Target Price': info.get('targetMeanPrice', 'N/A'), # Average target price set by analysts
                'Recommendation': info.get('recommendationMean', 'N/A'), # Average recommendation score from analysts (1-5 scale)
                
                # TRADING DATA
                '52W High': info.get('fiftyTwoWeekHigh', 'N/A'),
                '52W Low': info.get('fiftyTwoWeekLow', 'N/A'),
                'Beta': info.get('beta', 'N/A'), # measure of stock volatility compared to the market
            }
            
            all_stock_data[ticker] = metrics
            print(f"✅ Successfully pulled data for {ticker}")
            
            # Small delay to be respectful to API
            time.sleep(0.3)
            
        except Exception as e:
            print(f"❌ Error pulling data for {ticker}: {str(e)}")
            all_stock_data[ticker] = {
                'Error': str(e),
                'Last Updated': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
    
    # Create DataFrame with metrics as rows and tickers as columns
    df = pd.DataFrame(all_stock_data)
    
    return df

# Functions Used

def format_scale(value):
    """
    Format currency values with appropriate scale (K/M/B/T)
    
    Parameters:
    value: float, int, or string - The value to format
    
    Returns:
    str: Formatted currency string (e.g., "$1.7B", "$15.5M", "N/A")
    """
    if value == 'N/A' or value is None:
        return 'N/A'
    
    try:
        value = float(value)
    except (ValueError, TypeError):
        return 'N/A'
    
    if value >= 1e12:  # Trillions
        return f"${value/1e12:.3f}T"
    elif value >= 1e9:  # Billions
        return f"${value/1e9:.3f}B"
    elif value >= 1e6:  # Millions
        return f"${value/1e6:.3f}M"
    elif value >= 1e3:  # Thousands
        return f"${value/1e3:.3f}K"
    else:
        return f"${value:.0f}"


def check_data_quality(df):
    """
    Quick data quality checks
    """
    warnings = []
    
    for ticker in df.columns:
        if 'Error' in df[ticker].index:
            error_value = df[ticker]['Error']
            if error_value is not None and str(error_value) not in ['', 'nan', 'None']:
                warnings.append(f"⚠️  {ticker}: Failed to fetch data")
                continue
            
        # Check for suspicious values
        pe_ratio = df.loc['P/E Ratio TTM', ticker] if 'P/E Ratio TTM' in df.index else 'N/A'
        if pe_ratio != 'N/A' and isinstance(pe_ratio, (int, float)) and pe_ratio > 500:
            warnings.append(f"⚠️  {ticker}: Unusual P/E ratio ({pe_ratio}) - check data")
        
        market_cap = df.loc['Current Market Cap', ticker] if 'Current Market Cap' in df.index else 'N/A'
        if market_cap == 'N/A':
            warnings.append(f"⚠️  {ticker}: Missing market cap data")
    
    return warnings

# SIMPLE USAGE
if __name__ == "__main__":
    # Your ticker list
    my_tickers = ['SSYS', 'BE', 'SLDP', 'NVAX', 'NBIS', 'VVX', 'ARDX', 'CELH', 'ANET', 'AEHR', 'APP', 
                  'PLTR', 'META', 'CTRE', 'BLDP', 'AAPL', 'AVGO', 'AUDC', 'CRSP', 'MRVL', 'VRT', 'NVDA', 
                  'PL', 'WMT', 'OXY', 'SGML', 'UNH', 'LQDT', 'MDT', 'ORCL', 'MSFT', 'TSLA', 'COST', 'MRK', 
                  'BLNK', 'NXP', 'BNTX', 'QBTS', 'RGTI', 'ABT', 'SIRI', 'CCJ', 'ASML', 'ADBE', 'PYPL', 
                  'SNOW', 'CHYM', 'RKLB', 'IONQ', 'ASTS', 'NOW', 'AISP', 'MRNA', 'CHGG', 'BBAI', 'QUBT', 
                  'INOD', 'CAVA', 'SMR', 'PHUN', 'DEFT', 'TMC', 'SEZL', 'VLDXD', 'GOOGL', 'MU', 'BIIB', 
                  'TNXP', 'INVZ', 'TLS', 'VVX', 'RDW', 'MP', 'INTC', 'LRCX', 'DLTR', 'WM', 'SPIR', 'GE', 'GEV']

    # my_tickers = ['EVER']
    
    print("🚀 Fetching current stock data...")
    print(f"📊 Tickers: {', '.join(my_tickers)}")
    print("=" * 60)
    
    # Get data
    df = get_stock_metrics(my_tickers)
    
    # Check quality
    warnings = check_data_quality(df)
    if warnings:
        print("\n⚠️  QUALITY WARNINGS:")
        for warning in warnings:
            print(warning)
    
    # Save with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'stock_data_current_{timestamp}.csv'
    df.to_csv(filename)
    
    print(f"\n💾 Data saved to: {filename}")
    print(f"📈 Shape: {df.shape[0]} metrics × {df.shape[1]} stocks")
