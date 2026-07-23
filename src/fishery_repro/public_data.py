from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

import pandas as pd

from .config import ROOT


WORLD_BANK_INDICATORS = {
    "ER.FSH.PROD.MT": "Total fisheries production",
    "ER.FSH.AQUA.MT": "Aquaculture production",
    "ER.FSH.CAPT.MT": "Capture fisheries production",
}

MOA_COMMUNIQUES = {
    2015: "https://yyj.moa.gov.cn/gzdt/201904/t20190418_6195519.htm",
    2016: "https://yyj.moa.gov.cn/gzdt/201904/t20190418_6195820.htm",
    2019: "https://cnafun.moa.gov.cn/kx/gn/202006/t20200619_6346974.html",
    2020: "https://yyj.moa.gov.cn/gzdt/202107/t20210728_6372958.htm",
    2021: "https://yyj.moa.gov.cn/gzdt/202207/t20220721_6405222.htm",
    2022: "https://yyj.moa.gov.cn/yqxx/202306/t20230628_6431131.htm",
    2023: "https://yyj.moa.gov.cn/gzdt/202407/t20240705_6458486.htm",
    2024: "https://yyj.moa.gov.cn/gzdt/202507/t20250707_6475475.htm",
}

NBS_INDICATOR_URL = "https://data.stats.gov.cn/easyquery.htm?cn=E0103&zb=A0407"
WORLD_BANK_LICENSE_URL = "https://datacatalog.worldbank.org/public-licenses"
MOA_2024_COMMUNIQUE_URL = MOA_COMMUNIQUES[2024]
MOA_ENVIRONMENT_2024_URL = "https://cjyzbgs.moa.gov.cn/gzdt/202509/t20250918_6477465.htm"
NBS_2025_COMMUNIQUE_URL = "https://www.stats.gov.cn/sj/zxfb/202602/t20260228_1962662.html"
ZHEJIANG_2025_COMMUNIQUE_URL = (
    "https://zjzd.stats.gov.cn/zwgk/zfxxgkml/tjxx/tjgb/"
    "art/2026/art_48c3c7315981425f9c25b53eab4d65d0.html"
)
PROCESSED_PUBLIC_LABEL = "经过处理的数据（公开来源）"


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        cleaned = " ".join(data.split())
        if cleaned:
            self.parts.append(cleaned)


@lru_cache(maxsize=None)
def _fetch(url: str) -> tuple[bytes, str | None]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "fishery-ia-nsga3-reproduction/0.2 (+https://github.com/niqundaye/Frontiers-in-Marine-Science)",
            "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read(), response.headers.get_content_charset()


def _html_text(content: bytes, charset: str | None) -> str:
    decoded = content.decode(charset or "utf-8", errors="replace")
    parser = _TextExtractor()
    parser.feed(decoded)
    return " ".join(parser.parts)


def _match(text: str, patterns: Iterable[str]) -> float | None:
    for pattern in patterns:
        found = re.search(pattern, text)
        if found:
            return float(found.group(1))
    return None


def _required_match(text: str, pattern: str, label: str) -> re.Match[str]:
    found = re.search(pattern, text, flags=re.DOTALL)
    if not found:
        raise ValueError(f"Required official statistic was not found: {label}")
    return found


def _signed_change(match: re.Match[str]) -> float | None:
    groups = match.groupdict()
    if not groups.get("yoy"):
        return None
    value = float(groups["yoy"])
    return -value if groups.get("direction") == "下降" else value


def _source_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def fetch_world_bank_fao(start_year: int = 2014, end_year: int = 2023) -> pd.DataFrame:
    retrieved_on = datetime.now(timezone.utc).date().isoformat()
    rows: list[dict[str, object]] = []
    for indicator_code, fallback_name in WORLD_BANK_INDICATORS.items():
        url = (
            f"https://api.worldbank.org/v2/country/CHN/indicator/{indicator_code}"
            f"?format=json&date={start_year}:{end_year}&per_page=100"
        )
        content, _ = _fetch(url)
        payload = json.loads(content.decode("utf-8"))
        metadata, records = payload
        for record in records:
            rows.append(
                {
                    "country_code": record["countryiso3code"],
                    "country": record["country"]["value"],
                    "year": int(record["date"]),
                    "indicator_code": indicator_code,
                    "indicator": record["indicator"]["value"] or fallback_name,
                    "value": record["value"],
                    "unit": "metric tonnes",
                    "source_organization": "FAO via World Bank World Development Indicators",
                    "source_url": url,
                    "source_last_updated": metadata.get("lastupdated"),
                    "retrieved_on": retrieved_on,
                    "license": "CC BY 4.0",
                    "license_url": WORLD_BANK_LICENSE_URL,
                }
            )
    return pd.DataFrame(rows).sort_values(["year", "indicator_code"]).reset_index(drop=True)


MOA_PATTERNS: dict[str, tuple[tuple[str, ...], float, str]] = {
    "total_economic_output": (
        (r"全社会渔业经济总产值(?:达到|为)?\s*([0-9.]+)\s*亿\s*元",),
        1.0,
        "100 million RMB",
    ),
    "fisher_per_capita_net_income": ((r"全国渔民人均纯收入(?:达到|为)?\s*([0-9.]+)\s*元",), 1.0, "RMB/year"),
    "total_aquatic_products": ((r"全国水产品总产量(?:达到|为)?\s*([0-9.]+)\s*万吨",), 10000.0, "tonnes"),
    "aquaculture_production": ((r"其中[，,:：\s]*养殖产量\s*([0-9.]+)\s*万吨",), 10000.0, "tonnes"),
    "capture_production": ((r"捕捞产量\s*([0-9.]+)\s*万吨",), 10000.0, "tonnes"),
    "distant_water_capture": ((r"远洋渔业产量\s*([0-9.]+)\s*万吨",), 10000.0, "tonnes"),
    "processing_enterprises": ((r"水产加工企业\s*([0-9.]+)\s*个",), 1.0, "count"),
    "cold_storage_units": ((r"水产冷库\s*([0-9.]+)\s*座",), 1.0, "count"),
    "motorized_fleet_power": (
        (r"机动渔船[^。]{0,120}?总功率\s*([0-9.]+)\s*万千瓦",),
        10000.0,
        "kW",
    ),
    "aquatic_exports_value": (
        (
            r"出口量[^。]{0,80}?出口额\s*([0-9.]+)\s*亿美元",
            r"出口额\s*([0-9.]+)\s*亿美元",
        ),
        100.0,
        "million USD",
    ),
}


def fetch_moa_communiques() -> pd.DataFrame:
    retrieved_on = datetime.now(timezone.utc).date().isoformat()
    rows: list[dict[str, object]] = []
    for year, url in MOA_COMMUNIQUES.items():
        content, charset = _fetch(url)
        text = _html_text(content, charset)
        for indicator, (patterns, multiplier, unit) in MOA_PATTERNS.items():
            raw_value = _match(text, patterns)
            rows.append(
                {
                    "year": year,
                    "indicator": indicator,
                    "value": None if raw_value is None else raw_value * multiplier,
                    "unit": unit,
                    "source_organization": "Ministry of Agriculture and Rural Affairs of the PRC",
                    "source_url": url,
                    "retrieved_on": retrieved_on,
                    "extraction_status": "parsed" if raw_value is not None else "not_found",
                    "extraction_method": "deterministic regex over official HTML text",
                }
            )
    return pd.DataFrame(rows).sort_values(["year", "indicator"]).reset_index(drop=True)


def fetch_moa_2024_detailed() -> pd.DataFrame:
    """Parse the detailed 2024 national fishery communique into auditable long form.

    Every row retains the value and unit exactly as reported, the explicit
    normalization multiplier, the normalized value, the official URL, retrieval
    date and SHA-256 of the downloaded HTML. Missing required fields fail loudly.
    """

    retrieved_on = datetime.now(timezone.utc).date().isoformat()
    content, charset = _fetch(MOA_2024_COMMUNIQUE_URL)
    text = _html_text(content, charset)
    digest = _source_sha256(content)
    rows: list[dict[str, object]] = []

    def add(
        *,
        section: str,
        indicator: str,
        indicator_zh: str,
        category: str,
        pattern: str,
        reported_unit: str,
        multiplier: float,
        unit: str,
    ) -> None:
        match = _required_match(text, pattern, indicator)
        reported_value = float(match.group("value"))
        rows.append(
            {
                "year": 2024,
                "section": section,
                "indicator": indicator,
                "indicator_zh": indicator_zh,
                "category": category,
                "reported_value": reported_value,
                "reported_unit": reported_unit,
                "normalization_multiplier": multiplier,
                "value": reported_value * multiplier,
                "unit": unit,
                "yoy_pct": _signed_change(match),
                "share_pct": float(match.group("share")) if match.groupdict().get("share") else None,
                "source_organization": "Ministry of Agriculture and Rural Affairs of the PRC",
                "source_url": MOA_2024_COMMUNIQUE_URL,
                "source_sha256": digest,
                "retrieved_on": retrieved_on,
                "data_label": PROCESSED_PUBLIC_LABEL,
                "extraction_method": "deterministic regex over official HTML text",
            }
        )

    scalar_specs = [
        (
            "economy",
            "total_fishery_economic_output",
            "全社会渔业经济总产值",
            "total",
            r"全社会渔业经济总产值\s*(?P<value>[0-9.]+)\s*亿\s*元",
            "亿元",
            1.0,
            "100 million RMB",
        ),
        (
            "economy",
            "fishery_output",
            "渔业产值",
            "total",
            r"其中渔业产\s*值\s*(?P<value>[0-9.]+)\s*亿\s*元",
            "亿元",
            1.0,
            "100 million RMB",
        ),
        (
            "economy",
            "fishery_industry_construction_output",
            "渔业工业和建筑业产值",
            "total",
            r"渔业工业和建筑业产值\s*(?P<value>[0-9.]+)\s*亿元",
            "亿元",
            1.0,
            "100 million RMB",
        ),
        (
            "economy",
            "fishery_circulation_services_output",
            "渔业流通和服务业产值",
            "total",
            r"渔业流通和服务业产\s*值\s*(?P<value>[0-9.]+)\s*亿\s*元",
            "亿元",
            1.0,
            "100 million RMB",
        ),
        (
            "economy",
            "recreational_fishing_output",
            "休闲渔业产值",
            "total",
            r"休闲渔业产值\s*(?P<value>[0-9.]+)\s*亿元，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%",
            "亿元",
            1.0,
            "100 million RMB",
        ),
        (
            "economy",
            "marine_capture_output",
            "海洋捕捞产值",
            "marine",
            r"海洋捕捞产值\s*(?P<value>[0-9.]+)\s*亿元",
            "亿元",
            1.0,
            "100 million RMB",
        ),
        (
            "economy",
            "marine_aquaculture_output",
            "海水养殖产值",
            "marine",
            r"海水养殖产值\s*(?P<value>[0-9.]+)\s*亿元",
            "亿元",
            1.0,
            "100 million RMB",
        ),
        (
            "economy",
            "freshwater_capture_output",
            "淡水捕捞产值",
            "freshwater",
            r"淡水捕捞产值\s*(?P<value>[0-9.]+)\s*亿元",
            "亿元",
            1.0,
            "100 million RMB",
        ),
        (
            "economy",
            "freshwater_aquaculture_output",
            "淡水养殖产值",
            "freshwater",
            r"淡水养殖产值\s*(?P<value>[0-9.]+)\s*亿元",
            "亿元",
            1.0,
            "100 million RMB",
        ),
        (
            "economy",
            "aquatic_seed_output",
            "水产苗种产值",
            "total",
            r"水产苗种产值\s*(?P<value>[0-9.]+)\s*亿元",
            "亿元",
            1.0,
            "100 million RMB",
        ),
        (
            "income",
            "fisher_per_capita_net_income",
            "渔民人均纯收入",
            "total",
            r"全国渔民人均纯收入\s*(?P<value>[0-9.]+)\s*元[^。]*同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%",
            "元",
            1.0,
            "RMB/person/year",
        ),
        (
            "production",
            "total_aquatic_products",
            "水产品总产量",
            "total",
            r"全国水产品总产量\s*(?P<value>[0-9.]+)\s*万吨，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%",
            "万吨",
            10000.0,
            "tonnes",
        ),
        (
            "production",
            "aquaculture_production",
            "养殖产量",
            "total",
            r"养殖产量\s*(?P<value>[0-9.]+)\s*万吨，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%",
            "万吨",
            10000.0,
            "tonnes",
        ),
        (
            "production",
            "capture_production",
            "捕捞产量",
            "total",
            r"捕捞产量\s*(?P<value>[0-9.]+)\s*万吨，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%",
            "万吨",
            10000.0,
            "tonnes",
        ),
        (
            "production",
            "marine_products",
            "海水产品产量",
            "marine",
            r"海水产品产量\s*(?P<value>[0-9.]+)\s*万吨，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%",
            "万吨",
            10000.0,
            "tonnes",
        ),
        (
            "production",
            "freshwater_products",
            "淡水产品产量",
            "freshwater",
            r"淡水产品产量\s*(?P<value>[0-9.]+)\s*万吨，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%",
            "万吨",
            10000.0,
            "tonnes",
        ),
        (
            "production",
            "distant_water_capture",
            "远洋渔业产量",
            "distant_water",
            r"全国远洋渔业产量\s*(?P<value>[0-9.]+)\s*万吨，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%",
            "万吨",
            10000.0,
            "tonnes",
        ),
        (
            "production",
            "aquatic_products_per_capita",
            "水产品人均占有量",
            "total",
            r"全国水产品人均占有量\s*(?P<value>[0-9.]+)\s*千克[^。]*同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%",
            "千克",
            1.0,
            "kg/person/year",
        ),
        (
            "aquaculture_area",
            "aquaculture_area",
            "水产养殖面积",
            "total",
            r"全国水产养殖面积\s*(?P<value>[0-9.]+)\s*千公顷，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%",
            "千公顷",
            1000.0,
            "hectares",
        ),
        (
            "aquaculture_area",
            "aquaculture_area",
            "水产养殖面积",
            "marine",
            r"海水养殖面积\s*(?P<value>[0-9.]+)\s*千公顷，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%",
            "千公顷",
            1000.0,
            "hectares",
        ),
        (
            "aquaculture_area",
            "aquaculture_area",
            "水产养殖面积",
            "freshwater",
            r"淡水养殖面积\s*(?P<value>[0-9.]+)\s*千公顷，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%",
            "千公顷",
            1000.0,
            "hectares",
        ),
    ]
    for section, indicator, indicator_zh, category, pattern, reported_unit, multiplier, unit in scalar_specs:
        add(
            section=section,
            indicator=indicator,
            indicator_zh=indicator_zh,
            category=category,
            pattern=pattern,
            reported_unit=reported_unit,
            multiplier=multiplier,
            unit=unit,
        )

    aqua_block = text[text.index("表1 2024年全国水产养殖产量") : text.index("表2 2024年国内捕捞产量")]
    for label, code in [("鱼类", "fish"), ("甲壳类", "crustaceans"), ("贝类", "shellfish"), ("藻类", "algae"), ("其他 类", "other")]:
        match = _required_match(
            aqua_block,
            rf"{label}\s+(?P<total>[0-9.]+)\s+(?P<marine>[0-9.]+)\s+(?P<marine_yoy>-?[0-9.]+)"
            rf"\s+(?P<freshwater>[0-9.]+)\s+(?P<freshwater_yoy>-?[0-9.]+)",
            f"aquaculture table: {code}",
        )
        for category, value_group, yoy_group in [
            ("total", "total", None),
            ("marine", "marine", "marine_yoy"),
            ("freshwater", "freshwater", "freshwater_yoy"),
        ]:
            reported_value = float(match.group(value_group))
            rows.append(
                {
                    "year": 2024,
                    "section": "aquaculture_production_by_species",
                    "indicator": f"aquaculture_{code}",
                    "indicator_zh": f"养殖{label.replace(' ', '')}",
                    "category": category,
                    "reported_value": reported_value,
                    "reported_unit": "万吨",
                    "normalization_multiplier": 10000.0,
                    "value": reported_value * 10000.0,
                    "unit": "tonnes",
                    "yoy_pct": None if yoy_group is None else float(match.group(yoy_group)),
                    "share_pct": None,
                    "source_organization": "Ministry of Agriculture and Rural Affairs of the PRC",
                    "source_url": MOA_2024_COMMUNIQUE_URL,
                    "source_sha256": digest,
                    "retrieved_on": retrieved_on,
                    "data_label": PROCESSED_PUBLIC_LABEL,
                    "extraction_method": "deterministic table-row regex over official HTML text",
                }
            )

    capture_block = text[text.index("表2 2024年国内捕捞产量") : text.index("2024年，全国远洋渔业产量")]
    domestic_total = _required_match(
        capture_block,
        r"全国总计\s+(?P<total>[0-9.]+)\s+(?P<marine>[0-9.]+)\s+(?P<marine_yoy>-?[0-9.]+)"
        r"\s+(?P<freshwater>[0-9.]+)\s+(?P<freshwater_yoy>-?[0-9.]+)",
        "domestic capture total",
    )
    for category, value_group, yoy_group in [
        ("total", "total", None),
        ("marine", "marine", "marine_yoy"),
        ("freshwater", "freshwater", "freshwater_yoy"),
    ]:
        reported_value = float(domestic_total.group(value_group))
        rows.append(
            {
                "year": 2024,
                "section": "domestic_capture",
                "indicator": "domestic_capture_production",
                "indicator_zh": "国内捕捞产量",
                "category": category,
                "reported_value": reported_value,
                "reported_unit": "万吨",
                "normalization_multiplier": 10000.0,
                "value": reported_value * 10000.0,
                "unit": "tonnes",
                "yoy_pct": None if yoy_group is None else float(domestic_total.group(yoy_group)),
                "share_pct": None,
                "source_organization": "Ministry of Agriculture and Rural Affairs of the PRC",
                "source_url": MOA_2024_COMMUNIQUE_URL,
                "source_sha256": digest,
                "retrieved_on": retrieved_on,
                "data_label": PROCESSED_PUBLIC_LABEL,
                "extraction_method": "deterministic table-row regex over official HTML text",
            }
        )

    five_column_capture = [
        ("鱼类", "fish"),
        ("甲壳类", "crustaceans"),
        ("贝类", "shellfish"),
        ("其他 类", "other"),
    ]
    for label, code in five_column_capture:
        match = _required_match(
            capture_block,
            rf"{label}\s+(?P<total>[0-9.]+)\s+(?P<marine>[0-9.]+)\s+(?P<marine_yoy>-?[0-9.]+)"
            rf"\s+(?P<freshwater>[0-9.]+)\s+(?P<freshwater_yoy>-?[0-9.]+)",
            f"domestic capture table: {code}",
        )
        for category, value_group, yoy_group in [
            ("total", "total", None),
            ("marine", "marine", "marine_yoy"),
            ("freshwater", "freshwater", "freshwater_yoy"),
        ]:
            reported_value = float(match.group(value_group))
            rows.append(
                {
                    "year": 2024,
                    "section": "domestic_capture_by_species",
                    "indicator": f"domestic_capture_{code}",
                    "indicator_zh": f"国内捕捞{label.replace(' ', '')}",
                    "category": category,
                    "reported_value": reported_value,
                    "reported_unit": "万吨",
                    "normalization_multiplier": 10000.0,
                    "value": reported_value * 10000.0,
                    "unit": "tonnes",
                    "yoy_pct": None if yoy_group is None else float(match.group(yoy_group)),
                    "share_pct": None,
                    "source_organization": "Ministry of Agriculture and Rural Affairs of the PRC",
                    "source_url": MOA_2024_COMMUNIQUE_URL,
                    "source_sha256": digest,
                    "retrieved_on": retrieved_on,
                    "data_label": PROCESSED_PUBLIC_LABEL,
                    "extraction_method": "deterministic table-row regex over official HTML text",
                }
            )

    for label, code in [("藻类", "algae"), ("头足类", "cephalopods")]:
        match = _required_match(
            capture_block,
            rf"{label}\s+(?P<total>[0-9.]+)\s+(?P<marine>[0-9.]+)\s+(?P<marine_yoy>-?[0-9.]+)",
            f"domestic capture table: {code}",
        )
        for category, value_group, yoy_group in [
            ("total", "total", None),
            ("marine", "marine", "marine_yoy"),
        ]:
            reported_value = float(match.group(value_group))
            rows.append(
                {
                    "year": 2024,
                    "section": "domestic_capture_by_species",
                    "indicator": f"domestic_capture_{code}",
                    "indicator_zh": f"国内捕捞{label}",
                    "category": category,
                    "reported_value": reported_value,
                    "reported_unit": "万吨",
                    "normalization_multiplier": 10000.0,
                    "value": reported_value * 10000.0,
                    "unit": "tonnes",
                    "yoy_pct": None if yoy_group is None else float(match.group(yoy_group)),
                    "share_pct": None,
                    "source_organization": "Ministry of Agriculture and Rural Affairs of the PRC",
                    "source_url": MOA_2024_COMMUNIQUE_URL,
                    "source_sha256": digest,
                    "retrieved_on": retrieved_on,
                    "data_label": PROCESSED_PUBLIC_LABEL,
                    "extraction_method": "deterministic table-row regex over official HTML text",
                }
            )

    marine_area_block = text[text.index("表3 2024年全国海水养殖面积") : text.index("表4 2024年全国淡水养殖面积")]
    for label, code in [("鱼类", "fish"), ("甲壳类", "crustaceans"), ("贝类", "shellfish"), ("藻类", "algae"), ("其他类", "other")]:
        match = _required_match(
            marine_area_block,
            rf"{label}\s+(?P<value>[0-9.]+)\s+(?P<yoy>-?[0-9.]+)\s+(?P<share>[0-9.]+)",
            f"marine aquaculture area table: {code}",
        )
        reported_value = float(match.group("value"))
        rows.append(
            {
                "year": 2024,
                "section": "aquaculture_area_by_type",
                "indicator": f"marine_aquaculture_area_{code}",
                "indicator_zh": f"海水{label}养殖面积",
                "category": "marine",
                "reported_value": reported_value,
                "reported_unit": "千公顷",
                "normalization_multiplier": 1000.0,
                "value": reported_value * 1000.0,
                "unit": "hectares",
                "yoy_pct": float(match.group("yoy")),
                "share_pct": float(match.group("share")),
                "source_organization": "Ministry of Agriculture and Rural Affairs of the PRC",
                "source_url": MOA_2024_COMMUNIQUE_URL,
                "source_sha256": digest,
                "retrieved_on": retrieved_on,
                "data_label": PROCESSED_PUBLIC_LABEL,
                "extraction_method": "deterministic table-row regex over official HTML text",
            }
        )

    freshwater_area_block = text[text.index("表4 2024年全国淡水养殖面积") : text.index("五、渔船年末拥有量")]
    for label, code in [("池塘", "ponds"), ("湖泊", "lakes"), ("水库", "reservoirs"), ("河沟", "rivers_ditches"), ("其他", "other")]:
        match = _required_match(
            freshwater_area_block,
            rf"{label}\s+(?P<value>[0-9.]+)\s+(?P<yoy>-?[0-9.]+)\s+(?P<share>[0-9.]+)",
            f"freshwater aquaculture area table: {code}",
        )
        reported_value = float(match.group("value"))
        rows.append(
            {
                "year": 2024,
                "section": "aquaculture_area_by_type",
                "indicator": f"freshwater_aquaculture_area_{code}",
                "indicator_zh": f"淡水{label}养殖面积",
                "category": "freshwater",
                "reported_value": reported_value,
                "reported_unit": "千公顷",
                "normalization_multiplier": 1000.0,
                "value": reported_value * 1000.0,
                "unit": "hectares",
                "yoy_pct": float(match.group("yoy")),
                "share_pct": float(match.group("share")),
                "source_organization": "Ministry of Agriculture and Rural Affairs of the PRC",
                "source_url": MOA_2024_COMMUNIQUE_URL,
                "source_sha256": digest,
                "retrieved_on": retrieved_on,
                "data_label": PROCESSED_PUBLIC_LABEL,
                "extraction_method": "deterministic table-row regex over official HTML text",
            }
        )

    operational_specs = [
        ("fleet", "vessel_count", "渔船数量", "total", r"年末渔船总数(?P<value>[0-9.]+)万艘", "万艘", 10000.0, "count"),
        ("fleet", "vessel_tonnage", "渔船总吨位", "total", r"年末渔船总数[0-9.]+万艘、总吨位(?P<value>[0-9.]+)万吨", "万吨", 10000.0, "tonnes"),
        ("fleet", "vessel_count", "渔船数量", "motorized", r"其中，机动渔船(?P<value>[0-9.]+)万艘", "万艘", 10000.0, "count"),
        ("fleet", "vessel_tonnage", "渔船总吨位", "motorized", r"机动渔船[0-9.]+万艘、总吨位(?P<value>[0-9.]+)万吨", "万吨", 10000.0, "tonnes"),
        ("fleet", "vessel_power", "渔船总功率", "motorized", r"机动渔船[^；]+总功率(?P<value>[0-9.]+)万千瓦", "万千瓦", 10000.0, "kW"),
        ("fleet", "vessel_count", "渔船数量", "non_motorized", r"非机动渔船(?P<value>[0-9.]+)万艘", "万艘", 10000.0, "count"),
        ("fleet", "vessel_tonnage", "渔船总吨位", "non_motorized", r"非机动渔船[0-9.]+万艘、总吨位(?P<value>[0-9.]+)万吨", "万吨", 10000.0, "tonnes"),
        ("fleet", "vessel_count", "渔船数量", "production", r"生产渔船(?P<value>[0-9.]+)万艘", "万艘", 10000.0, "count"),
        ("fleet", "vessel_tonnage", "渔船总吨位", "production", r"生产渔船[0-9.]+万艘、总吨位(?P<value>[0-9.]+)万吨", "万吨", 10000.0, "tonnes"),
        ("fleet", "vessel_power", "渔船总功率", "production", r"生产渔船[^；]+总功率(?P<value>[0-9.]+)万千瓦", "万千瓦", 10000.0, "kW"),
        ("fleet", "vessel_count", "渔船数量", "auxiliary", r"辅助渔船(?P<value>[0-9.]+)万艘", "万艘", 10000.0, "count"),
        ("fleet", "vessel_tonnage", "渔船总吨位", "auxiliary", r"辅助渔船[0-9.]+万艘、总吨位(?P<value>[0-9.]+)万吨", "万吨", 10000.0, "tonnes"),
        ("fleet", "vessel_power", "渔船总功率", "auxiliary", r"辅助渔船[^。]+总功率(?P<value>[0-9.]+)万千瓦", "万千瓦", 10000.0, "kW"),
        ("population", "fishery_population", "渔业人口", "total", r"渔业人口(?P<value>[0-9.]+)万人[^。]*同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%", "万人", 10000.0, "persons"),
        ("population", "traditional_fishers", "传统渔民", "total", r"传统渔民为(?P<value>[0-9.]+)万人[^。]*同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%", "万人", 10000.0, "persons"),
        ("population", "fishery_workforce", "渔业从业人员", "total", r"渔业从业人员(?P<value>[0-9.]+)万人[^。]*同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%", "万人", 10000.0, "persons"),
        ("processing_trade", "processing_enterprises", "水产加工企业", "total", r"水产加工企业(?P<value>[0-9.]+)个", "个", 1.0, "count"),
        ("processing_trade", "cold_storage_units", "水产冷库", "total", r"水产冷库(?P<value>[0-9.]+)座", "座", 1.0, "count"),
        ("processing_trade", "processed_products", "水产加工品总量", "total", r"水产加工品总量(?P<value>[0-9.]+)万吨，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%", "万吨", 10000.0, "tonnes"),
        ("processing_trade", "processed_products", "水产加工品总量", "marine", r"海水加工产品(?P<value>[0-9.]+)万吨，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%", "万吨", 10000.0, "tonnes"),
        ("processing_trade", "processed_products", "水产加工品总量", "freshwater", r"淡水加工产品(?P<value>[0-9.]+)万吨，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%", "万吨", 10000.0, "tonnes"),
        ("processing_trade", "products_used_for_processing", "用于加工的水产品总量", "total", r"用于加工的水产品总量(?P<value>[0-9.]+)万吨，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%", "万吨", 10000.0, "tonnes"),
        ("processing_trade", "products_used_for_processing", "用于加工的水产品总量", "marine", r"用于加工的海水产品(?P<value>[0-9.]+)万吨，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%", "万吨", 10000.0, "tonnes"),
        ("processing_trade", "products_used_for_processing", "用于加工的水产品总量", "freshwater", r"用于加工的淡水产品(?P<value>[0-9.]+)万吨，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%", "万吨", 10000.0, "tonnes"),
        ("processing_trade", "trade_volume", "水产品进出口量", "total", r"水产品进出口总量(?P<value>[0-9.]+)万吨，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%", "万吨", 10000.0, "tonnes"),
        ("processing_trade", "trade_value", "水产品进出口额", "total", r"进出口总额(?P<value>[0-9.]+)亿美元，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%", "亿美元", 100.0, "million USD"),
        ("processing_trade", "trade_volume", "水产品出口量", "export", r"出口量(?P<value>[0-9.]+)万吨，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%", "万吨", 10000.0, "tonnes"),
        ("processing_trade", "trade_value", "水产品出口额", "export", r"出口额(?P<value>[0-9.]+)亿美元，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%", "亿美元", 100.0, "million USD"),
        ("processing_trade", "trade_volume", "水产品进口量", "import", r"进口量(?P<value>[0-9.]+)万吨，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%", "万吨", 10000.0, "tonnes"),
        ("processing_trade", "trade_value", "水产品进口额", "import", r"进口额(?P<value>[0-9.]+)亿美元，同比(?P<direction>增长|下降)(?P<yoy>[0-9.]+)%", "亿美元", 100.0, "million USD"),
        ("processing_trade", "trade_deficit", "水产品贸易逆差", "total", r"贸易逆差(?P<value>[0-9.]+)亿美元", "亿美元", 100.0, "million USD"),
        ("disaster", "production_loss", "渔业灾情水产品产量损失", "total", r"水产品产量损失(?P<value>[0-9.]+)万吨", "万吨", 10000.0, "tonnes"),
        ("disaster", "affected_aquaculture_area", "受灾养殖面积", "total", r"受灾养殖面积(?P<value>[0-9.]+)千公顷", "千公顷", 1000.0, "hectares"),
        ("disaster", "direct_economic_loss", "直接经济损失", "total", r"直接经济损失(?P<value>[0-9.]+)亿元", "亿元", 1.0, "100 million RMB"),
    ]
    for section, indicator, indicator_zh, category, pattern, reported_unit, multiplier, unit in operational_specs:
        add(
            section=section,
            indicator=indicator,
            indicator_zh=indicator_zh,
            category=category,
            pattern=pattern,
            reported_unit=reported_unit,
            multiplier=multiplier,
            unit=unit,
        )

    return pd.DataFrame(rows).sort_values(["section", "indicator", "category"]).reset_index(drop=True)


def fetch_moa_environment_2024() -> pd.DataFrame:
    """Extract official 2024 fishery-environment monitoring indicators."""

    retrieved_on = datetime.now(timezone.utc).date().isoformat()
    content, charset = _fetch(MOA_ENVIRONMENT_2024_URL)
    text = _html_text(content, charset)
    digest = _source_sha256(content)
    rows: list[dict[str, object]] = []

    specs = [
        ("monitoring_stations", "监测站数量", r"所属(?P<value>[0-9.]+)个监测站", "个", 1.0, "count", 2024, "level"),
        ("important_fishery_waters", "重要渔业水域数量", r"对(?P<value>[0-9.]+)个、总面积", "个", 1.0, "count", 2024, "level"),
        ("monitored_water_area", "监测水域总面积", r"总面积(?P<value>[0-9.]+)万公顷", "万公顷", 10000.0, "hectares", 2024, "level"),
        ("monitoring_station_increase", "监测站增加数", r"增加了(?P<value>[0-9.]+)个监测站", "个", 1.0, "count", 2023, "increase"),
        ("important_water_increase", "重要渔业水域增加数", r"、(?P<value>[0-9.]+)个重要渔业水域", "个", 1.0, "count", 2023, "increase"),
        (
            "monitored_area_increase",
            "监测面积增加量",
            r"分别增加了[0-9.]+个监测站、[0-9.]+个重要渔业水域、面积(?P<value>[0-9.]+)万公顷",
            "万公顷",
            10000.0,
            "hectares",
            2023,
            "increase",
        ),
        ("marine_cod_exceedance_area_ratio", "海洋化学需氧量超标面积比例", r"化学需氧量指标的超标面积比例下降幅度为(?P<value>[0-9.]+)%", "%", 1.0, "percentage points reported as decline magnitude", 2023, "decrease"),
        ("inland_unionized_ammonia_exceedance_area_ratio", "内陆非离子氨超标面积比例", r"非离子氨、高锰酸盐指数指标的超标面积比例下降幅度分别为(?P<value>[0-9.]+)%", "%", 1.0, "percentage points reported as decline magnitude", 2023, "decrease"),
        ("inland_permanganate_exceedance_area_ratio", "内陆高锰酸盐指数超标面积比例", r"非离子氨、高锰酸盐指数指标的超标面积比例下降幅度分别为[0-9.]+%和(?P<value>[0-9.]+)%", "%", 1.0, "percentage points reported as decline magnitude", 2023, "decrease"),
        ("marine_inorganic_nitrogen_exceedance_area_ratio", "海洋无机氮超标面积比例", r"无机氮和活性磷酸盐，其指标的超标面积比例下降幅度分别为(?P<value>[0-9.]+)%", "%", 1.0, "percentage points reported as decline magnitude", 2020, "decrease"),
        ("marine_reactive_phosphate_exceedance_area_ratio", "海洋活性磷酸盐超标面积比例", r"无机氮和活性磷酸盐，其指标的超标面积比例下降幅度分别为[0-9.]+%和(?P<value>[0-9.]+)%", "%", 1.0, "percentage points reported as decline magnitude", 2020, "decrease"),
        ("river_total_phosphorus_exceedance_area_ratio", "江河总磷超标面积比例", r"总磷超标面积比例下降幅度为(?P<value>[0-9.]+)%", "%", 1.0, "percentage points reported as decline magnitude", 2020, "decrease"),
    ]
    for indicator, indicator_zh, pattern, reported_unit, multiplier, unit, comparison_year, direction in specs:
        match = _required_match(text, pattern, indicator)
        reported_value = float(match.group("value"))
        rows.append(
            {
                "year": 2024,
                "comparison_year": comparison_year,
                "indicator": indicator,
                "indicator_zh": indicator_zh,
                "reported_value": reported_value,
                "reported_unit": reported_unit,
                "normalization_multiplier": multiplier,
                "value": reported_value * multiplier,
                "unit": unit,
                "change_direction": direction,
                "source_organization": "Ministry of Agriculture and Rural Affairs / Ministry of Ecology and Environment",
                "source_url": MOA_ENVIRONMENT_2024_URL,
                "source_sha256": digest,
                "retrieved_on": retrieved_on,
                "data_label": PROCESSED_PUBLIC_LABEL,
                "extraction_method": "deterministic regex over official HTML summary",
            }
        )
    return pd.DataFrame(rows)


def fetch_latest_official_aquatic_products() -> pd.DataFrame:
    """Extract the latest official national and Zhejiang aquatic-product totals."""

    retrieved_on = datetime.now(timezone.utc).date().isoformat()
    sources = [
        {
            "geography_code": "CHN",
            "geography": "China",
            "publisher": "National Bureau of Statistics of China",
            "url": NBS_2025_COMMUNIQUE_URL,
            "category_basis": "production method",
            "pattern": (
                r"全年水产品总产量\s*(?P<total>[0-9.]+)\s*万吨，比上年增长\s*(?P<total_yoy>[0-9.]+)%\s*。其中，"
                r"养殖产量\s*(?P<aquaculture>[0-9.]+)\s*万吨，增长\s*(?P<aquaculture_yoy>[0-9.]+)%\s*；"
                r"捕捞产量\s*(?P<capture>[0-9.]+)\s*万吨，增长\s*(?P<capture_yoy>[0-9.]+)%"
            ),
            "indicators": [
                ("total_aquatic_products", "水产品总产量", "total", "total_yoy"),
                ("aquaculture_production", "养殖产量", "aquaculture", "aquaculture_yoy"),
                ("capture_production", "捕捞产量", "capture", "capture_yoy"),
            ],
        },
        {
            "geography_code": "CN-ZJ",
            "geography": "Zhejiang",
            "publisher": "Zhejiang Provincial Bureau of Statistics / NBS Zhejiang Survey Office",
            "url": ZHEJIANG_2025_COMMUNIQUE_URL,
            "category_basis": "water body",
            "pattern": (
                r"全年水产品产量\s*(?P<total>[0-9.]+)\s*万吨，增长\s*(?P<total_yoy>[0-9.]+)%"
                r"，其中，海水产品产量\s*(?P<marine>[0-9.]+)\s*万吨，增长\s*(?P<marine_yoy>[0-9.]+)%"
                r"；淡水产品产量\s*(?P<freshwater>[0-9.]+)\s*万吨，增长\s*(?P<freshwater_yoy>[0-9.]+)%"
            ),
            "indicators": [
                ("total_aquatic_products", "水产品总产量", "total", "total_yoy"),
                ("marine_products", "海水产品产量", "marine", "marine_yoy"),
                ("freshwater_products", "淡水产品产量", "freshwater", "freshwater_yoy"),
            ],
        },
    ]
    rows: list[dict[str, object]] = []
    for source in sources:
        content, charset = _fetch(str(source["url"]))
        text = _html_text(content, charset)
        digest = _source_sha256(content)
        match = _required_match(text, str(source["pattern"]), str(source["geography_code"]))
        for indicator, indicator_zh, value_group, yoy_group in source["indicators"]:
            reported_value = float(match.group(value_group))
            rows.append(
                {
                    "year": 2025,
                    "geography_code": source["geography_code"],
                    "geography": source["geography"],
                    "indicator": indicator,
                    "indicator_zh": indicator_zh,
                    "reported_value": reported_value,
                    "reported_unit": "万吨",
                    "normalization_multiplier": 10000.0,
                    "value": reported_value * 10000.0,
                    "unit": "tonnes",
                    "yoy_pct": float(match.group(yoy_group)),
                    "category_basis": source["category_basis"],
                    "source_organization": source["publisher"],
                    "source_url": source["url"],
                    "source_sha256": digest,
                    "retrieved_on": retrieved_on,
                    "data_label": PROCESSED_PUBLIC_LABEL,
                    "extraction_method": "deterministic regex over official statistical communique HTML",
                }
            )
    return pd.DataFrame(rows)


def source_catalog(retrieved_on: str | None = None) -> pd.DataFrame:
    date = retrieved_on or datetime.now(timezone.utc).date().isoformat()
    rows: list[dict[str, object]] = []
    for code in WORLD_BANK_INDICATORS:
        rows.append(
            {
                "source_id": f"world_bank_{code.lower().replace('.', '_')}",
                "publisher": "World Bank / FAO",
                "dataset": WORLD_BANK_INDICATORS[code],
                "coverage": "China, 2014-2023 snapshot",
                "url": f"https://api.worldbank.org/v2/country/CHN/indicator/{code}?format=json&date=2014:2023&per_page=100",
                "access": "Downloaded and normalized",
                "license_or_terms": "CC BY 4.0",
                "repository_file": "data/public/world_bank_fao_china_fisheries_2014_2023.csv",
                "retrieved_on": date,
                "notes": "National series; not a substitute for the missing 31-province coefficient matrix.",
            }
        )
    for year, url in MOA_COMMUNIQUES.items():
        rows.append(
            {
                "source_id": f"moa_communique_{year}",
                "publisher": "Ministry of Agriculture and Rural Affairs of the PRC",
                "dataset": f"{year} national fishery economic statistics communique",
                "coverage": f"China, {year}",
                "url": url,
                "access": "Key statistics extracted from official HTML",
                "license_or_terms": "Official website terms apply; numerical facts extracted with attribution",
                "repository_file": "data/public/moa_national_fishery_statistics.csv",
                "retrieved_on": date,
                "notes": "2017 is an attachment-only legacy DOC and 2018 was not available as an accessible official HTML page; neither is silently interpolated.",
            }
        )
    rows.extend(
        [
            {
                "source_id": "moa_2024_detailed",
                "publisher": "Ministry of Agriculture and Rural Affairs of the PRC",
                "dataset": "2024 national fishery economic statistics communique, detailed extraction",
                "coverage": "China, 2024; economy, production, species, area, fleet, population, processing, trade, disasters",
                "url": MOA_2024_COMMUNIQUE_URL,
                "access": "Detailed statistics extracted and normalized from official HTML",
                "license_or_terms": "Official website terms apply; numerical facts extracted with attribution",
                "repository_file": "data/public/moa_2024_detailed_fishery_statistics.csv",
                "retrieved_on": date,
                "notes": f"{PROCESSED_PUBLIC_LABEL}; reported values and units are retained beside normalized values.",
            },
            {
                "source_id": "moa_environment_2024",
                "publisher": "Ministry of Agriculture and Rural Affairs / Ministry of Ecology and Environment",
                "dataset": "China fishery ecological environment status communique 2024 summary",
                "coverage": "China, 2024; monitoring network and selected exceedance-area changes",
                "url": MOA_ENVIRONMENT_2024_URL,
                "access": "Statistics extracted and normalized from official HTML summary",
                "license_or_terms": "Official website terms apply; numerical facts extracted with attribution",
                "repository_file": "data/public/moa_fishery_environment_2024.csv",
                "retrieved_on": date,
                "notes": f"{PROCESSED_PUBLIC_LABEL}; decline magnitudes are not absolute concentration levels.",
            },
            {
                "source_id": "nbs_2025_aquatic_products",
                "publisher": "National Bureau of Statistics of China",
                "dataset": "2025 national economic and social development statistical communique",
                "coverage": "China, 2025; total, aquaculture and capture production",
                "url": NBS_2025_COMMUNIQUE_URL,
                "access": "Statistics extracted and normalized from official HTML",
                "license_or_terms": "National Bureau of Statistics website terms apply",
                "repository_file": "data/public/official_latest_aquatic_products_2025.csv",
                "retrieved_on": date,
                "notes": f"{PROCESSED_PUBLIC_LABEL}; national rows use production-method categories.",
            },
            {
                "source_id": "zhejiang_2025_aquatic_products",
                "publisher": "Zhejiang Provincial Bureau of Statistics / NBS Zhejiang Survey Office",
                "dataset": "2025 Zhejiang economic and social development statistical communique",
                "coverage": "Zhejiang, 2025; total, marine and freshwater production",
                "url": ZHEJIANG_2025_COMMUNIQUE_URL,
                "access": "Statistics extracted and normalized from official HTML",
                "license_or_terms": "Zhejiang statistics website terms apply",
                "repository_file": "data/public/official_latest_aquatic_products_2025.csv",
                "retrieved_on": date,
                "notes": f"{PROCESSED_PUBLIC_LABEL}; Zhejiang rows use water-body categories.",
            },
            {
                "source_id": "nbs_a0407",
                "publisher": "National Bureau of Statistics of China",
                "dataset": "Provincial annual aquatic-product production indicator A0407",
                "coverage": "31 provincial-level regions; coverage depends on sub-indicator",
                "url": NBS_INDICATOR_URL,
                "access": "Link and indicator code documented; automated endpoint returned HTTP 403 during retrieval",
                "license_or_terms": "National Bureau of Statistics website terms apply",
                "repository_file": "",
                "retrieved_on": date,
                "notes": "Not redistributed because a reliable machine-readable download could not be obtained from the official endpoint.",
            },
            {
                "source_id": "china_fisheries_statistical_yearbook",
                "publisher": "China Agriculture Press / Ministry statistical system",
                "dataset": "China Fisheries Statistical Yearbook",
                "coverage": "Province-level detailed fishery statistics",
                "url": "https://www.stats.gov.cn/fw/bmdcxmsp/bmzd/202302/t20230215_1907093.html",
                "access": "Commercial/copyrighted yearbook; not copied",
                "license_or_terms": "Copyrighted publication",
                "repository_file": "",
                "retrieved_on": date,
                "notes": "The official statistical-system page explains that annual results are published through the yearbook.",
            },
        ]
    )
    return pd.DataFrame(rows)


def download_public_data(output_dir: str | Path | None = None) -> dict[str, Path]:
    target = Path(output_dir) if output_dir else ROOT / "data" / "public"
    target.mkdir(parents=True, exist_ok=True)
    world_bank = fetch_world_bank_fao()
    moa = fetch_moa_communiques()
    moa_2024_detailed = fetch_moa_2024_detailed()
    environment_2024 = fetch_moa_environment_2024()
    latest_official = fetch_latest_official_aquatic_products()
    catalog = source_catalog(world_bank["retrieved_on"].iloc[0])
    paths = {
        "world_bank": target / "world_bank_fao_china_fisheries_2014_2023.csv",
        "moa": target / "moa_national_fishery_statistics.csv",
        "moa_2024_detailed": target / "moa_2024_detailed_fishery_statistics.csv",
        "environment_2024": target / "moa_fishery_environment_2024.csv",
        "latest_official": target / "official_latest_aquatic_products_2025.csv",
        "catalog": target / "source_catalog.csv",
    }
    world_bank.to_csv(paths["world_bank"], index=False)
    moa.to_csv(paths["moa"], index=False)
    moa_2024_detailed.to_csv(paths["moa_2024_detailed"], index=False)
    environment_2024.to_csv(paths["environment_2024"], index=False)
    latest_official.to_csv(paths["latest_official"], index=False)
    catalog.to_csv(paths["catalog"], index=False)
    return paths
