# Tapas to Apex Investing v2: High-Performance Data Pipeline

**Optimized, Robust, and Scalable Stock Analysis**

Version 2 of the Tapas to Apex Investing automation suite focuses on **efficiency, reliability, and scale**. It introduces a dedicated preprocessing stage to filter tickers *before* heavy data extraction, significantly reducing API calls and processing time while improving data quality.

## 🚀 Key Improvements in v2

*   **Smart Pre-filtering**: `00_ticker_preprocessing.py` rapidly scans thousands of tickers to filter out illiquid, micro-cap, or invalid securities (warrants, units, rights) before deep analysis.
*   **Robust Error Handling**: Implements exponential backoff retry logic for 429 (Rate Limit) and network errors.
*   **Checkpointing**: Saves progress every 100 tickers during preprocessing, allowing you to resume interrupted runs without starting over.
*   **Ticker Cleaning**: Automatically detects and removes non-common stock tickers (e.g., `ABCW` warrants, `XYZU` units, `DEF-P` preferreds).
*   **Segmentation**: Capabilities to split large ticker lists into manageable segments for batch processing.

## 📋 Repository Structure

```
tta_automation_v2/
├── 00_ticker_preprocessing.py          # FAST: Filters raw ticker lists by cap/price/vol
├── 01_data_extraction_fundamentals.py  # DEEP: Extracts 55+ metrics for filtered tickers
├── all_tickers.txt                     # Input list of all potential tickers
├── ticker_data/                        # Directory for checkpoints and results
│   ├── filtered_tickers_[date].csv     # Result of Step 0
│   └── error_details_[date].txt        # Log of failed tickers
├── README_TICKER_FILTERING.md          # Detailed guide on filtering logic
├── RETRY_LOGIC_IMPROVEMENTS.md         # Technical details on error handling
└── SECTOR_SEGMENTATION_GUIDE.md        # Guide for sector-based analysis
```

## ⚙️ Workflow

### Step 0: Ticker Preprocessing (`00_ticker_preprocessing.py`)
**Goal**: Reduce the universe of 10,000+ tickers to a high-quality list of investable assets.

This script performs a lightweight API call to check basic criteria:
*   **Market Cap**: > $100M (default)
*   **Price**: > $1.00 (default)
*   **Volume**: > 100k avg daily (default)
*   **Asset Type**: Removes warrants, units, preferred shares.

**Usage**:
```bash
python 00_ticker_preprocessing.py
```
*Output*: Generates `ticker_data/filtered_tickers_YYYYMMDD.csv` and `filtered_tickers_YYYYMMDD.txt`.

### Step 1: Deep Data Extraction (`01_data_extraction_fundamentals.py`)
**Goal**: Extract comprehensive fundamental, valuation, and momentum metrics for the *filtered* list.

This script takes the high-quality list from Step 0 and performs the deep-dive extraction found in v1, but with improved session management and error handling.

**Usage**:
1. Open `01_data_extraction_fundamentals.py`
2. Update the `ticker_type` configuration to point to your filtered file:
   ```python
   # Option 3: Use PRE-FILTERED tickers
   ticker_type = 'filtered_all'
   filtered_date = '20250107'  # Match your file date
   ```
3. Run the script:
   ```bash
   python 01_data_extraction_fundamentals.py
   ```

## 📊 Features & Logic

### Ticker Cleaning Logic
The `clean_ticker_list` function automatically excludes:
*   **Warrants**: Ending in `W`, `WS`, `WT`.
*   **Units**: Ending in `U`.
*   **Preferreds**: Containing `-P`, `-PR`.
*   **Rights**: Ending in `R` (with length > 4).
*   **Special**: Containing `^` or `~`.

### Retry & Recovery
*   **Rate Limits (429)**: Waits and retries with exponential backoff (0.25s -> 0.75s -> 2.25s).
*   **Checkpoints**: Progress is saved to `ticker_data/preprocessing_checkpoint.csv`. If the script crashes, it automatically resumes from the last checkpoint.

## 🔧 Configuration

You can adjust filtering thresholds in `00_ticker_preprocessing.py`:

```python
viable_tickers, failed_tickers, error_details = filter_by_basic_criteria(
    clean_tickers,
    min_market_cap=100e6,   # $100M
    min_price=1.0,          # $1.00
    min_volume=100000,      # 100k shares
    max_retries=3
)
```

## 📈 Next Steps
After running this pipeline, you will have a clean, high-quality dataset (`stock_data_current_...csv`) ready for:
1.  **Screening** (using v1's `02_ticker_selection.ipynb`)
2.  **Analysis** (using v1's `03_fundamentals_analysis.ipynb`)
## 🗺️ Roadmap & Vision

### Objective
To build a sophisticated, automated investment research engine that:
1.  **Casts a Wider Net**: Efficiently surveils the entire U.S. stock market, not just a handful of tickers.
2.  **Modular & Scalable**: Moves away from manual, single-ticker analysis to automated, batch processing of sectors and portfolios.
3.  **AI-Powered Insights**: Integrates LLM APIs (Gemini) to generate "owner-level" understanding of companies and actionable buy/sell signals.
4.  **Portfolio Management**: Provides intelligent monitoring of existing holdings, distinguishing between short-term trades and long-term compounders.

### 🚀 Development Priorities

#### 1. Broadening the Net (Surveillance)
*   **Enhanced Filtering**: Refine `00_ticker_preprocessing.py` to filter by Market Cap, Price, and Volume.
*   **Sector Segmentation**: Add sector/industry columns to partition data. This allows for sector-specific analysis (e.g., "Analyze all SaaS companies under $10B").
*   **Web Search Integration**: Supplement static financial metrics with live web search to capture recent earnings calls, guidance changes, and breaking news (VGEO integration).

#### 2. Modularization & Architecture
*   **Refactor Ticker Selection**: Convert `02_ticker_selection.ipynb` into a robust Python module (`ticker_selection.py`) with reusable classes.
*   **LLM Integration**:
    *   Create a dedicated `llm_prompts.py` to manage system prompts.
    *   Implement an API wrapper (Gemini) to automate analysis.
    *   **Goal**: "Analyze these 50 tickers" -> System outputs a ranked list with summaries, instead of manually running a notebook 50 times.

#### 3. Portfolio Intelligence
*   **"Owner's Mindset"**: Generate reports that help you understand the business model, moat, and risks of every company you own.
*   **Actionable Monitoring**:
    *   Daily/Bi-weekly reports on sector trends.
    *   Alerts for when the "narrative changes" (e.g., thesis drift).
    *   Clear distinction between Short-Term opportunities and Long-Term holds.
*   **Portfolio Feed**: Feed current holdings into the system to get recommendations on rebalancing, adding to winners, or cutting losers.

#### 4. Advanced Analytics (Above & Beyond)
*   **Statistical Models**: Incorporate regression analysis and mean reversion models.
*   **Prompt Engineering**: Utilize advanced prompting techniques (e.g., Chain-of-Thought) to improve stock selection accuracy.
*   **Daily Sector Reports**: Automated briefings on which sectors are heating up or cooling down.

---
**"Understand each company I’m investing in as if I own it."**
