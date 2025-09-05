import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import statsmodels.api as sm

class PortfolioAnalyzer:
    def __init__(self, tickers, weights, benchmark = 'SPY', start_date = '2023-08-25'):
        """
        Initialize portfolio analyzer
        
        Parameters:
        tickers: list of stock symbols
        weights: list of portfolio weights (must sum to 1.0)
        benchmark: benchmark symbol (default SPY, it can be replace to QQQ)
        start_date: start date for analysis (default 2 years ago)
        """
        self.tickers = tickers
        self.weights = np.array(weights)
        self.benchmark = benchmark
        
        if start_date is None:
            self.start_date = datetime.now() - timedelta(days = 730)
        else:
            self.start_date = pd.to_datetime(start_date)
            
        # Validating weights 
        if abs(sum(weights) - 1.0) > 0.01:
            print(f"Warning: Weights sum to {sum(weights):.3f}, not 1.0")
            
            
    def fetch_data(self):
        "Download price data for all tickers and benchmark"
        print("Downloading data...")
        
        # Get stock data
        all_tickers = self.tickers + [self.benchmark]
        self.data = yf.download(all_tickers, start = self.start_date)['Close']
        
        # Get risk-free rate (3-month Treasury)
        # Convert DataFrame to Series immediately
        treasury_data = yf.download('^IRX', start=self.start_date)['Close']
        if isinstance(treasury_data, pd.DataFrame):
            self.risk_free_rate = treasury_data['^IRX'].dropna() / 100  # Extract series
        else:
            self.risk_free_rate = treasury_data.dropna() / 100  # Already a series
        
        print(f"Downloaded data for {len(self.tickers)} stocks from {self.start_date.date()}")
        
    def calculate_returns(self):
        """Calculate daily and monthly returns"""
        available_tickers = [t for t in self.tickers if t in self.data.columns]
        if len(available_tickers) < len(self.tickers):
            missing = set(self.tickers) - set(available_tickers)
            print(f"Warning: No data for {missing}")
        
        # Daily Returns
        self.daily_returns = self.data.pct_change().dropna()
        
        # Monthly returns
        monthly_data = self.data.resample('ME').last() # the resample function converts data to monthly frequency and takes the most recent value
        self.monthly_returns = monthly_data.pct_change().dropna()
        
        # Portfolio returns
        portfolio_weights = pd.Series(self.weights, index = self.tickers)
        self.daily_portfolio_returns = (self.daily_returns[self.tickers] * portfolio_weights).sum(axis = 1)
        self.monthly_portfolio_returns = (self.monthly_returns[self.tickers] * portfolio_weights).sum(axis = 1)

    def calculate_sharpe_ratio(self, return_series, risk_free_rate_period):
        """ Calculate Sharpe ratio for given returns series """
        if risk_free_rate_period == 'monthly':
            # Get monthly risk-free rates (these are annual rates though)            
            aligned_rf_monthly, rf_common_dates = self._get_aligned_monthly_rf_rate(return_series.index)
            aligned_returns = return_series.loc[rf_common_dates]
            
            # Calculate excess returns using aligned data
            excess_returns = aligned_returns - aligned_rf_monthly
        
        else:
            # Daily risk_free rate approximation (the formula is a rearranged version of the compound interest formula)
            aligned_rf_daily, rf_common_dates = self._get_aligned_daily_rf_rate(return_series.index)
            aligned_returns = return_series.loc[rf_common_dates]
            
            # Calculate excess returns using aligned data
            excess_returns = aligned_returns - aligned_rf_daily
            
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252 if risk_free_rate_period == 'daily' else 12)        
    
    def calculate_beta_alpha(self):
        """ Calculate portfolio beta and alpha """
        # Portfolio vs. benchmark returns
        portfolio_returns = self.monthly_portfolio_returns
        benchmark_returns = self.monthly_returns[self.benchmark]
        
        # Align dates
        common_dates = portfolio_returns.index.intersection(benchmark_returns.index)
        port_ret = portfolio_returns.loc[common_dates]
        bench_ret = benchmark_returns.loc[common_dates]
        
        # Calculate beta
        covariance = np.cov(port_ret, bench_ret, ddof = 1)[0, 1]
        benchmark_variance = np.var(bench_ret, ddof = 1)
        self.portfolio_beta = covariance / benchmark_variance
        
        # Calculate alpha
        rf_monthly, rf_common_dates = self._get_aligned_monthly_rf_rate(port_ret.index)

        expected_return = rf_monthly.mean() + self.portfolio_beta * (bench_ret.mean() - rf_monthly.mean())
        self.portfolio_alpha = port_ret.mean() - expected_return
        
        return self.portfolio_beta, self.portfolio_alpha
    
    def alpha_beta_reg(self):
        """Run OLS regression of Y on X."""
        return sm.OLS(self.Y, self.X).fit()

    def alpha_beta_contribution(self):
        """Calculate beta and alpha contributions from regression 
        results."""
        benchmark_col = self.X.columns[1]
        beta_contr = self.results.params[benchmark_col] * self.X.iloc[:, 1]  # Use second column (benchmark)
        alpha_contr = self.results.params['const'] + self.results.resid
        return beta_contr, alpha_contr

    def alpha_beta_eval(self):
        """Evaluate alpha performance metrics."""
        beta_contr, alpha_contr = self.alpha_beta_contribution()
        benchmark_col = self.X.columns[1]  # Second column is benchmark
        corr_benchmark = alpha_contr.corr(self.X[benchmark_col])
        alpha = alpha_contr.mean()
        ir = alpha_contr.mean() / alpha_contr.std() * np.sqrt(12)  # Monthly data
        alpha_tstat = self.results.tvalues['const']
        return corr_benchmark, alpha, ir, alpha_tstat

    def calculate_beta_alpha_v2(self):
        """Calculate portfolio beta and alpha using statsmodels 
        regression."""
        # Get aligned data
        portfolio_returns = self.monthly_portfolio_returns
        benchmark_returns = self.monthly_returns[self.benchmark]

        common_dates = portfolio_returns.index.intersection(benchmark_returns.index)
        port_ret = portfolio_returns.loc[common_dates]
        bench_ret = benchmark_returns.loc[common_dates]

        # Prepare regression data
        self.X = pd.DataFrame({'const': 1, self.benchmark: bench_ret})
        self.Y = port_ret

        # Run regression: portfolio_returns = alpha + beta * 
        # benchmark_returns + error
        self.results = self.alpha_beta_reg()

        # Extract results
        self.portfolio_beta = self.results.params[self.benchmark]
        self.portfolio_alpha = self.results.params['const']  # This is excess return alpha

        # Optional: Get additional metrics
        beta_contr, alpha_contr = self.alpha_beta_contribution()
        corr_benchmark, alpha_mean, ir, alpha_tstat = self.alpha_beta_eval()

        return {
                'beta': self.portfolio_beta,
                'alpha': self.portfolio_alpha,
                'information_ratio': ir,
                'alpha_tstat': alpha_tstat,
                'correlation_to_benchmark': corr_benchmark
            }
        
    def print_alpha_beta_results(self, results_dict):
        """Pretty print alpha/beta analysis results."""
        print("=" * 50)
        print("PORTFOLIO ALPHA/BETA ANALYSIS")
        print("=" * 50)
        print(f"Beta:                    {results_dict['beta']:.4f}")
        print(f"Alpha (monthly):         {results_dict['alpha']:.4f}")
        print(f"Alpha (annualized):      {results_dict['alpha'] * 12:.4f}")
        print(f"Information Ratio:       {results_dict['information_ratio']:.4f}")
        print(f"Alpha t-statistic:       {results_dict['alpha_tstat']:.4f}")
        print(f"Correlation to benchmark:{results_dict['correlation_to_benchmark']:.2e}")
        print("=" * 50)

        # Interpretation
        if abs(results_dict['alpha_tstat']) > 2:
            print("✓ Alpha is statistically significant")
        else:
            print("✗ Alpha is not statistically significant")

        if results_dict['information_ratio'] > 0.5:
            print("✓ Strong information ratio")
        elif results_dict['information_ratio'] > 0:
            print("~ Positive but modest information ratio")
        else:
            print("✗ Negative information ratio")
          
    def analyze_individual_stocks(self):
        """Analyze individual stock performance metrics """
        result = {}
        
        for ticker in self.tickers:
            stock_returns = self.monthly_returns[ticker]
            benchmark_returns = self.monthly_returns[self.benchmark]
            
            # Align dates
            common_dates = stock_returns.index.intersection(benchmark_returns.index)
            stock_ret = stock_returns.loc[common_dates]
            bench_ret = benchmark_returns.loc[common_dates]
            
            # Individual Sharpe Ratio
            rf_monthly, rf_common_dates = self._get_aligned_monthly_rf_rate(stock_ret.index)
            rf_monthly = rf_monthly.mean()
            excess_returns = stock_returns.loc[rf_common_dates] - rf_monthly
            sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(12)
            
            # Individual beta
            covariance = np.cov(stock_ret, bench_ret, ddof = 1)[0,1]
            benchmark_variance = np.var(bench_ret, ddof = 1)
            beta = covariance / benchmark_variance
            
            # Individual alpha 
            expected_return = rf_monthly + beta * (bench_ret.mean() - rf_monthly)
            alpha = stock_ret.mean() - expected_return
            
            result[ticker] = {
                'sharpe_ratio': sharpe,
                'beta': beta,
                'alpha': alpha,
                'annual_return': stock_ret.mean() * 12,
                'annual_volatility': stock_ret.std() * np.sqrt(12),
                'weight': self.weights[self.tickers.index(ticker)]
            }
            
        return pd.DataFrame(result).T
    
    def _get_aligned_monthly_rf_rate(self, target_dates):
        """
        Helper method to get monthly risk_free rate aligned with target dates
        
        Parameters: 
        target_dates: DatetimeIndex to align with
        
        Returns:
        float: Average monthly risk-free rate for the aligned period
        """       
        rf_monthly_annual = self.risk_free_rate.resample('ME').last()
        common_rf_dates = target_dates.intersection(rf_monthly_annual.index)
        aligned_rf_annual = rf_monthly_annual.loc[common_rf_dates]
        aligned_rf_monthly = ((1 + aligned_rf_annual)**(1/12) - 1)

        return aligned_rf_monthly, common_rf_dates
    
    def _get_aligned_daily_rf_rate(self, target_dates):
        """
        Helper method to get daily risk_free rate aligned with target dates
        
        Parameters: 
        target_dates: DatetimeIndex to align with
        
        Returns:
        float: Average monthly risk-free rate for the aligned period
        """       
        rf_daily_annual = self.risk_free_rate # daily annual rates
        common_rf_dates = target_dates.intersection(rf_daily_annual.index)
        aligned_rf_annual = rf_daily_annual.loc[common_rf_dates]
        aligned_rf_daily = (1 + aligned_rf_annual)**(1/252) - 1

        return aligned_rf_daily, common_rf_dates
    
    def analyze_recent_performance(self, days_back=30):
        """Analyze portfolio performance for the most recent period"""
        # Get recent cutoff date
        end_date = datetime.now()
        start_recent = end_date - timedelta(days=days_back)
        
        # Filter returns to recent period
        recent_daily_portfolio = self.daily_portfolio_returns[self.daily_portfolio_returns.index >= start_recent]
        recent_daily_benchmark = self.daily_returns[self.benchmark][self.daily_returns.index >= start_recent]
        
        if len(recent_daily_portfolio) == 0:
            print(f"No data available for the last {days_back} days")
            return None
        
        # Calculate recent metrics
        recent_portfolio_return = (1 + recent_daily_portfolio).prod() - 1
        recent_benchmark_return = (1 + recent_daily_benchmark).prod() - 1
        
        recent_portfolio_vol = recent_daily_portfolio.std() * np.sqrt(252)
        recent_benchmark_vol = recent_daily_benchmark.std() * np.sqrt(252)
        
        # Calculate recent alpha/beta (if enough data points)
        if len(recent_daily_portfolio) >= 10:
            aligned_dates = recent_daily_portfolio.index.intersection(recent_daily_benchmark.index)
            port_ret_aligned = recent_daily_portfolio.loc[aligned_dates]
            bench_ret_aligned = recent_daily_benchmark.loc[aligned_dates]
            
            if len(aligned_dates) >= 10:
                # Simple beta calculation
                covariance = np.cov(port_ret_aligned, bench_ret_aligned, ddof=1)[0, 1]
                benchmark_variance = np.var(bench_ret_aligned, ddof=1)
                recent_beta = covariance / benchmark_variance if benchmark_variance != 0 else 0
                
                # Simple alpha (excess return over beta-adjusted benchmark)
                recent_alpha_daily = port_ret_aligned.mean() - recent_beta * bench_ret_aligned.mean()
                recent_alpha_annualized = recent_alpha_daily * 252
            else:
                recent_beta = None
                recent_alpha_annualized = None
        else:
            recent_beta = None
            recent_alpha_annualized = None
        
        print(f"\n=== RECENT PERFORMANCE ({days_back} DAYS) ===")
        print(f"Period: {start_recent.date()} to {end_date.date()}")
        print(f"Trading days: {len(recent_daily_portfolio)}")
        print(f"\nPortfolio Return: {recent_portfolio_return:.2%}")
        print(f"Benchmark Return: {recent_benchmark_return:.2%}")
        print(f"Excess Return: {recent_portfolio_return - recent_benchmark_return:.2%}")
        print(f"\nPortfolio Volatility (annualized): {recent_portfolio_vol:.2%}")
        print(f"Benchmark Volatility (annualized): {recent_benchmark_vol:.2%}")
        
        if recent_beta is not None:
            print(f"\nRecent Beta: {recent_beta:.3f}")
            print(f"Recent Alpha (annualized): {recent_alpha_annualized:.2%}")
        else:
            print(f"\nInsufficient data for beta/alpha calculation (need ≥10 trading days)")
        
        return {
            'period_days': days_back,
            'trading_days': len(recent_daily_portfolio),
            'portfolio_return': recent_portfolio_return,
            'benchmark_return': recent_benchmark_return,
            'excess_return': recent_portfolio_return - recent_benchmark_return,
            'portfolio_vol': recent_portfolio_vol,
            'benchmark_vol': recent_benchmark_vol,
            'beta': recent_beta,
            'alpha_annualized': recent_alpha_annualized
        }
    
    def generate_report(self):
        self.calculate_returns()
        portfolio_beta, portfolio_alpha = self.calculate_beta_alpha()
        alpha_beta_result = self.calculate_beta_alpha_v2()
        individual_analysis = self.analyze_individual_stocks()
        
        # Portfolio-level metrics
        portfolio_sharpe = self.calculate_sharpe_ratio(self.monthly_portfolio_returns, 'monthly')
        # portfolio_sharpe = self.calculate_sharpe_ratio(self.daily_portfolio_returns, 'daily')
        portfolio_annual_return = self.monthly_portfolio_returns.mean() * 12
        portfolio_annual_vol = self.monthly_portfolio_returns.std() * np.sqrt(12)
        
        # Benchmark metrics
        benchmark_annual_return = self.monthly_returns[self.benchmark].mean() * 12
        benchmark_annual_vol = self.monthly_returns[self.benchmark].std() * np.sqrt(12)
        benchmark_sharpe = self.calculate_sharpe_ratio(self.monthly_returns[self.benchmark], 'monthly')
        
        print()
        print("=== PORTFOLIO PERFORMANCE REPORT ===")
        print(f"Analysis Period: {self.start_date.date()} to {datetime.now().date()}")
        print(f"Benchmark: {self.benchmark}")
        
        print("\n--- PORTFOLIO METRICS ---")
        print(f"Annual Return: {portfolio_annual_return:.2%}")
        print(f"Annual Volatility: {portfolio_annual_vol:.2%}")
        print(f"Sharpe Ratio: {portfolio_sharpe:.3f}")
        print(f"Beta: {portfolio_beta:.3f}")
        print(f"Alpha: {portfolio_alpha*12:.2%} (annualized)")
        
        print(f"\n--- ANOTHER ALPHA BETA ANALYSIS ---")
        print(self.print_alpha_beta_results(alpha_beta_result))
        
        print(f"\n--- BENCHMARK ({self.benchmark}) METRICS ---")
        print(f"Annual Return: {benchmark_annual_return:.2%}")
        print(f"Annual Volatility: {benchmark_annual_vol:.2%}")
        print(f"Sharpe Ratio: {benchmark_sharpe:.3f}")
        
        print(f"\n--- INDIVIDUAL STOCK ANALYSIS ---")
        print(individual_analysis.round(3))
        
        # Recent performance analysis
        recent_performance = self.analyze_recent_performance(30)  # Last 30 days
        
        return {
            'portfolio_metrics': {
                'annual_return': portfolio_annual_return,
                'annual_volatility': portfolio_annual_vol,
                'sharpe_ratio': portfolio_sharpe,
                'beta': portfolio_beta,
                'alpha': portfolio_alpha
            },
            'individual_stocks': individual_analysis,
            'benchmark_metrics': {
                'annual_return': benchmark_annual_return,
                'annual_volatility': benchmark_annual_vol,
                'sharpe_ratio': benchmark_sharpe
            }
        }
    
if __name__ == "__main__":
    tickers = ['TNXP', 'INVZ', 'TMC', 'NBIS', 'SSYS', 'UNH', 'CRSP', 'RKLB', 'AMZN']
    weights = np.ones(len(tickers)) / len(tickers)
    
    analyzer = PortfolioAnalyzer(tickers, weights)
    analyzer.fetch_data()
    analyzer.generate_report()
    
