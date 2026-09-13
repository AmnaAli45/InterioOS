"""Small, dependency-free helpers for turning BOQ text into 3D scene items."""

import json
import re
from typing import Any


CATEGORY_KEYWORDS = {
    "furniture": ("bed", "wardrobe", "sofa", "table", "chair", "cabinet", "shelf", "desk", "stool"),
    "lighting": ("light", "led", "lamp", "chandelier", "downlight", "electrical"),
    "finish": ("paint", "tile", "floor", "flooring", "wallpaper", "ceiling", "marble", "laminate"),
    "soft furnishing": ("curtain", "blind", "rug", "carpet", "cushion", "upholstery"),
    "decor": ("mirror", "plant", "decor", "art", "vase"),
}


def _category_for(name: str, category: str = "") -> str:
    text = f"{name} {category}".lower()
    for item_category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return item_category
    return "other"


def _item(name: str, category: str = "") -> dict[str, str]:
    clean_name = re.sub(r"\s+", " ", name).strip(" -*|:;,.\t")
    return {"name": clean_name, "category": _category_for(clean_name, category)}


def _items_from_json(text: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for match in re.finditer(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.IGNORECASE | re.DOTALL):
        try:
            value: Any = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if not isinstance(value, list):
            continue
        for entry in value:
            if isinstance(entry, dict) and entry.get("name"):
                items.append(_item(str(entry["name"]), str(entry.get("category", ""))))
        if items:
            return items
    return items


def parse_boq_items(boq_text: str) -> list[dict[str, str]]:
    """Extract unique named materials/furnishings from flexible BOQ text."""
    if not boq_text:
        return []

    json_items = _items_from_json(boq_text)
    if json_items:
        return _unique_items(json_items)

    items: list[dict[str, str]] = []
    for line in boq_text.splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) >= 3:
            # Repository format: Category | Item Name | Quantity | Unit | Notes
            offset = 1 if not cells[0] else 0
            candidate_index = offset + 1 if len(cells) > offset + 1 else offset
            candidate = cells[candidate_index]
            category = cells[offset]
            if candidate and not re.fullmatch(r"[-: ]+", candidate) and candidate.lower() not in {"item", "item name", "name", "quantity"}:
                items.append(_item(candidate, category))
            continue

        plain_line = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line)
        for category, keywords in CATEGORY_KEYWORDS.items():
            keyword = next((word for word in keywords if re.search(rf"\b{re.escape(word)}\b", plain_line, re.IGNORECASE)), None)
            if keyword:
                items.append(_item(plain_line.split(":", 1)[0], category))
                break

    return _unique_items(items)


def _unique_items(items: list[dict[str, str]]) -> list[dict[str, str]]:
    unique: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in items:
        key = item["name"].lower()
        if key and key not in seen and len(key) > 1:
            seen.add(key)
            unique.append(item)
    return unique
