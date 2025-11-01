"""
menu_notifier.py
This script fetches daily menu information and nutritional details from Nutrislice for North Broward Prep (Boarding School, Lower School, Middle/Upper School), and prints them. Configure the district slug and school slugs according to your Nutrislice site.
"""

import requests
import datetime

# Configuration: update these slugs if needed.
DISTRICT_SLUG = "nbps"  # District slug from Nutrislice (e.g., nbps or flikisdining). See lookup.nutrislice.com for your site.
SCHOOL_SLUGS = {
    "boarding": "boarding-menu",
    "lower": "lower",
    # Middle/Upper lunch uses the boarding menu lunch according to school guidelines.
    "middle_high": "boarding-menu",
}

# Define which meals to fetch for each location. Use "brunch" only on weekends.
MEALS_BY_LOCATION = {
    "boarding": ["breakfast", "lunch", "dinner", "brunch"],
    "lower": ["lunch"],
    "middle_high": ["lunch"],
}

def build_api_url(district: str, school_slug: str, meal_type: str, date: datetime.date) -> str:
    """Construct the Nutrislice API URL for the given parameters."""
    return (
        f"https://{district}.api.nutrislice.com/menu/api/weeks/"
        f"school/{school_slug}/menu-type/{meal_type}/"
        f"{date.year}/{date.month:02d}/{date.day:02d}/?format=json"
    )

def fetch_menu_for_meal(district: str, school_slug: str, meal_type: str, date: datetime.date) -> dict:
    """Fetch the menu data for a particular meal via Nutrislice API."""
    url = build_api_url(district, school_slug, meal_type, date)
    response = requests.get(url, timeout=10)
    # If the API returns 404 or 500, you may need to adjust the district or school slug.
    response.raise_for_status()
    return response.json()

def parse_menu_items(menu_json: dict, date: datetime.date) -> list:
    """
    Parse the Nutrislice API response to extract menu items and their nutrient info.
    Returns a list of dictionaries with 'name', 'nutrients', and 'allergens'.
    """
    menu_items = []
    date_str = date.strftime("%Y-%m-%d")
    weeks = menu_json.get("weeks", [])
    for week in weeks:
        for day in week.get("days", []):
            # The 'date' field may have format "YYYY-MM-DD"
            if day.get("date") == date_str:
                for menu in day.get("menu_items", []):
                    # Each 'menu' might represent a category (e.g., 'Hot Entrees').
                    items = menu.get("items", [])
                    for item in items:
                        food = item.get("food", {})
                        menu_items.append({
                            "name": food.get("name"),
                            "nutrients": food.get("nutrients", {}),
                            "allergens": food.get("allergens", []),
                        })
    return menu_items

def get_daily_menus(date: datetime.date | None = None) -> dict:
    """Fetch menus for all configured locations and meals for the given date."""
    if date is None:
        date = datetime.date.today()
    results: dict[str, dict] = {}
    # Determine if weekend for boarding brunch.
    weekday = date.weekday()  # Monday=0, Sunday=6
    for location, meals in MEALS_BY_LOCATION.items():
        items_by_meal: dict[str, list] = {}
        for meal in meals:
            # Only fetch brunch on weekends (Saturday=5, Sunday=6).
            if meal == "brunch" and weekday not in (5, 6):
                continue
            school_slug = SCHOOL_SLUGS[location]
            try:
                data = fetch_menu_for_meal(DISTRICT_SLUG, school_slug, meal, date)
                menu_items = parse_menu_items(data, date)
                items_by_meal[meal] = menu_items
            except Exception as exc:
                # If an error occurs (e.g., incorrect slugs), store the error.
                items_by_meal[meal] = {"error": str(exc)}
        results[location] = items_by_meal
    return results

def format_menu_output(menus: dict, date: datetime.date) -> str:
    """Format the menu data into a human-readable text block."""
    lines: list[str] = [f"Menu for {date.strftime('%A, %B %d, %Y')}\n"]
    for location, meals in menus.items():
        lines.append(f"== {location.replace('_', ' ').title()} ==")
        for meal, items in meals.items():
            lines.append(f"\n{meal.title()}")
            if isinstance(items, dict) and "error" in items:
                lines.append(f"  Error fetching menu: {items['error']}")
                continue
            if not items:
                lines.append("  No items available.")
                continue
            for item in items:
                name = item['name']
                nutrients = item['nutrients']
                allergens = item.get('allergens', [])
                nutrient_info = ", ".join([f"{k}: {v}" for k, v in nutrients.items()]) if nutrients else "N/A"
                allergen_info = ", ".join(allergens) if allergens else "None"
                lines.append(f"  - {name} (Allergens: {allergen_info}; Nutrients: {nutrient_info})")
        lines.append("")  # Add an extra newline between locations
    return "\n".join(lines)

def main() -> None:
    date = datetime.date.today()
    menus = get_daily_menus(date)
    output = format_menu_output(menus, date)
    print(output)

if __name__ == "__main__":
    main()
