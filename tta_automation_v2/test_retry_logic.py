"""
Quick test of the improved preprocessing with retry logic
Tests on a small sample including valid, invalid, and potentially rate-limited tickers
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime
import pandas as pd

# Import from our preprocessing script
exec(open('00_ticker_preprocessing.py').read())

# Test with a mix of tickers:
# - Valid tickers that should work
# - Invalid/delisted tickers
# - Mix of sectors
test_tickers = [
    # Valid major tickers
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
    # Valid smaller tickers
    'PLTR', 'RKLB', 'IONQ',
    # Invalid/questionable tickers (might fail)
    'INVALID123', 'ZZZZZ', 'XXXXX',
]

print("=" * 80)
print("🧪 TESTING RETRY LOGIC AND ERROR HANDLING")
print("=" * 80)
print(f"\nTesting with {len(test_tickers)} tickers")
print(f"Expected: ~8 successful, ~3 failed\n")

# Run the filter
viable_tickers, failed_tickers, error_details = filter_by_basic_criteria(
    test_tickers,
    min_market_cap=1e6,      # Lower threshold for testing
    min_price=1.0,           # Lower threshold for testing
    min_volume=10000,        # Lower threshold for testing
    max_retries=2,           # Fewer retries for faster testing
    base_delay=0.2,          # Shorter delay for faster testing
    checkpoint_interval=5    # More frequent checkpoints for testing
)

print("\n" + "=" * 80)
print("📊 TEST RESULTS")
print("=" * 80)

print(f"\n✅ Viable tickers ({len(viable_tickers)}):")
for ticker_data in viable_tickers:
    print(f"  {ticker_data['ticker']:10} - ${ticker_data['market_cap']/1e9:.2f}B - {ticker_data['sector']}")

print(f"\n❌ Failed tickers ({len(failed_tickers)}):")
for ticker in failed_tickers:
    print(f"  {ticker}")

print(f"\n🔍 Error breakdown:")
for error_type, tickers in error_details.items():
    if tickers:
        print(f"  {error_type:20} : {len(tickers)} tickers")

print("\n" + "=" * 80)
print("✅ Test complete!")
print("=" * 80)
