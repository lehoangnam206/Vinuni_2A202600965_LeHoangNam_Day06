from __future__ import annotations

import re
from typing import Any

from pymongo.database import Database

from .csv_importer import normalize_text


def _token_filter(field: str, query: str) -> dict[str, Any]:
    tokens = normalize_text(query).split()
    if not tokens:
        return {}
    return {"$and": [{field: {"$regex": re.escape(token)}} for token in tokens]}


def _ingredient_response(ingredient: dict[str, Any]) -> dict[str, Any]:
    return {
        "maNguyenLieu": ingredient["maNguyenLieu"],
        "tenNguyenLieu": ingredient["tenNguyenLieu"],
        "danhMuc": ingredient["danhMuc"],
        "quyCachDongGoi": ingredient["quyCachDongGoi"],
        "giaVnd": ingredient["giaVnd"],
        "conHang": ingredient["conHang"],
        "vietgapHoacSach": ingredient["vietgapHoacSach"],
        "nguyenLieuThayThe": ingredient["nguyenLieuThayThe"],
        "ghiChu": ingredient["ghiChu"],
    }


def search_ingredients(db: Database, query: str, limit: int = 20) -> list[dict[str, Any]]:
    name_filter = _token_filter("tenNguyenLieuSearch", query)
    results = list(db.ingredients.find(name_filter).sort("tenNguyenLieu", 1).limit(limit))

    if not results:
        fallback_filter = _token_filter("searchText", query)
        results = list(db.ingredients.find(fallback_filter).sort("tenNguyenLieu", 1).limit(limit))

    return [_ingredient_response(ingredient) for ingredient in results]
