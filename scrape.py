import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import csv


async def scrape_tcgplayer(url: str, output_csv: str) -> None:
    """
    Fetch a TCGplayer price guide page and export the main HTML table to a CSV file.

    This coroutine:
    - Launches a Chromium browser using Playwright.
    - Navigates to the given URL and waits for the page to finish loading.
    - Extracts the first relevant data table (preferably the TCGplayer price guide table).
    - Writes the table header and rows into a CSV file.
    """
    # Launch browser and navigate to URL
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Wait for network to be idle so JavaScript can populate the page
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(5000)

        html = await page.content()
        await browser.close()

    # Parse HTML and find the TCGplayer table
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", class_="tcg-table__table")
    if not table:
        # Fallback to first table on page
        table = soup.find("table")
        if not table:
            raise SystemExit("No <table> found. Inspect the page structure.")

    thead = table.find("thead")
    tbody = table.find("tbody")

    # Extract headers
    headers = [th.get_text(strip=True) for th in (thead.find_all("th") if thead else [])]
    print("HEADERS:", headers)

    # Extract data rows
    rows = []
    for tr in (tbody.find_all("tr") if tbody else table.find_all("tr")[1:]):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if cells:
            rows.append(cells)

    # Write to CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if headers:
            writer.writerow(headers)
        writer.writerows(rows)

    print(f"Wrote {len(rows)} data rows to {output_csv}")


# URLs to scrape and their corresponding output filenames
urls_and_files = [
    (
        "https://www.tcgplayer.com/categories/trading-and-collectible-card-games/"
        "star-wars-unlimited/price-guides/spark-of-rebellion",
        "spark_of_rebellion_raw.csv",
    ),
    (
        "https://www.tcgplayer.com/categories/trading-and-collectible-card-games/"
        "star-wars-unlimited/price-guides/shadows-of-the-galaxy",
        "shadows_of_the_galaxy_raw.csv",
    ),
    (
        "https://www.tcgplayer.com/categories/trading-and-collectible-card-games/"
        "star-wars-unlimited/price-guides/twilight-of-the-republic",
        "twilight_of_the_republic_raw.csv",
    ),
    (
        "https://www.tcgplayer.com/categories/trading-and-collectible-card-games/"
        "star-wars-unlimited/price-guides/jump-to-lightspeed",
        "jump_to_lightspeed_raw.csv",
    ),
    (
        "https://www.tcgplayer.com/categories/trading-and-collectible-card-games/"
        "star-wars-unlimited/price-guides/legends-of-the-force",
        "legends_of_the_force_raw.csv",
    ),
    (
        "https://www.tcgplayer.com/categories/trading-and-collectible-card-games/"
        "star-wars-unlimited/price-guides/secrets-of-power",
        "secrets_of_power_raw.csv",
    ),
]


async def main() -> None:
    """
    Orchestrate scraping for all configured TCGplayer price guide URLs.

    Iterates over the `urls_and_files` list and calls `scrape_tcgplayer`
    for each (url, output_csv) pair in sequence.
    """
    for url, output_csv in urls_and_files:
        print(f"Scraping {url} -> {output_csv}")
        await scrape_tcgplayer(url, output_csv)


if __name__ == "__main__":
    asyncio.run(main())
