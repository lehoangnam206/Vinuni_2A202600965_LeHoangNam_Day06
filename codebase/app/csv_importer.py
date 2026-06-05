from __future__ import annotations

import csv
import math
import re
import unicodedata
from pathlib import Path
from typing import Any

from pymongo import ASCENDING
from pymongo.database import Database

APP_ROOT = Path(__file__).resolve().parents[1]


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFD", text.strip().lower().replace("đ", "d"))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def to_int(value: str) -> int:
    return int(float(value)) if value not in ("", None) else 0


def to_float(value: str) -> float:
    return float(value) if value not in ("", None) else 0.0


def to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"yes", "true", "1", "y"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def ensure_indexes(db: Database) -> None:
    db.recipes.create_index([("maMonAn", ASCENDING)], unique=True)
    db.recipes.create_index([("searchText", ASCENDING)])
    db.recipes.create_index([("tags", ASCENDING)])

    db.ingredients.create_index([("maNguyenLieu", ASCENDING)], unique=True)
    db.ingredients.create_index([("tenNguyenLieuSearch", ASCENDING)])
    db.ingredients.create_index([("searchText", ASCENDING)])
    db.ingredients.create_index([("danhMuc", ASCENDING)])
    db.ingredients.create_index([("conHang", ASCENDING)])

    db.recipe_ingredients.create_index(
        [("maMonAn", ASCENDING), ("maNguyenLieu", ASCENDING)],
        unique=True,
    )
    db.recipe_ingredients.create_index([("maMonAn", ASCENDING), ("thuTu", ASCENDING)])
    db.recipe_ingredients.create_index([("maNguyenLieu", ASCENDING)])
    db.recipe_ingredients.create_index([("searchText", ASCENDING)])


def import_csv_to_mongo(db: Database, base_dir: Path = APP_ROOT, reset: bool = True) -> dict[str, Any]:
    recipes_csv = read_csv(base_dir / "recipes.csv")
    ingredients_csv = read_csv(base_dir / "ingredients.csv")
    recipe_ingredients_csv = read_csv(base_dir / "recipe_ingredients.csv")

    ensure_indexes(db)

    if reset:
        db.recipes.delete_many({})
        db.ingredients.delete_many({})
        db.recipe_ingredients.delete_many({})

    ingredients = []
    for row in ingredients_csv:
        tags = [
            row["ingredient_name"],
            row["category"],
            row["possible_substitute"],
            row["note"],
        ]
        doc = {
            "_id": row["ingredient_id"],
            "maNguyenLieu": row["ingredient_id"],
            "tenNguyenLieu": row["ingredient_name"],
            "tenNguyenLieuSearch": normalize_text(row["ingredient_name"]),
            "danhMuc": row["category"],
            "quyCachDongGoi": {
                "soLuong": to_float(row["package_qty"]),
                "donVi": row["package_unit"],
            },
            "giaVnd": to_int(row["price_vnd"]),
            "conHang": to_bool(row["available"]),
            "vietgapHoacSach": to_bool(row["is_clean_or_vietgap"]),
            "nguyenLieuThayThe": row["possible_substitute"],
            "ghiChu": row["note"],
            "searchText": normalize_text(" ".join(tags)),
        }
        ingredients.append(doc)

    recipes = []
    for row in recipes_csv:
        tags = [tag.strip() for tag in row["tags"].split(",") if tag.strip()]
        doc = {
            "_id": row["recipe_id"],
            "maMonAn": row["recipe_id"],
            "tenMonAn": row["recipe_name"],
            "loaiBua": row["meal_type"],
            "doKho": row["difficulty"],
            "soKhauPhanCoBan": to_int(row["base_servings"]),
            "thoiGianPhut": to_int(row["estimated_time_min"]),
            "tags": tags,
            "searchText": normalize_text(
                " ".join([row["recipe_name"], row["meal_type"], row["difficulty"], row["tags"]])
            ),
        }
        recipes.append(doc)

    recipe_ingredients = []
    for row in recipe_ingredients_csv:
        doc = {
            "_id": f"{row['recipe_id']}:{row['ingredient_id']}",
            "maMonAn": row["recipe_id"],
            "maNguyenLieu": row["ingredient_id"],
            "tenNguyenLieu": row["ingredient_name"],
            "thuTu": to_int(row["sequence_no"]),
            "soLuongChoKhauPhanCoBan": to_float(row["quantity_for_base_servings"]),
            "donViSoLuong": row["quantity_unit"],
            "batBuoc": row["required_or_optional"] == "required",
            "vaiTro": row["role"],
            "searchText": normalize_text(
                " ".join(
                    [
                        row["ingredient_name"],
                        row["quantity_unit"],
                        row["required_or_optional"],
                        row["role"],
                    ]
                )
            ),
        }
        recipe_ingredients.append(doc)

    if ingredients:
        db.ingredients.insert_many(ingredients, ordered=False)
    if recipes:
        db.recipes.insert_many(recipes, ordered=False)
    if recipe_ingredients:
        db.recipe_ingredients.insert_many(recipe_ingredients, ordered=False)

    return {
        "message": "Imported CSV files into MongoDB",
        "database": db.name,
        "collections": {
            "recipes": db.recipes.count_documents({}),
            "ingredients": db.ingredients.count_documents({}),
            "recipe_ingredients": db.recipe_ingredients.count_documents({}),
        },
    }


if __name__ == "__main__":
    from .db import get_db

    print(import_csv_to_mongo(get_db()))


def package_cost(required_qty: float, required_unit: str, ingredient: dict[str, Any]) -> int:
    if not ingredient.get("conHang"):
        return 0

    package = ingredient.get("quyCachDongGoi") or {}
    package_qty = float(package.get("soLuong") or 0)
    package_unit = package.get("donVi")
    price = int(ingredient.get("giaVnd") or 0)

    if package_qty <= 0 or price <= 0:
        return 0
    if package_unit != required_unit:
        return price
    return math.ceil(float(required_qty) / package_qty) * price
