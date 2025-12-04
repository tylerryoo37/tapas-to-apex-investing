# Ticker Filtering System - Usage Guide

## Overview
This system reduces your 6,664 tickers to a manageable, high-quality list by filtering out:
- Warrants, units, rights (~664 removed)
- Low market cap stocks (< $100M)
- Low-priced stocks (< $5)
- Low volume stocks (< 100K daily)

**Expected result**: ~2,000-3,000 high-quality, tradeable stocks divided into segments of 500 for efficient processing.

---

## Step-by-Step Workflow

### Step 1: Run the Preprocessing Script

```bash
cd /Users/tylerryoo/venv-tyler/tapas-to-apex-investing
python 00_ticker_preprocessing.py
```

**What it does:**
1. Loads all 6,664 tickers from `all_tickers.txt`
2. Removes warrants, units, preferred shares (6,664 → 6,000)
3. Filters by market cap, price, volume (6,000 → ~2,000-3,000)
4. Creates multiple output files (see below)

**Output files created:**
- `filtered_tickers_YYYYMMDD.txt` - Simple list of viable tickers
- `filtered_tickers_YYYYMMDD.csv` - Detailed data with market cap, price, volume
- `filtered_tickers_YYYYMMDD_segment_0.txt` - First 500 tickers
- `filtered_tickers_YYYYMMDD_segment_1.txt` - Next 500 tickers
- `filtered_tickers_YYYYMMDD_segment_2.txt` - And so on...

**Estimated runtime:** 30-60 minutes (depends on API rate limits)

---

### Step 2: Use Filtered Tickers in Your Analysis

Open `tta_automation_v2/01_data_extraction_fundamentals.py` and uncomment one of these options:

#### Option A: Process ONE segment (500 tickers) - **RECOMMENDED for testing**
```python
ticker_type = 'filtered_segment_0'
filtered_date = '20250107'  # Update this to match your file
segment_num = 0  # Change to 1, 2, 3... for different segments
with open(f'../filtered_tickers_{filtered_date}_segment_{segment_num}.txt', 'r') as f:
    my_tickers = [line.strip() for line in f if line.strip()]
```

#### Option B: Process ALL filtered tickers at once
```python
ticker_type = 'filtered_all'
filtered_date = '20250107'  # Update this to match your file
with open(f'../filtered_tickers_{filtered_date}.txt', 'r') as f:
    my_tickers = [line.strip() for line in f if line.strip()]
```

---

## Adjusting Filter Criteria

If you want more/fewer tickers, edit these parameters in `00_ticker_preprocessing.py` (lines ~154):

```python
viable_tickers, failed_tickers = filter_by_basic_criteria(
    clean_tickers,
    min_market_cap=100e6,   # Lower = more small caps (try 50e6 for $50M)
    min_price=5.0,          # Lower = more penny stocks (try 1.0)
    min_volume=100000       # Lower = less liquid stocks (try 50000)
)
```

**Conservative (fewer stocks):**
- `min_market_cap=500e6` ($500M)
- `min_price=10.0` ($10)
- `min_volume=500000` (500K)

**Aggressive (more stocks):**
- `min_market_cap=50e6` ($50M)
- `min_price=2.0` ($2)
- `min_volume=50000` (50K)

---

## Recommended Weekly Workflow

### Week 1: Process segment 0 (first 500 tickers)
```python
segment_num = 0
```

### Week 2: Process segment 1 (next 500 tickers)
```python
segment_num = 1
```

### Week 3: Process segment 2
```python
segment_num = 2
```

### Week 4: Process segment 3
```python
segment_num = 3
```

**Result:** Full coverage of all high-quality stocks in 4-6 weeks!

---

## Expected Results

### Before Filtering:
- **6,664 total tickers**
- Includes warrants, units, penny stocks, illiquid stocks
- Not practical to analyze all

### After Filtering:
- **~2,000-3,000 viable tickers** (actual number depends on your criteria)
- Split into **4-6 segments** of ~500 tickers each
- Each segment takes ~2-4 hours to process
- High-quality, tradeable stocks only

---

## Tips

1. **Start with ONE segment** to test your setup
2. **Review the CSV file** to understand what stocks passed filters
3. **Adjust criteria** if you're getting too many/few stocks
4. **Process different segments** on different days to stay within API limits
5. **Re-run preprocessing monthly** to get updated market conditions

---

## Troubleshooting

**"Too many tickers still"**
→ Increase min_market_cap and min_price in the preprocessing script

**"Not enough tickers"**
→ Lower the filter criteria (but be cautious with penny stocks)

**"API rate limit errors"**
→ Increase the sleep time in the preprocessing script (line ~173):
```python
time.sleep(0.2)  # Increase from 0.1 to 0.2 or 0.3
```

**"File not found error"**
→ Make sure you update the `filtered_date` variable to match your actual file date

---

## Quick Start Command Sequence

```bash
# 1. Run preprocessing (do this ONCE)
cd /Users/tylerryoo/venv-tyler/tapas-to-apex-investing
python 00_ticker_preprocessing.py

# 2. Edit your analysis script
# Open tta_automation_v2/01_data_extraction_fundamentals.py
# Uncomment Option 3 (filtered tickers)
# Update the filtered_date to match your file

# 3. Run analysis on first segment
cd tta_automation_v2
python 01_data_extraction_fundamentals.py
```

---

Good luck with your analysis! 🚀
