from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from openai import OpenAI
from pymongo import ASCENDING
from pymongo.database import Database

from .csv_importer import normalize_text, package_cost
from .db import load_environment
from .ingredient_search import search_ingredients
from .recipe_search import get_recipe_by_id, search_recipes

APP_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_PROMPT_PATH = APP_ROOT / "grocery-ai-prompt-engineering.md"
DEFAULT_MODEL = "gpt-4o-mini"
CHAT_HISTORY_LIMIT = 16
MAX_SERVINGS = 50

VIETNAMESE_NUMBER_WORDS = {
    "mot": 1,
    "hai": 2,
    "ba": 3,
    "bon": 4,
    "nam": 5,
    "sau": 6,
    "bay": 7,
    "tam": 8,
    "chin": 9,
    "muoi": 10,
}

STOPWORDS = {
    "ban",
    "can",
    "cho",
    "de",
    "duoc",
    "gi",
    "giup",
    "goi",
    "hom",
    "lam",
    "lieu",
    "minh",
    "mon",
    "mua",
    "muon",
    "nay",
    "nau",
    "nguyen",
    "hay",
    "kiem",
    "tim",
    "toi",
    "tu",
    "van",
    "voi",
    "an",
}

CART_ACTION_WORDS = {
    "bo",
    "loai",
    "xoa",
    "ra",
    "khoi",
    "danh",
    "sach",
    "toi",
    "minh",
    "da",
    "co",
    "roi",
    "san",
    "khong",
    "mua",
    "can",
    "nguyen",
    "lieu",
    "mon",
    "tang",
    "giam",
    "them",
    "bot",
    "so",
    "luong",
}

FOOD_SCOPE_PHRASES = {
    "an",
    "bua",
    "com",
    "di cho",
    "do an",
    "gi cung duoc",
    "goi y",
    "goi y mon",
    "gio hang",
    "mon",
    "mua thuc pham",
    "nau",
    "nguyen lieu",
    "sao cung duoc",
    "thanh toan",
    "thuc pham",
    "tuy",
}

ALLERGY_ALIASES = {
    "hai san": ["hai san", "ca", "tom", "muc"],
    "tom cua hai san": ["hai san", "ca", "tom", "muc"],
    "tom": ["tom"],
    "cua": ["cua"],
    "muc": ["muc"],
    "ca": ["ca", "hai san"],
    "trung": ["trung"],
    "dau phu": ["dau phu", "dau chay"],
    "hanh": ["hanh", "hanh la", "hanh tay", "hanh tim"],
    "thit lon": ["thit lon", "thit heo", "heo", "lon"],
}

ALLERGY_DISPLAY_LABELS = {
    "tom": "tôm",
    "cua": "cua",
    "muc": "mực",
    "ca": "cá",
    "hai san": "hải sản",
    "trung": "trứng",
    "dau phu": "đậu phụ",
    "hanh": "hành",
    "thit lon": "thịt lợn",
}

ALLERGY_CANONICAL_LABELS = {
    "heo": "thit lon",
    "lon": "thit lon",
    "thit heo": "thit lon",
    "thit lon": "thit lon",
}

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "check_recipe_ingredients",
            "description": (
                "Search MongoDB for a requested dish or recipe, then return the matched recipe, "
                "real inventory ingredients, prices, stock state, VietGAP state, estimated cost, "
                "and allergy conflicts. Call this before recommending any dish or cart."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's requested dish, recipe, or natural-language food request.",
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Search MongoDB inventory products by food name, category, substitute, or note. "
                "Call this before recommending standalone products."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Product, ingredient, category, or substitute search query.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum products to return.",
                        "minimum": 1,
                        "maximum": 20,
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remember_user_allergies",
            "description": (
                "Persist allergy or cannot-eat food memory for the current user. "
                "Call this whenever the user says they are allergic to, cannot eat, "
                "or must avoid a food."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "allergies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Food allergy or cannot-eat terms to remember.",
                    },
                    "note": {
                        "type": "string",
                        "description": "Short source note from the user's message.",
                    },
                },
                "required": ["allergies"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_current_cart_items",
            "description": (
                "Remove ingredients from the user's current ingredient list/cart when the user says "
                "they already have an item, do not want it, want to bỏ/loại/xóa it, or asks to remove it. "
                "Use this for follow-up messages after a menu has already been created."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Ingredient names or partial names to remove from the current list.",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Short reason from the user's message.",
                    },
                },
                "required": ["items"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_current_cart_item_quantity",
            "description": (
                "Increase or decrease one ingredient quantity in the user's current ingredient list/cart. "
                "Use this when the user asks to tăng/giảm số lượng or when UI +/- controls send an update."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string",
                        "description": "Ingredient name or partial name to adjust.",
                    },
                    "action": {
                        "type": "string",
                        "enum": ["increase", "decrease"],
                        "description": "Whether to increase or decrease the quantity.",
                    },
                    "steps": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "description": "Number of adjustment steps.",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Short reason from the user's message.",
                    },
                },
                "required": ["item", "action"],
                "additionalProperties": False,
            },
        },
    },
]


@lru_cache
def _load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()


@lru_cache
def _get_openai_client() -> OpenAI:
    load_environment()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in .env")
    return OpenAI(api_key=api_key)


def _get_openai_model() -> str:
    load_environment()
    return (os.getenv("OPENAI_MODEL") or DEFAULT_MODEL).strip()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_memory_indexes(db: Database) -> None:
    db.user_memories.create_index([("userId", ASCENDING)], unique=True)


def get_user_memory(db: Database, user_id: str) -> dict[str, Any]:
    _ensure_memory_indexes(db)
    memory = db.user_memories.find_one({"userId": user_id}) or {}
    return {
        "userId": user_id,
        "allergies": memory.get("allergies", []),
        "allergyNote": memory.get("allergyNote", ""),
        "allergySourceNote": memory.get("allergySourceNote", ""),
        "currentCart": memory.get("currentCart"),
        "chatHistory": memory.get("chatHistory", [])[-CHAT_HISTORY_LIMIT:],
    }


def _append_chat_history(db: Database, user_id: str, user_message: str, assistant_reply: str) -> None:
    _ensure_memory_indexes(db)
    now = _now()
    entries = [
        {"role": "user", "content": user_message.strip(), "createdAt": now},
        {"role": "assistant", "content": assistant_reply.strip(), "createdAt": now},
    ]
    db.user_memories.update_one(
        {"userId": user_id},
        {
            "$set": {"userId": user_id, "updatedAt": now},
            "$setOnInsert": {"createdAt": now, "allergies": []},
            "$push": {"chatHistory": {"$each": entries, "$slice": -CHAT_HISTORY_LIMIT}},
        },
        upsert=True,
    )


def _finalize_chat_response(
    db: Database,
    user_id: str,
    message: str,
    response: dict[str, Any],
) -> dict[str, Any]:
    _append_chat_history(db, user_id, message, str(response.get("reply") or ""))
    response["memory"] = get_user_memory(db, user_id)
    return response


def save_user_allergies(
    db: Database,
    user_id: str,
    allergies: list[str],
    note: str | None = None,
) -> dict[str, Any]:
    _ensure_memory_indexes(db)
    memory = get_user_memory(db, user_id)
    by_normalized = {
        item["normalized"]: item
        for item in memory.get("allergies", [])
        if item.get("normalized")
    }

    for allergy in allergies:
        label = str(allergy or "").strip()
        normalized = normalize_text(label)
        if not normalized:
            continue
        normalized = ALLERGY_CANONICAL_LABELS.get(normalized, normalized)
        label = ALLERGY_DISPLAY_LABELS.get(normalized, label)
        by_normalized[normalized] = {"label": label, "normalized": normalized}

    updated_allergies = sorted(by_normalized.values(), key=lambda item: item["normalized"])
    allergy_note = (
        f"Dị ứng: {', '.join(item['label'] for item in updated_allergies)}"
        if updated_allergies
        else ""
    )
    db.user_memories.update_one(
        {"userId": user_id},
        {
            "$set": {
                "userId": user_id,
                "allergies": updated_allergies,
                "allergyNote": allergy_note,
                "allergySourceNote": note or "",
                "lastNote": note or "",
                "updatedAt": _now(),
            },
            "$setOnInsert": {"createdAt": _now()},
        },
        upsert=True,
    )
    return {"userId": user_id, "allergies": updated_allergies}


def save_current_cart(
    db: Database,
    user_id: str,
    matched_recipe: dict[str, Any] | None,
    ingredients: list[dict[str, Any]],
    total_cost: int,
) -> dict[str, Any]:
    _ensure_memory_indexes(db)
    normalized_ingredients = [_normalize_cart_item(item) for item in ingredients]
    cart = {
        "matchedRecipe": matched_recipe,
        "ingredients": normalized_ingredients,
        "totalEstimatedCostVnd": _cart_total(normalized_ingredients) if normalized_ingredients else int(total_cost or 0),
        "updatedAt": _now(),
    }
    db.user_memories.update_one(
        {"userId": user_id},
        {
            "$set": {"userId": user_id, "currentCart": cart, "updatedAt": _now()},
            "$setOnInsert": {"createdAt": _now(), "allergies": []},
        },
        upsert=True,
    )
    return cart


def _normalize_cart_item(item: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(item)
    is_seasoning = _is_seasoning(normalized)
    current_quantity = float(normalized.get("soLuongChoKhauPhanCoBan") or 0)
    base_step = float(normalized.get("baseQuantityStep") or current_quantity or 1)
    base_line_cost = float(
        normalized.get("baseLineCostVnd")
        or normalized.get("chiPhiUocTinhVnd")
        or package_cost(base_step, str(normalized.get("donViSoLuong") or ""), normalized)
        or normalized.get("giaVnd")
        or 0
    )
    normalized["baseQuantityStep"] = base_step
    normalized["baseLineCostVnd"] = base_line_cost
    normalized["quantityMultiplier"] = float(normalized.get("quantityMultiplier") or 1)
    normalized["displayMode"] = "seasoning" if is_seasoning else "priced"
    normalized["showPrice"] = not is_seasoning
    normalized["chiPhiUocTinhVnd"] = (
        0 if is_seasoning else int(round(base_line_cost * normalized["quantityMultiplier"]))
    )
    if is_seasoning:
        normalized["seasoningLineCostVnd"] = int(
            round(base_line_cost * normalized["quantityMultiplier"])
        )
        normalized["purchaseSelected"] = bool(normalized.get("purchaseSelected", False))
        normalized["giaVnd"] = None
        normalized["quyCachDongGoi"] = None
        normalized["baseLineCostVnd"] = 0
        normalized.pop("package_qty", None)
        normalized.pop("package_unit", None)
    return normalized


def _is_seasoning(item: dict[str, Any]) -> bool:
    return normalize_text(item.get("danhMuc", "")) == "gia vi"


def _cart_total(ingredients: list[dict[str, Any]]) -> int:
    return sum(
        int(item.get("chiPhiUocTinhVnd") or 0)
        for item in ingredients
        if not _is_seasoning(item)
    )


def _matches_remove_term(ingredient: dict[str, Any], remove_term: str) -> bool:
    normalized_term = normalize_text(remove_term)
    cleaned_term = " ".join(
        token for token in normalized_term.split() if token not in CART_ACTION_WORDS
    )
    normalized_term = cleaned_term or normalized_term
    if not normalized_term:
        return False

    haystack = normalize_text(
        " ".join(
            str(value or "")
            for value in [
                ingredient.get("tenNguyenLieu"),
                ingredient.get("danhMuc"),
                ingredient.get("nguyenLieuThayThe"),
                ingredient.get("ghiChu"),
            ]
        )
    )
    term_tokens = normalized_term.split()
    return normalized_term in haystack or all(token in haystack for token in term_tokens)


def remove_current_cart_items(
    db: Database,
    user_id: str,
    items: list[str],
    reason: str | None = None,
) -> dict[str, Any]:
    memory = get_user_memory(db, user_id)
    cart = memory.get("currentCart") or {}
    ingredients = cart.get("ingredients") or []

    if not ingredients:
        return {
            "status": "EMPTY_CART",
            "removedItems": [],
            "remainingIngredients": [],
            "totalEstimatedCostVnd": 0,
            "reason": reason or "",
        }

    removed = []
    remaining = []
    for ingredient in ingredients:
        if any(_matches_remove_term(ingredient, item) for item in items):
            removed.append(ingredient)
        else:
            remaining.append(ingredient)

    total_cost = _cart_total(remaining)
    updated_cart = save_current_cart(
        db,
        user_id,
        cart.get("matchedRecipe"),
        remaining,
        total_cost,
    )

    return {
        "status": "CART_UPDATED" if removed else "ITEM_NOT_FOUND",
        "requestedItems": items,
        "removedItems": removed,
        "remainingIngredients": remaining,
        "matchedRecipe": updated_cart.get("matchedRecipe"),
        "totalEstimatedCostVnd": total_cost,
        "reason": reason or "",
    }


def update_current_cart_item_quantity(
    db: Database,
    user_id: str,
    item: str,
    action: str,
    steps: int = 1,
    reason: str | None = None,
) -> dict[str, Any]:
    memory = get_user_memory(db, user_id)
    cart = memory.get("currentCart") or {}
    ingredients = [_normalize_cart_item(ingredient) for ingredient in cart.get("ingredients", [])]

    if not ingredients:
        return {
            "status": "EMPTY_CART",
            "changedItem": None,
            "remainingIngredients": [],
            "totalEstimatedCostVnd": 0,
            "reason": reason or "",
        }

    matched_index = next(
        (index for index, ingredient in enumerate(ingredients) if _matches_remove_term(ingredient, item)),
        None,
    )
    if matched_index is None:
        return {
            "status": "ITEM_NOT_FOUND",
            "changedItem": None,
            "remainingIngredients": ingredients,
            "matchedRecipe": cart.get("matchedRecipe"),
            "totalEstimatedCostVnd": _cart_total(ingredients),
            "reason": reason or "",
        }

    changed = dict(ingredients[matched_index])
    step_count = max(1, min(int(steps or 1), 10))
    multiplier = float(changed.get("quantityMultiplier") or 1)
    if action == "increase":
        multiplier += step_count
    elif multiplier <= 1:
        multiplier = max(0.5, multiplier - (0.5 * step_count))
    else:
        multiplier = max(0.5, multiplier - step_count)

    base_step = float(changed.get("baseQuantityStep") or changed.get("soLuongChoKhauPhanCoBan") or 1)
    changed["quantityMultiplier"] = multiplier
    changed["soLuongChoKhauPhanCoBan"] = base_step * multiplier
    changed["chiPhiUocTinhVnd"] = (
        0
        if _is_seasoning(changed)
        else int(round(float(changed.get("baseLineCostVnd") or 0) * multiplier))
    )

    ingredients[matched_index] = changed
    total_cost = _cart_total(ingredients)
    updated_cart = save_current_cart(db, user_id, cart.get("matchedRecipe"), ingredients, total_cost)

    return {
        "status": "CART_UPDATED",
        "action": action,
        "changedItem": changed,
        "remainingIngredients": updated_cart.get("ingredients", []),
        "matchedRecipe": updated_cart.get("matchedRecipe"),
        "totalEstimatedCostVnd": total_cost,
        "reason": reason or "",
    }


def update_current_cart_servings(
    db: Database,
    user_id: str,
    servings: int,
    reason: str | None = None,
) -> dict[str, Any]:
    memory = get_user_memory(db, user_id)
    cart = memory.get("currentCart") or {}
    ingredients = cart.get("ingredients") or []
    matched_recipe = cart.get("matchedRecipe") or {}
    recipe_id = matched_recipe.get("maMonAn")

    if not ingredients or not recipe_id:
        return {
            "status": "EMPTY_CART",
            "action": "servings",
            "remainingIngredients": [],
            "totalEstimatedCostVnd": 0,
            "requestedServings": servings,
            "reason": reason or "",
        }

    recipe_detail = get_recipe_by_id(db, recipe_id)
    if not recipe_detail:
        return {
            "status": "ITEM_NOT_FOUND",
            "action": "servings",
            "remainingIngredients": ingredients,
            "matchedRecipe": matched_recipe,
            "totalEstimatedCostVnd": _cart_total(ingredients),
            "requestedServings": servings,
            "reason": reason or "",
        }

    current_ids = {
        item.get("maNguyenLieu")
        for item in ingredients
        if item.get("maNguyenLieu")
    }
    selected_seasonings = {
        item.get("maNguyenLieu")
        for item in ingredients
        if item.get("maNguyenLieu") and item.get("purchaseSelected")
    }
    source_ingredients = [
        item
        for item in recipe_detail["nguyenLieu"]
        if item.get("maNguyenLieu") in current_ids
    ]
    scaled_ingredients = _scale_ingredients_for_servings(
        source_ingredients,
        int(recipe_detail.get("soKhauPhanCoBan") or 1),
        servings,
    )
    for ingredient in scaled_ingredients:
        if ingredient.get("maNguyenLieu") in selected_seasonings:
            ingredient["purchaseSelected"] = True

    updated_recipe = {
        "maMonAn": recipe_detail["maMonAn"],
        "tenMonAn": recipe_detail["tenMonAn"],
        "soKhauPhanCoBan": recipe_detail["soKhauPhanCoBan"],
        "requestedServings": servings,
        "servingsScale": servings / max(1, int(recipe_detail.get("soKhauPhanCoBan") or 1)),
        "thoiGianPhut": recipe_detail["thoiGianPhut"],
        "doKho": recipe_detail["doKho"],
    }
    total_cost = _cart_total([_normalize_cart_item(item) for item in scaled_ingredients])
    updated_cart = save_current_cart(db, user_id, updated_recipe, scaled_ingredients, total_cost)

    return {
        "status": "CART_UPDATED",
        "action": "servings",
        "remainingIngredients": updated_cart.get("ingredients", []),
        "matchedRecipe": updated_cart.get("matchedRecipe"),
        "totalEstimatedCostVnd": updated_cart.get("totalEstimatedCostVnd", total_cost),
        "requestedServings": servings,
        "reason": reason or "",
    }


def _extract_local_allergies(message: str) -> list[str]:
    normalized = normalize_text(message)
    matches = re.findall(
        r"(?:di ung|khong an duoc|khong dung duoc|can tranh|tranh)\s+(.+)",
        normalized,
    )
    allergies: list[str] = []
    known_allergy_terms = set(ALLERGY_DISPLAY_LABELS) | {
        alias
        for aliases in ALLERGY_ALIASES.values()
        for alias in aliases
    }
    filler_tokens = {
        "cac",
        "thu",
        "may",
        "mon",
        "do",
        "an",
        "va",
        "voi",
        "nua",
        "nhe",
        "nha",
    }

    for match in matches:
        safe_segment = re.split(
            r"\b(?:nen|nhung|hom nay|toi muon|minh muon|hay goi y|goi y|muon an|muon nau)\b",
            match,
            maxsplit=1,
        )[0]
        safe_segment = re.sub(r"^(?:voi|cac|mon|thuc pham)\s+", "", safe_segment).strip()
        segment_tokens = [token for token in safe_segment.split() if token not in filler_tokens]
        for token in segment_tokens:
            if token in known_allergy_terms:
                allergies.append(token)

        for term in re.split(r"\s*(?:,|/|\bva\b|\bor\b)\s*", safe_segment):
            clean = term.strip()
            clean_tokens = [token for token in clean.split() if token not in filler_tokens]
            clean = " ".join(clean_tokens)
            has_known_token = any(token in known_allergy_terms for token in clean_tokens)
            if (
                1 <= len(clean_tokens) <= 4
                and clean not in STOPWORDS
                and (clean in known_allergy_terms or not has_known_token)
            ):
                allergies.append(clean)

    deduped = []
    seen = set()
    for allergy in allergies:
        normalized_allergy = normalize_text(allergy)
        normalized_allergy = ALLERGY_CANONICAL_LABELS.get(normalized_allergy, normalized_allergy)
        if normalized_allergy and normalized_allergy not in seen:
            seen.add(normalized_allergy)
            deduped.append(normalized_allergy)
    return deduped


def _format_quantity(value: Any, unit: str) -> str:
    number = float(value or 0)
    formatted = str(int(number)) if number.is_integer() else f"{number:g}"
    return f"{formatted} {unit}".strip()


def _format_price(value: Any) -> str:
    return f"{int(value or 0):,} VND".replace(",", ".")


def _clean_query(message: str) -> str:
    tokens = normalize_text(message).split()
    content_tokens = [token for token in tokens if token not in STOPWORDS]
    return " ".join(content_tokens)


def _parse_positive_int(value: str) -> int | None:
    normalized = normalize_text(value)
    if normalized.isdigit():
        parsed = int(normalized)
    else:
        parsed = VIETNAMESE_NUMBER_WORDS.get(normalized)
    if parsed is None or parsed <= 0:
        return None
    return min(parsed, MAX_SERVINGS)


def _extract_serving_count(message: str) -> int | None:
    normalized = normalize_text(message)
    number_pattern = r"\d{1,2}|mot|hai|ba|bon|nam|sau|bay|tam|chin|muoi"
    unit_pattern = r"nguoi|khau phan|phan|suat|cap|doi|gia dinh"
    patterns = [
        rf"(?:cho|khoang|tam|tầm)?\s*({number_pattern})\s*({unit_pattern})",
        rf"({unit_pattern})\s*({number_pattern})",
    ]
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, normalized)
        if match:
            num_str = match.group(1) if i == 0 else match.group(2)
            unit_str = match.group(2) if i == 0 else match.group(1)
            parsed = _parse_positive_int(num_str)
            if parsed:
                if "cap" in unit_str or "doi" in unit_str:
                    return parsed * 2
                return parsed
    return None


def _scale_ingredients_for_servings(
    ingredients: list[dict[str, Any]],
    base_servings: int,
    requested_servings: int | None,
) -> list[dict[str, Any]]:
    base = max(1, int(base_servings or 1))
    requested = max(1, int(requested_servings or base))
    scale = requested / base
    scaled_ingredients = []

    for ingredient in ingredients:
        scaled = dict(ingredient)
        base_quantity = float(
            scaled.get("recipeBaseQuantity")
            or scaled.get("soLuongChoKhauPhanCoBan")
            or 0
        )
        scaled_quantity = base_quantity * scale
        scaled["recipeBaseQuantity"] = base_quantity
        scaled["recipeBaseServings"] = base
        scaled["requestedServings"] = requested
        scaled["servingsScale"] = scale
        scaled["soLuongChoKhauPhanCoBan"] = scaled_quantity
        scaled["chiPhiUocTinhVnd"] = package_cost(
            scaled_quantity,
            str(scaled.get("donViSoLuong") or ""),
            scaled,
        )
        scaled_ingredients.append(scaled)

    return scaled_ingredients


def _has_normalized_phrase(normalized_message: str, phrase: str) -> bool:
    return re.search(rf"(?:^| ){re.escape(phrase)}(?: |$)", normalized_message) is not None


def _has_any_normalized_phrase(normalized_message: str, phrases: set[str] | list[str]) -> bool:
    return any(_has_normalized_phrase(normalized_message, phrase) for phrase in phrases)


def _has_new_recipe_intent(normalized_message: str) -> bool:
    return _has_any_normalized_phrase(
        normalized_message,
        [
            "muon an",
            "muon nau",
            "toi nau",
            "lam mon",
            "nau mon",
            "cho toi nguyen lieu",
        ],
    )


def _forced_cart_tool_name(message: str, memory: dict[str, Any]) -> str | None:
    if not (memory.get("currentCart") or {}).get("ingredients"):
        return None

    normalized = normalize_text(message)
    if _has_new_recipe_intent(normalized):
        return None

    if _has_any_normalized_phrase(normalized, ["tang", "them so luong", "nhieu hon"]):
        return "update_current_cart_item_quantity"
    if _has_any_normalized_phrase(normalized, ["giam", "bot so luong", "it hon"]):
        return "update_current_cart_item_quantity"
    if _has_any_normalized_phrase(
        normalized,
        [
            "bo",
            "loai",
            "xoa",
            "da co",
            "co san",
            "khong mua",
            "khong can",
        ],
    ):
        return "remove_current_cart_items"
    return None


def _recipe_score(message_text: str, recipe: dict[str, Any]) -> float:
    recipe_name = normalize_text(recipe.get("tenMonAn", ""))
    name_tokens = recipe_name.split()
    if not name_tokens:
        return 0

    message_tokens = set(message_text.split())
    hits = sum(1 for token in name_tokens if token in message_tokens)
    score = hits / len(name_tokens)

    if recipe_name in message_text:
        score += 1.0

    return score


def _find_best_recipe(db: Database, message: str) -> dict[str, Any] | None:
    normalized_message = normalize_text(message)
    recipes = list(db.recipes.find({}, {"maMonAn": 1, "tenMonAn": 1, "searchText": 1}))
    scored = sorted(
        ((_recipe_score(normalized_message, recipe), recipe) for recipe in recipes),
        key=lambda item: item[0],
        reverse=True,
    )

    if scored and scored[0][0] >= 0.6:
        return scored[0][1]

    cleaned_query = _clean_query(message)
    if cleaned_query:
        fallback = search_recipes(db, cleaned_query, limit=1)
        if fallback:
            return {"maMonAn": fallback[0]["maMonAn"], "tenMonAn": fallback[0]["tenMonAn"]}

    return None


def _is_food_related_message(
    db: Database,
    message: str,
    forced_tool_name: str | None,
    local_allergies: list[str],
    memory: dict[str, Any],
) -> bool:
    normalized = normalize_text(message)
    if not normalized:
        return False
    if forced_tool_name or local_allergies or _has_new_recipe_intent(normalized):
        return True
    if _extract_serving_count(message) and (memory.get("currentCart") or {}).get("ingredients"):
        return True
    if _has_any_normalized_phrase(normalized, FOOD_SCOPE_PHRASES):
        return True
    if _find_best_recipe(db, message):
        return True

    cleaned_query = _clean_query(message)
    return bool(cleaned_query and search_ingredients(db, cleaned_query, limit=1))


def _out_of_scope_response(message: str, user_id: str, memory: dict[str, Any]) -> dict[str, Any]:
    return {
        "message": message,
        "userId": user_id,
        "status": "NEED_MORE_INFO",
        "matchedRecipe": None,
        "ingredients": [],
        "totalEstimatedCostVnd": 0,
        "reply": (
            "Mình là trợ lý mua sắm thực phẩm. Bạn hãy hỏi mình về món muốn nấu, "
            "nguyên liệu cần mua, dị ứng cần tránh hoặc chỉnh danh sách nguyên liệu nhé."
        ),
        "warnings": ["OUT_OF_SCOPE"],
        "suggestions": [],
        "removedAllergyIngredients": [],
        "agent": {"status": "NEED_MORE_INFO", "scope": "grocery_only"},
        "memory": memory,
    }


def _allergy_terms(allergy: dict[str, str]) -> list[str]:
    normalized = allergy.get("normalized", "")
    return [normalized, *ALLERGY_ALIASES.get(normalized, [])]


def _ingredient_conflicts_with_allergy(
    ingredient: dict[str, Any],
    allergy: dict[str, str],
) -> bool:
    ingredient_name = normalize_text(ingredient.get("tenNguyenLieu", ""))
    normalized_allergy = allergy.get("normalized", "")
    if normalized_allergy == "ca" and (
        ingredient_name.startswith("ca chua")
        or ingredient_name.startswith("ca rot")
    ):
        return False

    haystack = normalize_text(
        " ".join(
            str(value or "")
            for value in [
                ingredient.get("tenNguyenLieu"),
                ingredient.get("danhMuc"),
                ingredient.get("nguyenLieuThayThe"),
                ingredient.get("ghiChu"),
            ]
        )
    )
    return any(term and term in haystack for term in _allergy_terms(allergy))


def _find_allergy_conflicts(
    ingredients: list[dict[str, Any]],
    memory: dict[str, Any],
) -> list[dict[str, str]]:
    conflicts = []
    for ingredient in ingredients:
        for allergy in memory.get("allergies", []):
            if _ingredient_conflicts_with_allergy(ingredient, allergy):
                conflicts.append(
                    {
                        "maNguyenLieu": ingredient.get("maNguyenLieu", ""),
                        "tenNguyenLieu": ingredient.get("tenNguyenLieu", ""),
                        "allergy": allergy.get("label", allergy.get("normalized", "")),
                    }
                )
    return conflicts


def _tool_check_recipe_ingredients(
    db: Database,
    query: str,
    memory: dict[str, Any],
    message: str = "",
) -> dict[str, Any]:
    recipe = _find_best_recipe(db, query)
    if not recipe:
        return {
            "status": "PRODUCT_NOT_FOUND",
            "query": query,
            "matchedRecipe": None,
            "ingredients": [],
            "allergyConflicts": [],
        }

    recipe_detail = get_recipe_by_id(db, recipe["maMonAn"])
    if not recipe_detail:
        return {
            "status": "PRODUCT_NOT_FOUND",
            "query": query,
            "matchedRecipe": None,
            "ingredients": [],
            "allergyConflicts": [],
        }

    base_servings = int(recipe_detail.get("soKhauPhanCoBan") or 1)
    extracted_servings = _extract_serving_count(query)
    
    if not extracted_servings and message:
        extracted_servings = _extract_serving_count(message)

    if not extracted_servings:
        last_user_msg = next((m for m in reversed(memory.get("chatHistory", [])) if m.get("role") == "user"), None)
        if last_user_msg:
            extracted_servings = _extract_serving_count(last_user_msg.get("content", ""))

    servings_specified = extracted_servings is not None
    requested_servings = extracted_servings or 1
    ingredients = _scale_ingredients_for_servings(
        recipe_detail["nguyenLieu"],
        base_servings,
        requested_servings,
    )
    conflicts = _find_allergy_conflicts(ingredients, memory)
    conflict_ids = {conflict["maNguyenLieu"] for conflict in conflicts}
    safe_ingredients = [
        ingredient
        for ingredient in ingredients
        if ingredient.get("maNguyenLieu") not in conflict_ids
    ]
    return {
        "status": "ALLERGY_CONFLICT" if conflicts and not safe_ingredients else "APPROVED",
        "query": query,
        "matchedRecipe": {
            "maMonAn": recipe_detail["maMonAn"],
            "tenMonAn": recipe_detail["tenMonAn"],
            "soKhauPhanCoBan": recipe_detail["soKhauPhanCoBan"],
            "requestedServings": requested_servings,
            "servingsSpecified": servings_specified,
            "servingsScale": requested_servings / max(1, base_servings),
            "thoiGianPhut": recipe_detail["thoiGianPhut"],
            "doKho": recipe_detail["doKho"],
        },
        "ingredients": safe_ingredients,
        "totalEstimatedCostVnd": _cart_total([_normalize_cart_item(item) for item in safe_ingredients]),
        "unavailableIngredients": recipe_detail.get("nguyenLieuHetHang", []),
        "allergyConflicts": conflicts,
        "removedAllergyIngredients": conflicts,
        "knownAllergies": memory.get("allergies", []),
    }


def _tool_search_products(
    db: Database,
    query: str,
    limit: int,
    memory: dict[str, Any],
) -> dict[str, Any]:
    products = search_ingredients(db, query, limit=max(1, min(limit, 20)))
    conflicts = _find_allergy_conflicts(products, memory)
    conflict_ids = {item["maNguyenLieu"] for item in conflicts}
    available_products = [
        product
        for product in products
        if product.get("conHang") and product.get("maNguyenLieu") not in conflict_ids
    ]

    return {
        "status": "PRODUCT_NOT_FOUND" if not products else "APPROVED",
        "query": query,
        "products": products,
        "safeAvailableProducts": available_products,
        "allergyConflicts": conflicts,
        "knownAllergies": memory.get("allergies", []),
    }


def _build_agent_system_prompt(memory: dict[str, Any]) -> str:
    allergies = memory.get("allergies", [])
    allergies_text = ", ".join(item["label"] for item in allergies) if allergies else "none"
    current_cart = memory.get("currentCart") or {}
    current_recipe = (current_cart.get("matchedRecipe") or {}).get("tenMonAn")
    current_items = [
        item.get("tenNguyenLieu", "")
        for item in current_cart.get("ingredients", [])
        if item.get("tenNguyenLieu")
    ]
    current_cart_text = (
        f"{current_recipe or 'unknown recipe'}: {', '.join(current_items)}"
        if current_items
        else "none"
    )
    return f"""
{_load_system_prompt()}

## App Tool-Calling Extensions

Bạn đang chạy trong FastAPI backend và có tool để kiểm tra MongoDB inventory.

Quy tắc bắt buộc:
1. Trước khi gợi ý bất kỳ món, nguyên liệu, sản phẩm hoặc giỏ hàng nào, bạn phải gọi tool `check_recipe_ingredients` hoặc `search_products`.
2. Nếu người dùng nói họ dị ứng, không ăn được, hoặc cần tránh món gì, bạn phải gọi tool `remember_user_allergies`.
3. Tuyệt đối không đưa nguyên liệu có `allergyConflicts` vào giỏ hàng.
4. Nếu món người dùng yêu cầu có xung đột dị ứng, hãy loại nguyên liệu xung đột khỏi danh sách mua, cảnh báo ngắn gọn cho người dùng, và chỉ từ chối khi không còn nguyên liệu an toàn nào.
5. Chỉ dùng sản phẩm, giá, tồn kho và VietGAP từ tool output. Không tự bịa.
6. Nếu người dùng chỉ hỏi muốn ăn/nấu một món và không đưa ngân sách, vẫn gợi ý nguyên liệu trong database. Khi đó `summary.budget` là null và status là `APPROVED` nếu không có lỗi tồn kho/dị ứng.
7. Chỉ dùng `OVER_BUDGET` khi người dùng thật sự đưa ngân sách.
8. Nếu người dùng nói họ đã có sẵn một nguyên liệu, không muốn một nguyên liệu, hoặc muốn bỏ/loại/xóa nguyên liệu khỏi danh sách hiện tại, bạn phải gọi tool `remove_current_cart_items`.
	9. Nếu cùng một câu vừa yêu cầu nấu món vừa nói đã có sẵn nguyên liệu, trước tiên gọi `check_recipe_ingredients`, sau đó gọi `remove_current_cart_items` cho nguyên liệu đã có.
	10. Nếu người dùng nói tăng/giảm số lượng một nguyên liệu hoặc UI gửi yêu cầu +/- một nguyên liệu, bạn phải gọi tool `update_current_cart_item_quantity`.
	11. Trường `reply` là lời tư vấn hội thoại ngắn bằng tiếng Việt, khoảng 2-3 câu. Không liệt kê chi tiết từng nguyên liệu trong `reply` vì UI sẽ hiển thị danh sách nguyên liệu bên dưới.
	12. LƯU Ý KHI GỌI TOOL: Nếu người dùng nói số người ăn, bắt buộc đưa số đó vào tham số `query` của tool `check_recipe_ingredients`.
	13. QUAN TRỌNG: Nếu tool trả về `servingsSpecified` là `false` (nghĩa là người dùng chưa cung cấp số người ăn), BẮT BUỘC bạn phải thêm câu hỏi này vào `reply`: "Món này đang lấy mặc định cho X người, bạn muốn nấu cho mấy người ăn?".
	14. QUAN TRỌNG: Nếu tên món người dùng yêu cầu KHÁC với tên món trong `matchedRecipe`, TUYỆT ĐỐI KHÔNG tự động gán món gợi ý đó thành món người dùng yêu cầu. Bạn phải nói rõ: "Rất tiếc, hệ thống hiện không có công thức cho món [Món yêu cầu]. Bạn có muốn chuyển sang món [Tên matchedRecipe] không?".

Known user allergies for this user: {allergies_text}
Current ingredient list for this user: {current_cart_text}

	Final response must be valid JSON and include these keys:
{{
  "status": "APPROVED | OVER_BUDGET | PRODUCT_NOT_FOUND | ALLERGY_CONFLICT | MEMORY_UPDATED | CART_UPDATED | NEED_MORE_INFO",
        "reply": "short Vietnamese advisory chat text, not an ingredient list",
  "summary": {{
    "budget": null,
    "total_cost": 0,
    "remaining_budget": null
  }},
  "matched_recipe": null,
  "recommended_menu": [],
  "cart_items": [],
  "warnings": [],
  "suggestions": []
}}
	"""


def _history_messages(memory: dict[str, Any]) -> list[dict[str, str]]:
    messages = []
    for item in memory.get("chatHistory", [])[-10:]:
        role = item.get("role")
        content = str(item.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    return messages


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _parse_json_object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", value, flags=re.S)
        parsed = json.loads(match.group(0)) if match else {}
    return parsed if isinstance(parsed, dict) else {}


def _assistant_message_dict(message: Any) -> dict[str, Any]:
    data: dict[str, Any] = {"role": "assistant", "content": message.content}
    if message.tool_calls:
        data["tool_calls"] = [
            {
                "id": tool_call.id,
                "type": tool_call.type,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                },
            }
            for tool_call in message.tool_calls
        ]
    return data


def _execute_tool(
    db: Database,
    user_id: str,
    memory: dict[str, Any],
    name: str,
    arguments: dict[str, Any],
    message: str = "",
) -> tuple[dict[str, Any], dict[str, Any]]:
    if name == "check_recipe_ingredients":
        result = _tool_check_recipe_ingredients(db, str(arguments.get("query", "")), memory, message)
        if result.get("status") == "APPROVED" and result.get("ingredients"):
            save_current_cart(
                db,
                user_id,
                result.get("matchedRecipe"),
                result.get("ingredients", []),
                int(result.get("totalEstimatedCostVnd") or 0),
            )
            memory = get_user_memory(db, user_id)
        return result, memory

    if name == "search_products":
        result = _tool_search_products(
            db,
            str(arguments.get("query", "")),
            int(arguments.get("limit") or 10),
            memory,
        )
        return result, memory

    if name == "remember_user_allergies":
        result = save_user_allergies(
            db,
            user_id,
            [str(item) for item in arguments.get("allergies", [])],
            note=str(arguments.get("note", "")),
        )
        return {"status": "MEMORY_UPDATED", **result}, get_user_memory(db, user_id)

    if name == "remove_current_cart_items":
        result = remove_current_cart_items(
            db,
            user_id,
            [str(item) for item in arguments.get("items", [])],
            reason=str(arguments.get("reason", "")),
        )
        return result, get_user_memory(db, user_id)

    if name == "update_current_cart_item_quantity":
        result = update_current_cart_item_quantity(
            db,
            user_id,
            str(arguments.get("item", "")),
            str(arguments.get("action", "")),
            int(arguments.get("steps") or 1),
            reason=str(arguments.get("reason", "")),
        )
        return result, get_user_memory(db, user_id)

    return {"status": "UNKNOWN_TOOL", "tool": name}, memory


def _fallback_chat_response(
    message: str,
    memory: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    allergies = [item["label"] for item in memory.get("allergies", [])]
    allergy_text = f" Dị ứng đã nhớ: {', '.join(allergies)}." if allergies else ""
    return {
        "message": message,
        "userId": memory["userId"],
        "status": "OPENAI_ERROR",
        "matchedRecipe": None,
        "ingredients": [],
        "totalEstimatedCostVnd": 0,
        "reply": f"OpenAI đang lỗi nên mình chưa thể gợi ý giỏ hàng bằng agent.{allergy_text}",
        "warnings": [reason],
        "suggestions": [],
        "agent": {},
        "memory": memory,
    }


def _build_recipe_reply(
    matched_recipe: dict[str, Any] | None,
    ingredients: list[dict[str, Any]],
    total_cost: int,
    removed_allergy_items: list[dict[str, Any]] | None = None,
) -> str:
    if not matched_recipe or not ingredients:
        return "Mình đã kiểm tra database nhưng chưa có đủ nguyên liệu để gợi ý."
    requested_servings = int(
        matched_recipe.get("requestedServings")
        or matched_recipe.get("soKhauPhanCoBan")
        or 0
    )
    servings_text = f" cho {requested_servings} người" if requested_servings else ""
    allergy_note = ""
    if removed_allergy_items:
        removed_names = ", ".join(
            item.get("tenNguyenLieu", "")
            for item in removed_allergy_items
            if item.get("tenNguyenLieu")
        )
        if removed_names:
            allergy_note = f" Mình đã loại {removed_names} vì trùng với ghi nhớ dị ứng của bạn."

    return (
        f"Dựa trên yêu cầu của bạn, mình đã lên danh sách nguyên liệu cho món "
        f"{matched_recipe['tenMonAn']}{servings_text} ở bên dưới. Tổng dự kiến là {_format_price(total_cost)}. "
        "Bạn có thể tick bỏ món đã có, bấm +/- để chỉnh số lượng, hoặc bấm Chốt khi đồng ý."
        f"{allergy_note}"
    )


def _response_from_agent_json(
    message: str,
    user_id: str,
    memory: dict[str, Any],
    agent_json: dict[str, Any],
    last_recipe_tool_result: dict[str, Any] | None,
    last_cart_tool_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    status = agent_json.get("status") or "NEED_MORE_INFO"
    matched_recipe = agent_json.get("matched_recipe") or None
    ingredients: list[dict[str, Any]] = []
    total_cost = 0
    removed_allergy_items: list[dict[str, Any]] = []

    if last_recipe_tool_result and status not in {"PRODUCT_NOT_FOUND", "MEMORY_UPDATED"}:
        tool_recipe = last_recipe_tool_result.get("matchedRecipe")
        if isinstance(matched_recipe, str):
            matched_recipe = {"tenMonAn": matched_recipe}
        matched_recipe = {**tool_recipe, **(matched_recipe or {})} if tool_recipe else matched_recipe
        selected_ids = {
            item.get("maNguyenLieu") or item.get("product_id") or item.get("ingredient_id")
            for item in agent_json.get("cart_items", [])
            if isinstance(item, dict)
        }
        tool_ingredients = last_recipe_tool_result.get("ingredients", [])
        if selected_ids:
            selected_names = {
                normalize_text(str(item.get("tenNguyenLieu") or item.get("ingredient") or item.get("name") or ""))
                for item in agent_json.get("cart_items", [])
                if isinstance(item, dict)
            }
            ingredients = [
                item
                for item in tool_ingredients
                if item.get("maNguyenLieu") in selected_ids
                or normalize_text(item.get("tenNguyenLieu", "")) in selected_names
            ]
            if not ingredients:
                ingredients = tool_ingredients
        else:
            ingredients = tool_ingredients
        total_cost = int(last_recipe_tool_result.get("totalEstimatedCostVnd") or 0)
        removed_allergy_items = last_recipe_tool_result.get("removedAllergyIngredients", [])
        if status == "ALLERGY_CONFLICT" and ingredients:
            status = "APPROVED"
            agent_json["status"] = "APPROVED"

    if last_cart_tool_result:
        matched_recipe = last_cart_tool_result.get("matchedRecipe") or matched_recipe
        ingredients = last_cart_tool_result.get("remainingIngredients", [])
        total_cost = int(last_cart_tool_result.get("totalEstimatedCostVnd") or 0)

    summary = agent_json.get("summary") if isinstance(agent_json.get("summary"), dict) else {}
    total_cost = int(summary.get("total_cost") or total_cost or 0)
    reply = agent_json.get("reply") or "Mình cần thêm thông tin để gợi ý chính xác."

    if last_cart_tool_result:
        removed_names = [
            item.get("tenNguyenLieu", "")
            for item in last_cart_tool_result.get("removedItems", [])
            if item.get("tenNguyenLieu")
        ]
        changed_item = last_cart_tool_result.get("changedItem")
        action = last_cart_tool_result.get("action")
        if last_cart_tool_result.get("status") == "CART_UPDATED" and action == "servings":
            status = "CART_UPDATED"
            requested_servings = int(last_cart_tool_result.get("requestedServings") or 0)
            servings_text = f" cho {requested_servings} người" if requested_servings else ""
            reply = (
                f"Đã chỉnh danh sách nguyên liệu{servings_text}. "
                f"Tổng mới là {_format_price(total_cost)}."
            )
        elif last_cart_tool_result.get("status") == "CART_UPDATED" and changed_item:
            status = "CART_UPDATED"
            action_text = "tăng" if action == "increase" else "giảm"
            reply = (
                f"Đã {action_text} số lượng {changed_item.get('tenNguyenLieu')}. "
                f"Tổng mới là {_format_price(total_cost)}."
            )
        elif last_cart_tool_result.get("status") == "CART_UPDATED":
            status = "CART_UPDATED"
            reply = (
                f"Đã bỏ {', '.join(removed_names)} khỏi danh sách. "
                f"Tổng mới là {_format_price(total_cost)}."
            )
        elif last_cart_tool_result.get("status") == "ITEM_NOT_FOUND":
            status = "NEED_MORE_INFO"
            reply = "Mình chưa thấy nguyên liệu đó trong danh sách hiện tại."
        else:
            status = "NEED_MORE_INFO"
            reply = "Hiện chưa có danh sách nguyên liệu nào để chỉnh."
        agent_json["status"] = status
        agent_json["reply"] = reply

    if status == "OVER_BUDGET" and summary.get("budget") is None:
        status = "APPROVED"
        agent_json["status"] = "APPROVED"
        reply = _build_recipe_reply(matched_recipe, ingredients, total_cost, removed_allergy_items)
        agent_json["reply"] = reply
        agent_json["warnings"] = [
            warning
            for warning in agent_json.get("warnings", [])
            if "ngân sách" not in str(warning).lower() and "ngan sach" not in normalize_text(warning)
        ]
    elif status == "APPROVED" and matched_recipe and ingredients:
        if not reply or reply == "Mình cần thêm thông tin để gợi ý chính xác.":
            reply = _build_recipe_reply(matched_recipe, ingredients, total_cost, removed_allergy_items)
        elif removed_allergy_items:
            removed_names = ", ".join(
                item.get("tenNguyenLieu", "")
                for item in removed_allergy_items
                if item.get("tenNguyenLieu")
            )
            if removed_names and removed_names not in reply:
                reply = f"{reply} Mình đã loại {removed_names} vì trùng với ghi nhớ dị ứng của bạn."
        agent_json["reply"] = reply

    return {
        "message": message,
        "userId": user_id,
        "status": status,
        "matchedRecipe": matched_recipe,
        "ingredients": ingredients,
        "totalEstimatedCostVnd": total_cost,
        "reply": reply,
        "warnings": agent_json.get("warnings", []),
        "suggestions": agent_json.get("suggestions", []),
        "removedAllergyIngredients": removed_allergy_items,
        "agent": agent_json,
        "memory": memory,
    }


def _is_serving_change_intent(message: str) -> bool:
    import re
    normalized = normalize_text(message)
    cleaned = re.sub(r"(?:cho|thanh|doi thanh|nau cho)?\s*\d{1,2}\s*(?:nguoi|khau phan|phan|suat)(?:\s*an)?", "", normalized).strip()
    words = [w for w in cleaned.split() if w not in {"nhe", "nha", "di", "ban", "bot", "lam", "nau", "an", "thay", "doi", "thanh", "cho", "chinh", "toi", "muon", "mua"}]
    return len("".join(words)) <= 3


def build_chat_response(db: Database, message: str, user_id: str = "default") -> dict[str, Any]:
    user_id = (user_id or "default").strip()

    local_allergies = _extract_local_allergies(message)
    if local_allergies:
        save_user_allergies(db, user_id, local_allergies, note=message)

    memory = get_user_memory(db, user_id)
    forced_tool_name = _forced_cart_tool_name(message, memory)
    normalized_message = normalize_text(message)
    if not _is_food_related_message(db, message, forced_tool_name, local_allergies, memory):
        return _finalize_chat_response(
            db,
            user_id,
            message,
            _out_of_scope_response(message, user_id, memory),
        )

    requested_servings = _extract_serving_count(message)
    is_new_recipe_mentioned = bool(_find_best_recipe(db, message))
    if (
        requested_servings
        and (memory.get("currentCart") or {}).get("ingredients")
        and not _has_new_recipe_intent(normalized_message)
        and not forced_tool_name
        and not is_new_recipe_mentioned
        and _is_serving_change_intent(message)
    ):
        tool_result = update_current_cart_servings(
            db,
            user_id,
            requested_servings,
            reason="fast_path_servings",
        )
        memory = get_user_memory(db, user_id)
        response = _response_from_agent_json(
            message,
            user_id,
            memory,
            {"status": tool_result.get("status"), "reply": ""},
            None,
            tool_result,
        )
        return _finalize_chat_response(db, user_id, message, response)

    if forced_tool_name == "remove_current_cart_items":
        tool_result = remove_current_cart_items(db, user_id, [message], reason="fast_path_cart_remove")
        memory = get_user_memory(db, user_id)
        response = _response_from_agent_json(
            message,
            user_id,
            memory,
            {"status": tool_result.get("status"), "reply": ""},
            None,
            tool_result,
        )
        return _finalize_chat_response(db, user_id, message, response)

    if forced_tool_name == "update_current_cart_item_quantity":
        action = "increase" if _has_any_normalized_phrase(normalized_message, ["tang", "them so luong", "nhieu hon"]) else "decrease"
        tool_result = update_current_cart_item_quantity(
            db,
            user_id,
            message,
            action,
            steps=1,
            reason="fast_path_cart_quantity",
        )
        memory = get_user_memory(db, user_id)
        response = _response_from_agent_json(
            message,
            user_id,
            memory,
            {"status": tool_result.get("status"), "reply": ""},
            None,
            tool_result,
        )
        return _finalize_chat_response(db, user_id, message, response)

    if local_allergies and not _has_new_recipe_intent(normalized_message):
        memory = get_user_memory(db, user_id)
        allergies = ", ".join(item["label"] for item in memory.get("allergies", []))
        response = {
            "message": message,
            "userId": user_id,
            "status": "MEMORY_UPDATED",
            "matchedRecipe": None,
            "ingredients": [],
            "totalEstimatedCostVnd": 0,
            "reply": f"Mình đã ghi nhớ dị ứng của bạn: {allergies}. Khi gợi ý nguyên liệu, mình sẽ tự loại các món này khỏi danh sách.",
            "warnings": [],
            "suggestions": [],
            "removedAllergyIngredients": [],
            "agent": {"status": "MEMORY_UPDATED"},
            "memory": memory,
        }
        return _finalize_chat_response(db, user_id, message, response)

    forced_tool_used = False
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _build_agent_system_prompt(memory)},
        *_history_messages(memory),
        {"role": "user", "content": message},
    ]

    last_recipe_tool_result: dict[str, Any] | None = None
    last_cart_tool_result: dict[str, Any] | None = None
    agent_json: dict[str, Any] = {}

    try:
        for _ in range(5):
            tool_choice: Any = "auto"
            if forced_tool_name and not forced_tool_used:
                tool_choice = {"type": "function", "function": {"name": forced_tool_name}}

            response = _get_openai_client().chat.completions.create(
                model=_get_openai_model(),
                messages=messages,
                tools=TOOLS,
                tool_choice=tool_choice,
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            response_message = response.choices[0].message

            if not response_message.tool_calls:
                agent_json = _parse_json_object(response_message.content)
                break

            messages.append(_assistant_message_dict(response_message))
            if forced_tool_name:
                forced_tool_used = True

            for tool_call in response_message.tool_calls:
                name = tool_call.function.name
                arguments = _parse_json_object(tool_call.function.arguments)
                tool_result, memory = _execute_tool(db, user_id, memory, name, arguments, message)
                if name == "check_recipe_ingredients":
                    last_recipe_tool_result = tool_result
                if name == "remove_current_cart_items":
                    last_cart_tool_result = tool_result
                if name == "update_current_cart_item_quantity":
                    last_cart_tool_result = tool_result
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": name,
                        "content": _json_dumps(tool_result),
                    }
                )
        else:
            agent_json = {
                "status": "NEED_MORE_INFO",
                "reply": "Mình cần thêm thông tin để gợi ý chính xác.",
                "summary": {"budget": None, "total_cost": 0, "remaining_budget": None},
                "matched_recipe": None,
                "recommended_menu": [],
                "cart_items": [],
                "warnings": ["Tool calling loop reached the limit."],
                "suggestions": [],
            }
    except Exception as exc:
        return _finalize_chat_response(
            db,
            user_id,
            message,
            _fallback_chat_response(message, memory, exc.__class__.__name__),
        )

    if (
        forced_tool_name == "remove_current_cart_items"
        and (not last_cart_tool_result or last_cart_tool_result.get("status") == "ITEM_NOT_FOUND")
    ):
        retry_result = remove_current_cart_items(db, user_id, [message], reason="fallback_match_from_user_message")
        if retry_result.get("status") == "CART_UPDATED":
            last_cart_tool_result = retry_result

    if (
        forced_tool_name == "update_current_cart_item_quantity"
        and (not last_cart_tool_result or last_cart_tool_result.get("status") == "ITEM_NOT_FOUND")
    ):
        normalized_message = normalize_text(message)
        action = "increase" if _has_any_normalized_phrase(normalized_message, ["tang", "them so luong", "nhieu hon"]) else "decrease"
        retry_result = update_current_cart_item_quantity(
            db,
            user_id,
            message,
            action,
            steps=1,
            reason="fallback_match_from_user_message",
        )
        if retry_result.get("status") == "CART_UPDATED":
            last_cart_tool_result = retry_result

    memory = get_user_memory(db, user_id)
    response = _response_from_agent_json(
        message,
        user_id,
        memory,
        agent_json,
        last_recipe_tool_result,
        last_cart_tool_result,
    )

    if response["status"] in {"APPROVED", "CART_UPDATED"} and response["ingredients"]:
        current_cart = save_current_cart(
            db,
            user_id,
            response.get("matchedRecipe"),
            response["ingredients"],
            response.get("totalEstimatedCostVnd", 0),
        )
        response["ingredients"] = current_cart.get("ingredients", response["ingredients"])
        response["totalEstimatedCostVnd"] = current_cart.get(
            "totalEstimatedCostVnd",
            response.get("totalEstimatedCostVnd", 0),
        )
        response["memory"] = get_user_memory(db, user_id)

    return _finalize_chat_response(db, user_id, message, response)
