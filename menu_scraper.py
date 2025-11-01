"""
menu_notifier.py
This script fetches daily menu information by scraping the Nutrislice web pages for North Broward Prep and prints them. It uses BeautifulSoup to parse the HTML pages for boarding, lower, and middle/high schools, and extracts menu items for the current date. Configure school slugs and meal types accordingly.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Base URL for NBPS menu site
BASE_URL = "https://nbps.flikisdining.com/menu"

# Slugs for school locations
SCHOOL_SLUGS = {
    "boarding": "boarding-menu",
    "lower": "lower",
    "middle_high": "boarding-menu",  # middle/high uses boarding lunch
}

# Meal types per location
MEALS_BY_LOCATION = {
    "boarding": ["breakfast", "lunch", "dinner", "brunch"],
    "lower": ["lunch"],
    "middle_high": ["lunch"],
}

def fetch_menu_html(school_slug: str, meal_type: str, date: datetime) -> str:
    """
    Build the URL for the menu page for a given date and fetch the HTML content.
    """
    date_str = date.strftime("%Y-%m-%d")
    url = f"{BASE_URL}/{school_slug}/{meal_type}/{date_str}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text

def parse_menu_items_from_html(html: str) -> list[str]:
    """
    Parse menu items from Nutrislice HTML page.
    This function tries to extract all food item names listed on the page.
    """
    soup = BeautifulSoup(html, "html.parser")
    items: list[str] = []
    # Nutrislice uses 'food-name' or similar classes for item names; use multiple selectors
    for tag in soup.select("[class*='food-name'], .menu-item-name, ns-meal-item .name"):
        text = tag.get_text(strip=True)
        if text and text not in items:
            items.append(text)
    return items

def get_daily_menus(date: datetime) -> dict:
    """Fetch and parse menus for all configured locations and meal types."""
    results: dict[str, dict] = {}
    weekday = date.weekday()  # Monday=0, Sunday=6
    for location, meals in MEALS_BY_LOCATION.items():
        menu_by_meal: dict[str, list] = {}
        slug = SCHOOL_SLUGS[location]
        for meal in meals:
            if meal == "brunch" and weekday not in (5, 6):
                # brunch only on weekends
                continue
            try:
                html = fetch_menu_html(slug, meal, date)
                items = parse_menu_items_from_html(html)
                menu_by_meal[meal] = items
            except Exception as e:
                menu_by_meal[meal] = {"error": str(e)}
        results[location] = menu_by_meal
    return results

def format_output(menus: dict, date: datetime) -> str:
    """Format the scraped menu data for printing."""
    lines: list[str] = [f"Menu for {date.strftime('%A, %B %d, %Y')}\n"]
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
