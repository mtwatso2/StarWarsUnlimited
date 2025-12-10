# Star Wars Unlimited Price Guide Scraper

A Python-based web scraper and data cleaner for TCGplayer Star Wars Unlimited price guides. This tool automatically fetches card pricing data and formats it into clean, sorted CSV files ready for inventory tracking.

## Features

- Scrapes price guide data from TCGplayer for all Star Wars Unlimited sets
- Cleans and normalizes card names, types, and numbering
- Intelligently sorts cards by location/character with proper variant grouping
- Exports clean CSV files with Quantity column for inventory management

## Supported Sets

- Spark of Rebellion
- Shadows of the Galaxy
- Twilight of the Republic
- Jump to Lightspeed
- Legends of the Force
- Secrets of Power

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Required Packages

Install the required dependencies using pip:
```bash
pip install playwright beautifulsoup4
```

After installing Playwright, you need to install the browser binaries:
```bash
playwright install chromium
```

### Package Details

- **playwright**: Headless browser automation for scraping dynamic web pages
- **beautifulsoup4**: HTML parsing library for extracting table data
- **pandas**: Data manipulation and CSV processing
- **csv**: Built-in Python module (no installation needed)
- **re**, **unicodedata**, **asyncio**: Built-in Python modules (no installation needed)

## Usage

### 1. Scrape Price Guide Data

Run the scraper to fetch current pricing data from TCGplayer:
```bash
python scrape.py
```

This will create `*_raw.csv` files for each set.

### 2. Clean the Data

Process the raw CSV files into clean, sorted format:

```bash
python clean.py
```

This will create cleaned CSV files (without `_raw` suffix) ready for use.

## Output Format

The cleaned CSV files contain the following columns:

- **Name**: Card name with variants (e.g., "Theed Palace // TIE Fighter")
- **Type**: Card type (Normal, Hyperspace, Foil, etc.)
- **Rarity**: Card rarity
- **Number**: Card number in set
- **Quantity**: Empty column for tracking your inventory

## File Structure

```
├── scrape.py # Web scraper script
├── clean.py # Data cleaning script
├── *_raw.csv # Raw scraped data (generated)
├── *.csv # Cleaned data files (generated)
└── README.md # This file
```

## Notes

- The scraper runs with a visible browser window (`headless=False`). Change to `headless=True` in `scrape.py` if you prefer background execution.
- A 5-second delay is included to ensure JavaScript content loads completely.
- Card names are normalized to handle encoding issues and special characters.
- Variants are sorted alphabetically by suffix, then by card type.

## License

This project is provided as-is for personal use.
