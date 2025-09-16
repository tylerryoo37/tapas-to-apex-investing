import yfinance as yf
import pandas as pd
from datetime import datetime
import time
import numpy as np 
import requests
from io import StringIO
import random

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
            current_price = recent_data['Close'].iloc[-1] if not recent_data.empty else info.get('currentPrice', np.nan)
            
            # Get price data for momentum calculations
            price_1m = stock.history(period="1mo")
            price_3m = stock.history(period="3mo")
            price_6m = stock.history(period="6mo")
            price_1y = stock.history(period="1y")
            
            # Calculate momentum metrics (price change percentages)
            momentum_1m = ((current_price - price_1m['Close'].iloc[0]) / price_1m['Close'].iloc[0] * 100) if not price_1m.empty and price_1m['Close'].iloc[0] > 0 and not pd.isna(current_price) else np.nan
            momentum_3m = ((current_price - price_3m['Close'].iloc[0]) / price_3m['Close'].iloc[0] * 100) if not price_3m.empty and price_3m['Close'].iloc[0] > 0 and not pd.isna(current_price) else np.nan
            momentum_6m = ((current_price - price_6m['Close'].iloc[0]) / price_6m['Close'].iloc[0] * 100) if not price_6m.empty and price_6m['Close'].iloc[0] > 0 and not pd.isna(current_price) else np.nan
            momentum_1y = ((current_price - price_1y['Close'].iloc[0]) / price_1y['Close'].iloc[0] * 100) if not price_1y.empty and price_1y['Close'].iloc[0] > 0 and not pd.isna(current_price) else np.nan
            
            # Calculate relative strength vs 52-week range
            high_52w = info.get('fiftyTwoWeekHigh', np.nan)
            low_52w = info.get('fiftyTwoWeekLow', np.nan)
            
            # Calculate price vs moving averages
            fifty_day_avg = info.get('fiftyDayAverage', np.nan)
            two_hundred_day_avg = info.get('twoHundredDayAverage', np.nan)
            price_vs_50ma = (current_price / fifty_day_avg - 1) if not pd.isna(current_price) and not pd.isna(fifty_day_avg) and fifty_day_avg != 0 else np.nan
            price_vs_200ma = (current_price / two_hundred_day_avg - 1) if not pd.isna(current_price) and not pd.isna(two_hundred_day_avg) and two_hundred_day_avg != 0 else np.nan
            relative_strength = ((current_price - low_52w) / (high_52w - low_52w) * 100) if not pd.isna(high_52w) and not pd.isna(low_52w) and (high_52w - low_52w) > 0 and not pd.isna(current_price) else np.nan
            
            # Calculate volume change metrics (attention/interest indicators)
            current_volume = recent_data['Volume'].iloc[-1] if not recent_data.empty else np.nan
            avg_volume_1m = price_1m['Volume'].mean() if not price_1m.empty else np.nan
            avg_volume_3m = price_3m['Volume'].mean() if not price_3m.empty else np.nan
            avg_volume_6m = price_6m['Volume'].mean() if not price_6m.empty else np.nan
            avg_volume_1y = price_1y['Volume'].mean() if not price_1y.empty else np.nan
            
            # Volume change percentages vs historical averages
            volume_change_1m = ((current_volume - avg_volume_1m) / avg_volume_1m * 100) if not pd.isna(current_volume) and not pd.isna(avg_volume_1m) and avg_volume_1m > 0 else np.nan
            volume_change_3m = ((current_volume - avg_volume_3m) / avg_volume_3m * 100) if not pd.isna(current_volume) and not pd.isna(avg_volume_3m) and avg_volume_3m > 0 else np.nan
            volume_change_6m = ((current_volume - avg_volume_6m) / avg_volume_6m * 100) if not pd.isna(current_volume) and not pd.isna(avg_volume_6m) and avg_volume_6m > 0 else np.nan
            volume_change_1y = ((current_volume - avg_volume_1y) / avg_volume_1y * 100) if not pd.isna(current_volume) and not pd.isna(avg_volume_1y) and avg_volume_1y > 0 else np.nan
            
            # Relative volume ratios (current volume vs historical averages)
            volume_ratio_1m = (current_volume / avg_volume_1m) if not pd.isna(current_volume) and not pd.isna(avg_volume_1m) and avg_volume_1m > 0 else np.nan
            volume_ratio_3m = (current_volume / avg_volume_3m) if not pd.isna(current_volume) and not pd.isna(avg_volume_3m) and avg_volume_3m > 0 else np.nan
            volume_ratio_6m = (current_volume / avg_volume_6m) if not pd.isna(current_volume) and not pd.isna(avg_volume_6m) and avg_volume_6m > 0 else np.nan
            volume_ratio_1y = (current_volume / avg_volume_1y) if not pd.isna(current_volume) and not pd.isna(avg_volume_1y) and avg_volume_1y > 0 else np.nan

            # Calculate volume ratios from info data
            volume_info = info.get('volume', np.nan)
            avg_volume_info = info.get('averageVolume', np.nan)
            avg_volume_10d_info = info.get('averageVolume10days', np.nan)
            volume_ratio_info = (volume_info / avg_volume_info) if not pd.isna(volume_info) and not pd.isna(avg_volume_info) and avg_volume_info != 0 else np.nan
            volume_trend_info = (avg_volume_10d_info / avg_volume_info) if not pd.isna(avg_volume_10d_info) and not pd.isna(avg_volume_info) and avg_volume_info != 0 else np.nan
            
            # Get cash flow data
            free_cash_flow_row = stock.quarterly_cashflow.loc['Free Cash Flow'] if 'Free Cash Flow' in stock.quarterly_cashflow.index else pd.Series()
            ttm_fcf = free_cash_flow_row.dropna().head(4).sum() if 'Free Cash Flow' in stock.quarterly_cashflow.index else np.nan
            free_cash_flow_row_year = stock.cashflow.loc['Free Cash Flow'] if 'Free Cash Flow' in stock.cashflow.index else pd.Series()
            recent_fcf = free_cash_flow_row_year.dropna().iloc[0] if not isinstance(free_cash_flow_row_year, float) and len(free_cash_flow_row_year.dropna()) > 0 else np.nan
            
            # Get Ebitda data
            ttm_ebitda = q_info.loc['EBITDA'].dropna().head(4).sum() if 'EBITDA' in q_info.index else np.nan
            
            # Get Operating Margin
            ttm_op_income = q_info.loc['Operating Income'].dropna().head(4).sum() if 'Operating Income' in q_info.index else np.nan
            ttm_total_revenue = q_info.loc['Total Revenue'].dropna().head(4).sum() if 'Total Revenue' in q_info.index else np.nan
            ttm_operating_margin = ttm_op_income / ttm_total_revenue if ttm_total_revenue > 0 else np.nan
            
            # Get Quarterly Revenue Growth
            revenue_quarters = q_info.loc['Total Revenue'].dropna().head(2) if 'Total Revenue' in q_info.index else np.nan
            quarterly_revenue_growth = ((revenue_quarters.iloc[0] - revenue_quarters.iloc[1]) / revenue_quarters.iloc[1]) if not isinstance(revenue_quarters, float) and len(revenue_quarters) == 2 and revenue_quarters.iloc[1] != 0 else np.nan
            
            # Get Gross Margin
            ttm_gross_profit = q_info.loc['Gross Profit'].dropna().head(4).sum() if 'Gross Profit' in q_info.index else np.nan
            ttm_total_revenue = q_info.loc['Total Revenue'].dropna().head(4).sum() if 'Total Revenue' in q_info.index else np.nan
            ttm_gross_margin = ttm_gross_profit / ttm_total_revenue if ttm_total_revenue > 0 else np.nan

            # Get Profit Margin
            ttm_net_income = q_info.loc['Net Income'].dropna().head(4).sum() if 'Net Income' in q_info.index else np.nan
            ttm_profit_margin = ttm_net_income / ttm_total_revenue if ttm_total_revenue > 0 else np.nan
            
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
                'Current Price': round(current_price, 2) if not pd.isna(current_price) else info.get('currentPrice', np.nan),
                'Current Market Cap': info.get('marketCap', 'N/A'), # Total market value of the company's outstanding shares
                'P/E Ratio TTM': info.get('trailingPE', 'N/A'), # Current Stock Price / Earnings Per Share (last 12 months): how many years it would take to get your money back based on last year's profit
                'P/E Ratio LFQ (Calculated)': current_price / (ttm_net_income / info.get('sharesOutstanding', 1)) if not pd.isna(ttm_net_income) and ttm_net_income > 0 and not pd.isna(current_price) else np.nan, # Current Stock Price / Earnings Per Share (last 4 quarters): how many years it would take to get your money back based on last year's profit
                'Forward P/E': info.get('forwardPE', 'N/A'),  # Current Stock Price / Projected Earnings Per Share (next 12 months): how many years it would take based on what you THINK it will make next year
                'P/B Ratio': info.get('priceToBook', 'N/A'), # how much investors are paying relative to a company's book value (net worth on the balance sheet)
                'P/S Ratio TTM': info.get('priceToSalesTrailing12Months', 'N/A'), # Price / Sales: how much investors are paying for each dollar of sales
                'Current Ratio MRQ': info.get('currentRatio', 'N/A'), # Current Assets / Current Liabilities: how easily a company can pay its short-term obligations
                'Debt to Equity MRQ': info.get('debtToEquity', 'N/A'), # Total Debt / Shareholder's Equity: how much debt a company has compared to its equity
                'ROE TTM': info.get('returnOnEquity', 'N/A'),  # Return on Equity: how efficiently a company uses shareholder equity to generate profit
                'Revenue Growth YOY': info.get('revenueGrowth', 'N/A'), # Year-over-year revenue growth: how much a company's revenue has increased compared to the same quarter last year
                'Quarterly Revenue Growth (Calculated)': quarterly_revenue_growth,  # Quarterly revenue growth: how much a company's revenue has increased compared to the previous quarter
                
                # VALUATION METRICS
                'P/FCF TTM (Calculated)': info.get('marketCap', np.nan) / recent_fcf if not pd.isna(recent_fcf) and recent_fcf > 0 and info.get('marketCap') not in [None] else np.nan, # Price / Free Cash Flow: how much investors are paying for each dollar of free cash flow
                'P/FCF LFQ (Calculated)': info.get('marketCap', np.nan) / ttm_fcf if not pd.isna(ttm_fcf) and ttm_fcf > 0 and info.get('marketCap') not in [None] else np.nan, # Price / Free Cash Flow: how much investors are paying for each dollar of free cash flow
                'TEV/EBITDA LFQ (Calculated)': info.get('enterpriseValue', np.nan) / ttm_ebitda if not pd.isna(ttm_ebitda) and ttm_ebitda > 0 and info.get('enterpriseValue') not in [None] else np.nan, # Total Enterprise Value / Earnings Before Interest, Taxes, Depreciation, and Amortization: how much investors are paying for each dollar of EBITDA
                'Operating Margin MRQ': info.get('operatingMargins', 'N/A'), # Operating Income / Revenue: how much profit a company makes from its operations before interest and taxes
                'Operating Margin LFQ (Calculated)': ttm_operating_margin,
                'Gross Margin': info.get('grossMargins', 'N/A'), # Gross Profit / Revenue: how much profit a company makes after deducting the cost of goods sold
                'Gross Margin LFQ (Calculated)': ttm_gross_margin, # Gross Profit / Revenue: how much profit a company makes after deducting the cost of goods sold
                'Profit Margin': info.get('profitMargins', 'N/A'), # Net Income / Revenue: how much profit a company makes after all expenses, taxes, and interest
                'Profit Margin LFQ (Calculated)': ttm_profit_margin, # Net Income / Revenue: how much profit a company makes after all expenses, taxes, and interest
                
                # FINANCIAL HEALTH
                'Free Cash Flow LFQ (Calculated)': "; ".join([f"{date}: ${value/1e6:.0f}M" for date, value in free_cash_flow_row.dropna().head(4).items()]) if not isinstance(free_cash_flow_row, float) and len(free_cash_flow_row) > 0 else np.nan, # Free Cash Flow: cash generated after capital expenditures, available for distribution to investors
                'Total Cash MRQ': format_scale(info.get('totalCash', 'N/A')), # Total Cash: cash and cash equivalents on the balance sheet
                'Total Debt MRQ': format_scale(info.get('totalDebt', 'N/A')), # Total Debt: total interest-bearing debt on the balance sheet
                
                # ADDITIONAL METRICS  
                'ROA': info.get('returnOnAssets', 'N/A'), # Return on Assets: how efficiently a company uses its assets to generate profit
                'EPS TTM': info.get('trailingEps', 'N/A'), # Earnings Per Share: how much profit a company makes per share of stock
                'Dividend Yield': info.get('dividendYield', 'N/A'), # Dividend Yield: annual dividend payment divided by stock price, expressed as a percentage
                'Shares Outstanding': info.get('sharesOutstanding', 'N/A'), # total number of shares of stock currently held by all shareholders
                
                # ANALYST DATA
                'Target Price': info.get('targetMeanPrice', 'N/A'), # Average target price set by analysts
                'Recommendation': info.get('recommendationMean', 'N/A'), # Average recommendation score from analysts (1-5 scale)
                'Institutional Ownership (%)': round(info.get('heldPercentInstitutions', 0) * 100, 2) if info.get('heldPercentInstitutions') not in [None, 'N/A'] else 'N/A', # Percentage held by institutions
                'Insider Ownership (%)': round(info.get('heldPercentInsiders', 0) * 100, 2) if info.get('heldPercentInsiders') not in [None, 'N/A'] else 'N/A', # Percentage held by insiders
                'Short Ratio': round(info.get('shortRatio', 0), 2) if info.get('shortRatio') not in [None, 'N/A'] else 'N/A', # Days to cover short positions
                
                # TRADING DATA
                '52W High': info.get('fiftyTwoWeekHigh', 'N/A'),
                '52W Low': info.get('fiftyTwoWeekLow', 'N/A'),
                'Beta': info.get('beta', 'N/A'), # measure of stock volatility compared to the market
                
                # MOMENTUM METRICS
                'Momentum 1M (%)': round(momentum_1m, 2) if not pd.isna(momentum_1m) else np.nan, # Price change over last 1 month
                'Momentum 3M (%)': round(momentum_3m, 2) if not pd.isna(momentum_3m) else np.nan, # Price change over last 3 months
                'Momentum 6M (%)': round(momentum_6m, 2) if not pd.isna(momentum_6m) else np.nan, # Price change over last 6 months
                'Momentum 1Y (%)': round(momentum_1y, 2) if not pd.isna(momentum_1y) else np.nan, # Price change over last 1 year
                'Relative Strength (%)': round(relative_strength, 2) if not pd.isna(relative_strength) else np.nan, # Position within 52-week range (0-100%)
                'Price vs 50MA (%)': round(price_vs_50ma * 100, 2) if not pd.isna(price_vs_50ma) else np.nan, # Current price relative to 50-day moving average
                'Price vs 200MA (%)': round(price_vs_200ma * 100, 2) if not pd.isna(price_vs_200ma) else np.nan, # Current price relative to 200-day moving average
                
                # VOLUME METRICS (Attention/Interest Indicators)
                'Current Volume': int(current_volume) if not pd.isna(current_volume) else np.nan, # Latest trading volume
                'Avg Volume 1M': int(avg_volume_1m) if not pd.isna(avg_volume_1m) else np.nan, # Average daily volume over 1 month
                'Avg Volume 3M': int(avg_volume_3m) if not pd.isna(avg_volume_3m) else np.nan, # Average daily volume over 3 months
                'Volume Change 1M (%)': round(volume_change_1m, 2) if not pd.isna(volume_change_1m) else np.nan, # Volume change vs 1-month average
                'Volume Change 3M (%)': round(volume_change_3m, 2) if not pd.isna(volume_change_3m) else np.nan, # Volume change vs 3-month average
                'Volume Change 6M (%)': round(volume_change_6m, 2) if not pd.isna(volume_change_6m) else np.nan, # Volume change vs 6-month average
                'Volume Change 1Y (%)': round(volume_change_1y, 2) if not pd.isna(volume_change_1y) else np.nan, # Volume change vs 1-year average
                'Volume Ratio (Avg)': round(volume_ratio_info, 2) if not pd.isna(volume_ratio_info) else np.nan, # Current volume vs average volume (from info)
                'Volume Trend (10d/Avg)': round(volume_trend_info, 2) if not pd.isna(volume_trend_info) else np.nan, # 10-day volume trend vs average
                'Volume Ratio 1M': round(volume_ratio_1m, 2) if not pd.isna(volume_ratio_1m) else np.nan, # Current volume / 1-month avg (>1 = above normal)
                'Volume Ratio 3M': round(volume_ratio_3m, 2) if not pd.isna(volume_ratio_3m) else np.nan, # Current volume / 3-month avg (>1 = above normal)
                'Volume Ratio 6M': round(volume_ratio_6m, 2) if not pd.isna(volume_ratio_6m) else np.nan, # Current volume / 6-month avg (>1 = above normal)
                'Volume Ratio 1Y': round(volume_ratio_1y, 2) if not pd.isna(volume_ratio_1y) else np.nan, # Current volume / 1-year avg (>1 = above normal)

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

def sp500_tickers():

    # Get S&P500 tickers
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    response = requests.get(url, headers=headers)
    tickers = pd.read_html(StringIO(response.text))[0].Symbol.to_list()
    tickers = [x.replace('.','-') for x in tickers]

    return tickers

def nasdaq_tickers():

    # Get S&P500 tickers
    url = 'https://en.wikipedia.org/wiki/NASDAQ-100'
    response = requests.get(url, headers=headers)
    tickers = pd.read_html(StringIO(response.text))[4]['Ticker'].to_list()
    tickers = [x.replace('.','-') for x in tickers]

    return tickers

def dow_jones_tickers():
    """Get Dow Jones Industrial Average tickers from Wikipedia"""
    url = 'https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average'
    response = requests.get(url, headers=headers)
    tables = pd.read_html(StringIO(response.text))
    tickers = tables[2]['Symbol'].to_list()
    tickers = [x.replace('.', '-') for x in tickers]
    return tickers

# SIMPLE USAGE
if __name__ == "__main__":
    
    #=============================================================================================================
    # TICKER SELECTION OPTIONS
    #=============================================================================================================
    
    ticker_type =None
    
    # Option 1: Manual ticker selection for specific stocks of interest
    # Uncomment and modify this list to analyze specific tickers
    # ticker_type = 'tta'
    # my_tickers = ['IBM', 'NICE', 'ADBE', 'STGW', 'PGY', 'KOPN', 'ENPH', 'SMCI', 'INTC', 'DLTR']  # Single ticker example
    
    # Current manual selection - mix of growth, value, and speculative stocks
    # ticker_type = 'tta'
    # my_tickers = ['SSYS', 'BE', 'SLDP', 'NVAX', 'NBIS', 'VVX', 'ARDX', 'CELH', 'ANET', 'AEHR', 'APP', 
    #               'PLTR', 'META', 'CTRE', 'BLDP', 'AAPL', 'AVGO', 'AUDC', 'CRSP', 'MRVL', 'VRT', 'NVDA', 
    #               'PL', 'WMT', 'OXY', 'SGML', 'UNH', 'LQDT', 'MDT', 'ORCL', 'MSFT', 'TSLA', 'COST', 'MRK', 
    #               'BLNK', 'NXP', 'BNTX', 'QBTS', 'RGTI', 'ABT', 'SIRI', 'CCJ', 'ASML', 'ADBE', 'PYPL', 
    #               'SNOW', 'CHYM', 'RKLB', 'IONQ', 'ASTS', 'NOW', 'AISP', 'MRNA', 'CHGG', 'BBAI', 'QUBT', 
    #               'INOD', 'CAVA', 'SMR', 'PHUN', 'DEFT', 'TMC', 'SEZL', 'VLDXD', 'GOOGL', 'MU', 'BIIB', 
    #               'TNXP', 'INVZ', 'TLS', 'VVX', 'RDW', 'MP', 'INTC', 'LRCX', 'DLTR', 'WM', 'SPIR', 'GE', 'GEV']

    #=============================================================================================================
    
    # Option 2: Programmatically select tickers from major indices
    # Uncomment the lines below to use S&P 500 or NASDAQ-100 tickers instead of manual selection
    
    # Required headers for web scraping (prevents 403 errors from Wikipedia)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    # Uncomment these lines to use S&P 500 tickers:
    # ticker_type = 'sp500'
    # my_tickers = sp500_tickers()
    
    # Uncomment these lines to use NASDAQ-100 tickers:
    # ticker_type = 'nasdaq'
    # my_tickers = nasdaq_tickers()
    
    # Uncomment these lines to use Dow Jones tickers:
    # ticker_type = 'dowjones'
    # my_tickers = dow_jones_tickers()
    
    # Uncomment these lines to get a selection of 500-1000 tickers from a larger list
    all_tickers = pd.read_csv('tapas-to-apex-investing/all_tickers.txt', header=None)[0].to_list()
    segment_size = 500
    segment_number = 1
    ticker_type = f'segment_{segment_number}'
    
    start_idx = segment_number * segment_size
    end_idx = start_idx + segment_size
    my_tickers = all_tickers[start_idx:end_idx]
    
    # my_tickers = all_tickers[1001:1501]
    # my_tickers = all_tickers[501:1001]
    # my_tickers = all_tickers[0:500]
    # my_tickers = random.sample(all_tickers, 500)
    
    #=============================================================================================================
    
    #=============================================================================================================
    # DATA COLLECTION AND PROCESSING
    #=============================================================================================================
    
    print("=" * 60)
    print("🚀 Fetching current stock data...")
    print(f"📊 Tickers to analyze: {', '.join(my_tickers)}")
    print("=" * 60)
    
    # Fetch financial data for all selected tickers
    # This will pull key metrics including P/E ratios, market cap, financial ratios, etc.
    df = get_stock_metrics(my_tickers)
    
    # Perform data quality checks to identify missing data or suspicious values
    # This helps identify potential issues like missing P/E ratios or extreme values
    warnings = check_data_quality(df)
    if warnings:
        print("\n⚠️  DATA QUALITY WARNINGS:")
        for warning in warnings:
            print(warning)

    #=============================================================================================================
    # DATA EXPORT
    #=============================================================================================================
    
    # Create timestamped filename for data export (prevents overwriting previous analyses)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    datestamp = datetime.now().strftime('%Y%m%d')
    if ticker_type is not None: 
        filename = f'tapas-to-apex-investing/stock_data_current_{datestamp}_{ticker_type}.csv'    
    else:
        filename = f'tapas-to-apex-investing/stock_data_current_{timestamp}.csv'
    
    # Export complete dataset to CSV for further analysis or record keeping
    df.to_csv(filename)
    
    print(f"📈 Dataset dimensions: {df.shape[0]} metrics × {df.shape[1]} stocks")
    print(f"\n💾 Complete dataset saved to: {filename}")
    print("=" * 60)
