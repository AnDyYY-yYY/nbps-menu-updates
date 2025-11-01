"""
menu_scraper_selenium.py

This script uses Selenium to fetch daily menu information from the Nutrislice web pages for North Broward Prep by automating a headless browser. It accepts the Nutrislice terms-of-use by clicking the "View Menus" button and then scrapes breakfast, lunch, dinner and brunch (weekends) menus for boarding, plus lunch menus for lower and middle/high schools. It uses BeautifulSoup to parse the HTML and prints the menu items for the current date.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime

# Mapping of locations to their Nutrislice slugs
SCHOOL_SLUGS = {
    "boarding": "boarding-menu",
    "lower": "lower",
    "middle_high": "boarding-menu",  # Middle/Upper lunch uses boarding menu slug
}

# Meals by location; brunch is only fetched on weekends
MEALS_BY_LOCATION = {
    "boarding": ["breakfast", "lunch", "dinner", "brunch"],
    "lower": ["lunch"],
    "middle_high": ["lunch"],
}

def accept_terms(driver: webdriver.Chrome) -> None:
    """
    Accept the Nutrislice terms by clicking the "View Menus" button if it exists.
    """
    driver.get("https://nbps.flikisdining.com/menu")
    try:
        button = driver.find_element(By.XPATH, "//button[contains(., 'View Menus')]")
        button.click()
    except Exception:
        # If the button is not found, assume terms have been accepted or not required
        pass

def fetch_menu_html(driver: webdriver.Chrome, slug: str, meal: str, date: datetime) -> str:
    """
    Load the menu page for a given slug, meal, and date and return the page HTML.
    """
    date_str = date.strftime("%Y-%m-%d")
    url = f"https://nbps.flikisdining.com/menu/{slug}/{meal}/{date_str}"
    driver.get(url)
    return driver.page_source

def parse_menu_items_from_html(html: str) -> list:
    """
    Parse menu item names from the HTML using BeautifulSoup.
    """
    soup = BeautifulSoup(html, "html.parser")
    items = []
    # The site uses various classes for menu items; try multiple selectors.
    for selector in [".name", ".food-name", ".menu-item-name"]:
        for el in soup.select(selector):
            text = el.get_text(strip=True)
            if text:
                items.append(text)
    # Remove duplicates while preserving order
    unique_items = []
    seen = set()
    for item in items:
        if item not in seen:
            unique_items.append(item)
            seen.add(item)
    return unique_items

def get_daily_menus(date: datetime) -> dict:
    """
    Scrape the daily menus for all configured locations and meals.
    """
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    accept_terms(driver)
    results = {}
    weekday = date.weekday()  # 0=Monday, 6=Sunday
    for location, meals in MEALS_BY_LOCATION.items():
        slug = SCHOOL_SLUGS[location]
        menu_by_meal = {}
        for meal in meals:
            if meal == "brunch" and weekday not in (5, 6):
                # Only fetch brunch on weekends
                continue
            try:
                html = fetch_menu_html(driver, slug, meal, date)
                items = parse_menu_items_from_html(html)
                menu_by_meal[meal] = items
            except Exception as e:
                menu_by_meal[meal] = {"error": str(e)}
        results[location] = menu_by_meal
    driver.quit()
    return results

def format_output(menus: dict, date: datetime) -> str:
    """
    Format the scraped menu data for printing.
    """
    lines = [f"Menu for {date.strftime('%A, %B %d, %Y')}\n"]
    for location, meals in menus.items():
        lines.append(f"== {location.replace('_', ' ').title()} ==")
        for meal, items in meals.items():
            lines.append(f"\n{meal.title()}")
            if isinstance(items, dict) and 'error' in items:
                lines.append(f"  Error fetching menu: {items['error']}")
                continue
            if not items:
                lines.append("  No items available.")
                continue
            for item in items:
                lines.append(f"  - {item}")
            lines.append("")
    return "\n".join(lines)

def main() -> None:
    date = datetime.now()
    menus = get_daily_menus(date)
    print(format_output(menus, date))

if __name__ == "__main__":
    main()
