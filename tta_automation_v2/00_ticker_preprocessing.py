import yfinance as yf
import pandas as pd
from datetime import datetime
import time
from tqdm import tqdm
import requests

def clean_ticker_list(tickers):
    """
    Remove warrants, units, preferred shares, and other non-common stock tickers

    Common patterns to exclude:
    - Ends with W, WS, WT = Warrants
    - Ends with U = Units (stock + warrant bundle)
    - Contains -PR, -P = Preferred shares
    - Ends with R = Rights
    - Contains ^ or ~ = Special share classes
    """
    clean_tickers = []
    excluded_count = {'warrants': 0, 'units': 0, 'preferred': 0, 'rights': 0, 'other': 0}

    for ticker in tickers:
        ticker = ticker.strip()
        ticker_upper = ticker.upper()

        # Skip if contains special characters
        if '^' in ticker or '~' in ticker:
            excluded_count['other'] += 1
            continue

        # Skip warrants
        if ticker_upper.endswith('W') or ticker_upper.endswith('WS') or ticker_upper.endswith('WT'):
            excluded_count['warrants'] += 1
            continue

        # Skip units
        if ticker_upper.endswith('U'):
            excluded_count['units'] += 1
            continue

        # Skip preferred shares
        if '-PR' in ticker_upper or '-P' in ticker_upper:
            excluded_count['preferred'] += 1
            continue

        # Skip rights
        if ticker_upper.endswith('R') and len(ticker) > 4:  # Avoid removing single letters like 'R'
            excluded_count['rights'] += 1
            continue

        clean_tickers.append(ticker)

    print(f"\n📊 Ticker Cleaning Results:")
    print(f"  Original count: {len(tickers)}")
    print(f"  Cleaned count: {len(clean_tickers)}")
    print(f"  Excluded - Warrants: {excluded_count['warrants']}")
    print(f"  Excluded - Units: {excluded_count['units']}")
    print(f"  Excluded - Preferred: {excluded_count['preferred']}")
    print(f"  Excluded - Rights: {excluded_count['rights']}")
    print(f"  Excluded - Other: {excluded_count['other']}")

    return clean_tickers


def filter_by_basic_criteria(tickers,
                             min_market_cap=100e6,  # $100M minimum
                             min_price=5.0,          # $5 minimum
                             min_volume=100000,      # 100K shares minimum
                             max_retries=3,          # Number of retries for failed requests
                             base_delay=0.25,        # Base delay between requests (seconds)
                             checkpoint_interval=100): # Save progress every N tickers
    """
    Filter tickers by market cap, price, and volume with retry logic and checkpointing
    This does a lightweight API call to get basic info only
    """
    viable_tickers = []
    failed_tickers = []
    filtered_out = {'market_cap': 0, 'price': 0, 'volume': 0, 'no_data': 0}
    error_details = {
        'rate_limit': [],
        'not_found': [],
        'timeout': [],
        'network_error': [],
        'other_error': []
    }

    print(f"\n🔍 Filtering {len(tickers)} tickers by criteria:")
    print(f"  Min Market Cap: ${min_market_cap/1e6:.0f}M")
    print(f"  Min Price: ${min_price}")
    print(f"  Min Volume: {min_volume:,}")
    print(f"  Max Retries: {max_retries}")
    print(f"  Base Delay: {base_delay}s")
    print(f"  Checkpoint Interval: Every {checkpoint_interval} tickers")
    print("\nThis may take a while...\n")

    # Try to load previous checkpoint if exists
    checkpoint_file = 'ticker_data/preprocessing_checkpoint.csv'
    start_index = 0
    try:
        if pd.io.common.file_exists(checkpoint_file):
            checkpoint_df = pd.read_csv(checkpoint_file)
            viable_tickers = checkpoint_df.to_dict('records')
            start_index = len(viable_tickers)
            print(f"📂 Resuming from checkpoint: {start_index} tickers already processed\n")
    except Exception:
        pass

    for idx, ticker in enumerate(tqdm(tickers[start_index:], desc="Filtering tickers", initial=start_index, total=len(tickers))):
        success = False
        last_error = None

        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                stock = yf.Ticker(ticker)
                info = stock.info

                # Get basic metrics
                market_cap = info.get('marketCap', 0)
                price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                volume = info.get('volume') or info.get('averageVolume', 0)

                # Get sector and industry data
                sector = info.get('sector', 'Unknown')
                industry = info.get('industry', 'Unknown')

                # Check if we have any data
                if market_cap == 0 and price == 0 and volume == 0:
                    filtered_out['no_data'] += 1
                    failed_tickers.append(ticker)
                    success = True  # Don't retry - ticker truly has no data
                    break

                # Apply filters
                if market_cap > 0 and market_cap < min_market_cap:
                    filtered_out['market_cap'] += 1
                    success = True
                    break

                if price > 0 and price < min_price:
                    filtered_out['price'] += 1
                    success = True
                    break

                if volume > 0 and volume < min_volume:
                    filtered_out['volume'] += 1
                    success = True
                    break

                # Passed all filters
                viable_tickers.append({
                    'ticker': ticker,
                    'market_cap': market_cap,
                    'price': price,
                    'volume': volume,
                    'sector': sector,
                    'industry': industry
                })
                success = True
                break

            except requests.exceptions.HTTPError as e:
                last_error = e
                if hasattr(e, 'response') and e.response.status_code == 429:
                    # Rate limited - wait longer
                    wait_time = base_delay * (3 ** attempt)  # Exponential backoff: 0.25s, 0.75s, 2.25s
                    time.sleep(wait_time)
                    continue
                elif hasattr(e, 'response') and e.response.status_code == 404:
                    # Not found - don't retry
                    error_details['not_found'].append(ticker)
                    success = True
                    break
                else:
                    # Other HTTP error
                    time.sleep(base_delay * (2 ** attempt))
                    continue

            except requests.exceptions.Timeout:
                last_error = "Timeout"
                time.sleep(base_delay * (2 ** attempt))
                continue

            except requests.exceptions.RequestException as e:
                last_error = e
                time.sleep(base_delay * (2 ** attempt))
                continue

            except Exception as e:
                last_error = e
                time.sleep(base_delay * (2 ** attempt))
                continue

        # If all retries failed, categorize the error
        if not success:
            failed_tickers.append(ticker)
            filtered_out['no_data'] += 1

            if isinstance(last_error, requests.exceptions.HTTPError):
                if hasattr(last_error, 'response') and last_error.response.status_code == 429:
                    error_details['rate_limit'].append(ticker)
                else:
                    error_details['other_error'].append(ticker)
            elif isinstance(last_error, requests.exceptions.Timeout):
                error_details['timeout'].append(ticker)
            elif isinstance(last_error, requests.exceptions.RequestException):
                error_details['network_error'].append(ticker)
            else:
                error_details['other_error'].append(ticker)

        # Checkpoint progress every N tickers
        if (idx + 1) % checkpoint_interval == 0 and viable_tickers:
            try:
                pd.DataFrame(viable_tickers).to_csv(checkpoint_file, index=False)
            except Exception:
                pass  # Continue even if checkpoint fails

        # Normal delay between requests
        time.sleep(base_delay)

    # Print detailed results
    print(f"\n✅ Filtering Complete:")
    print(f"  Viable tickers: {len(viable_tickers)}")
    print(f"  Filtered out - Market cap too low: {filtered_out['market_cap']}")
    print(f"  Filtered out - Price too low: {filtered_out['price']}")
    print(f"  Filtered out - Volume too low: {filtered_out['volume']}")
    print(f"  Filtered out - No data/Failed: {filtered_out['no_data']}")

    print(f"\n🔍 Error Breakdown:")
    print(f"  Rate limited (429): {len(error_details['rate_limit'])}")
    print(f"  Not found (404): {len(error_details['not_found'])}")
    print(f"  Timeout: {len(error_details['timeout'])}")
    print(f"  Network errors: {len(error_details['network_error'])}")
    print(f"  Other errors: {len(error_details['other_error'])}")

    return viable_tickers, failed_tickers, error_details


def create_segments(tickers, segment_size=500):
    """
    Split tickers into segments for batch processing
    Returns list of segments
    """
    segments = []
    for i in range(0, len(tickers), segment_size):
        segments.append(tickers[i:i + segment_size])

    print(f"\n📦 Created {len(segments)} segments of ~{segment_size} tickers each")
    return segments


def save_filtered_tickers(viable_tickers, output_dir='ticker_data/'):
    """
    Save filtered tickers to files:
    1. Simple list of ticker symbols
    2. Detailed CSV with metrics
    3. Segmented files for batch processing
    """
    timestamp = datetime.now().strftime('%Y%m%d')

    # Convert to DataFrame
    df = pd.DataFrame(viable_tickers)

    # Sort by market cap (largest first)
    df = df.sort_values('market_cap', ascending=False).reset_index(drop=True)

    # Save detailed CSV
    csv_filename = f'{output_dir}filtered_tickers_{timestamp}.csv'
    df.to_csv(csv_filename, index=False)
    print(f"\n💾 Saved detailed ticker data to: {csv_filename}")

    # Save simple ticker list
    ticker_list_filename = f'{output_dir}filtered_tickers_{timestamp}.txt'
    with open(ticker_list_filename, 'w') as f:
        f.write('\n'.join(df['ticker'].tolist()))
    print(f"💾 Saved ticker list to: {ticker_list_filename}")

    # # Create segments
    # segments = create_segments(df['ticker'].tolist(), segment_size=500)

    # # Save each segment
    # for idx, segment in enumerate(segments):
    #     segment_filename = f'{output_dir}filtered_tickers_{timestamp}_segment_{idx}.txt'
    #     with open(segment_filename, 'w') as f:
    #         f.write('\n'.join(segment))
    #     print(f"💾 Saved segment {idx} ({len(segment)} tickers) to: {segment_filename}")

    return df


def analyze_ticker_distribution(df):
    """
    Print statistics about the filtered ticker distribution
    """
    print("\n" + "="*60)
    print("📊 TICKER DISTRIBUTION ANALYSIS")
    print("="*60)

    # Market cap tiers
    large_cap = df[df['market_cap'] >= 10e9]
    mid_cap = df[(df['market_cap'] >= 2e9) & (df['market_cap'] < 10e9)]
    small_cap = df[df['market_cap'] < 2e9]

    print(f"\nMarket Cap Distribution:")
    print(f"  Large Cap (≥$10B): {len(large_cap)} tickers ({len(large_cap)/len(df)*100:.1f}%)")
    print(f"  Mid Cap ($2B-$10B): {len(mid_cap)} tickers ({len(mid_cap)/len(df)*100:.1f}%)")
    print(f"  Small Cap (<$2B): {len(small_cap)} tickers ({len(small_cap)/len(df)*100:.1f}%)")

    # Price distribution
    print(f"\nPrice Distribution:")
    print(f"  $5-$20: {len(df[(df['price'] >= 5) & (df['price'] < 20)])} tickers")
    print(f"  $20-$100: {len(df[(df['price'] >= 20) & (df['price'] < 100)])} tickers")
    print(f"  $100+: {len(df[df['price'] >= 100])} tickers")

    # Volume distribution
    print(f"\nVolume Distribution:")
    print(f"  100K-500K: {len(df[(df['volume'] >= 100000) & (df['volume'] < 500000)])} tickers")
    print(f"  500K-1M: {len(df[(df['volume'] >= 500000) & (df['volume'] < 1000000)])} tickers")
    print(f"  1M+: {len(df[df['volume'] >= 1000000])} tickers")

    # Sector distribution
    if 'sector' in df.columns:
        print(f"\n🏭 Sector Distribution:")
        sector_counts = df['sector'].value_counts().sort_values(ascending=False)
        for sector, count in sector_counts.items():
            percentage = (count / len(df)) * 100
            print(f"  {sector:30} - {count:4} tickers ({percentage:5.1f}%)")

        print(f"\n  Total sectors: {len(sector_counts)}")
        print(f"  Unknown/Missing: {len(df[df['sector'] == 'Unknown'])} tickers")

    # Top 10 by market cap
    print(f"\nTop 10 by Market Cap:")
    for _, row in df.head(10).iterrows():
        sector_info = f" ({row['sector']})" if 'sector' in df.columns else ""
        print(f"  {row['ticker']:6} - ${row['market_cap']/1e9:.1f}B{sector_info}")

    print("="*60)


if __name__ == "__main__":

    # ========================================
    # STEP 1: Load and clean ticker list
    # ========================================

    print("="*60)
    print("🚀 TICKER PREPROCESSING PIPELINE")
    print("="*60)

    # Load all tickers
    print("\n📂 Loading ticker list...")
    with open('all_tickers.txt', 'r') as f:
        all_tickers = [line.strip() for line in f if line.strip()]
        # all_tickers = all_tickers[:50]

    print(f"✅ Loaded {len(all_tickers)} tickers")

    # Clean the list (remove warrants, units, etc.)
    clean_tickers = clean_ticker_list(all_tickers)

    # ========================================
    # STEP 2: Filter by basic criteria
    # ========================================

    # Adjust these parameters based on your needs:
    # - Lower min_market_cap to include more small caps
    # - Lower min_price to include penny stocks (risky!)
    # - Lower min_volume to include less liquid stocks

    viable_tickers, failed_tickers, error_details = filter_by_basic_criteria(
        clean_tickers,
        min_market_cap=100e6,   # $100M minimum
        min_price=1.0,           # $5 minimum
        min_volume=100000,       # 100K shares minimum
        max_retries=3,           # Retry failed requests up to 3 times
        base_delay=0.25,         # 0.25 second base delay between requests
        checkpoint_interval=100  # Save progress every 100 tickers
    )

    # ========================================
    # STEP 3: Save results
    # ========================================

    if viable_tickers:
        df = save_filtered_tickers(viable_tickers)

        # Show distribution analysis
        analyze_ticker_distribution(df)

        # Save failed tickers for potential retry
        timestamp = datetime.now().strftime('%Y%m%d')
        if failed_tickers:
            failed_file = f'ticker_data/failed_tickers_{timestamp}.txt'
            with open(failed_file, 'w') as f:
                f.write('\n'.join(failed_tickers))
            print(f"\n💾 Saved {len(failed_tickers)} failed tickers to: {failed_file}")

        # Save error details for analysis
        if any(error_details.values()):
            error_file = f'ticker_data/error_details_{timestamp}.txt'
            with open(error_file, 'w') as f:
                f.write("ERROR DETAILS\n")
                f.write("=" * 60 + "\n\n")
                for error_type, tickers in error_details.items():
                    if tickers:
                        f.write(f"{error_type.upper()} ({len(tickers)} tickers):\n")
                        f.write('\n'.join(tickers))
                        f.write('\n\n')
            print(f"💾 Saved error details to: {error_file}")

        print(f"\n✅ Preprocessing complete!")
        print(f"📊 Reduced from {len(all_tickers)} to {len(viable_tickers)} viable tickers")
        print(f"📈 Ready for detailed analysis!")
    else:
        print("\n⚠️  No viable tickers found. Consider relaxing filter criteria.")

    print("\n" + "="*60)
