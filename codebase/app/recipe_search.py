from __future__ import annotations

import re
from typing import Any

from pymongo.database import Database

from .csv_importer import normalize_text, package_cost


def _token_filter(field: str, query: str) -> dict[str, Any]:
    tokens = normalize_text(query).split()
    if not tokens:
        return {}
    return {"$and": [{field: {"$regex": re.escape(token)}} for token in tokens]}


def _recipe_response(db: Database, recipe: dict[str, Any], match_source: str) -> dict[str, Any]:
    links = list(
        db.recipe_ingredients.find({"maMonAn": recipe["maMonAn"]}).sort("thuTu", 1)
    )
    ingredient_ids = [link["maNguyenLieu"] for link in links]
    ingredients = {
        item["maNguyenLieu"]: item
        for item in db.ingredients.find({"maNguyenLieu": {"$in": ingredient_ids}})
    }

    ingredient_items = []
    total_cost = 0
    unavailable = []

    for link in links:
        ingredient = ingredients.get(link["maNguyenLieu"])
        cost = package_cost(
            link["soLuongChoKhauPhanCoBan"],
            link["donViSoLuong"],
            ingredient or {},
        )
        total_cost += cost
        if ingredient and not ingredient.get("conHang"):
            unavailable.append(ingredient["tenNguyenLieu"])

        ingredient_items.append(
            {
                "maNguyenLieu": link["maNguyenLieu"],
                "tenNguyenLieu": link["tenNguyenLieu"],
                "soLuongChoKhauPhanCoBan": link["soLuongChoKhauPhanCoBan"],
                "donViSoLuong": link["donViSoLuong"],
                "batBuoc": link["batBuoc"],
                "vaiTro": link["vaiTro"],
                "danhMuc": ingredient.get("danhMuc") if ingredient else None,
                "giaVnd": ingredient.get("giaVnd") if ingredient else None,
                "quyCachDongGoi": ingredient.get("quyCachDongGoi") if ingredient else None,
                "conHang": ingredient.get("conHang") if ingredient else None,
                "vietgapHoacSach": ingredient.get("vietgapHoacSach") if ingredient else None,
                "nguyenLieuThayThe": ingredient.get("nguyenLieuThayThe") if ingredient else None,
                "chiPhiUocTinhVnd": cost,
            }
        )

    return {
        "maMonAn": recipe["maMonAn"],
        "tenMonAn": recipe["tenMonAn"],
        "loaiBua": recipe["loaiBua"],
        "doKho": recipe["doKho"],
        "soKhauPhanCoBan": recipe["soKhauPhanCoBan"],
        "thoiGianPhut": recipe["thoiGianPhut"],
        "tags": recipe["tags"],
        "matchSource": match_source,
        "tongChiPhiUocTinhVnd": total_cost,
        "nguyenLieuHetHang": unavailable,
        "nguyenLieu": ingredient_items,
    }


def search_recipes(db: Database, query: str, limit: int = 20) -> list[dict[str, Any]]:
    recipe_filter = _token_filter("searchText", query)
    direct_recipes = list(db.recipes.find(recipe_filter).limit(limit))

    ingredient_filter = _token_filter("searchText", query)
    ingredient_ids = [item["maNguyenLieu"] for item in db.ingredients.find(ingredient_filter)]
    mapping_recipe_ids = [
        item["maMonAn"]
        for item in db.recipe_ingredients.find(
            {
                "$or": [
                    _token_filter("searchText", query),
                    {"maNguyenLieu": {"$in": ingredient_ids}},
                ]
            },
            {"maMonAn": 1},
        )
    ]

    recipes_by_id: dict[str, tuple[dict[str, Any], str]] = {}
    for recipe in direct_recipes:
        recipes_by_id[recipe["maMonAn"]] = (recipe, "mon_an")

    remaining_slots = max(limit - len(recipes_by_id), 0)
    if remaining_slots and mapping_recipe_ids:
        for recipe in db.recipes.find({"maMonAn": {"$in": mapping_recipe_ids}}).limit(remaining_slots):
            recipes_by_id.setdefault(recipe["maMonAn"], (recipe, "nguyen_lieu"))

    return [
        _recipe_response(db, recipe, match_source)
        for recipe, match_source in recipes_by_id.values()
    ][:limit]


def get_recipe_by_id(db: Database, recipe_id: str) -> dict[str, Any] | None:
    recipe = db.recipes.find_one({"maMonAn": recipe_id})
    if not recipe:
        return None
    return _recipe_response(db, recipe, "mon_an")
