from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime, timezone
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
}

NBS_INDICATOR_URL = "https://data.stats.gov.cn/easyquery.htm?cn=E0103&zb=A0407"
WORLD_BANK_LICENSE_URL = "https://datacatalog.worldbank.org/public-licenses"


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        cleaned = " ".join(data.split())
        if cleaned:
            self.parts.append(cleaned)


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
    "total_economic_output": ((r"全社会渔业经济总产值(?:达到|为)?\s*([0-9.]+)\s*亿元",), 1.0, "100 million RMB"),
    "fisher_per_capita_net_income": ((r"全国渔民人均纯收入(?:达到|为)?\s*([0-9.]+)\s*元",), 1.0, "RMB/year"),
    "total_aquatic_products": ((r"全国水产品总产量(?:达到|为)?\s*([0-9.]+)\s*万吨",), 10000.0, "tonnes"),
    "aquaculture_production": ((r"其中[，,:：\s]*养殖产量\s*([0-9.]+)\s*万吨",), 10000.0, "tonnes"),
    "capture_production": ((r"捕捞产量\s*([0-9.]+)\s*万吨",), 10000.0, "tonnes"),
    "distant_water_capture": ((r"远洋渔业产量\s*([0-9.]+)\s*万吨",), 10000.0, "tonnes"),
    "processing_enterprises": ((r"水产加工企业\s*([0-9.]+)\s*个",), 1.0, "count"),
    "cold_storage_units": ((r"水产冷库\s*([0-9.]+)\s*座",), 1.0, "count"),
    "motorized_fleet_power": ((r"机动渔船[^。]{0,120}?总功率\s*([0-9.]+)\s*万千瓦",), 10000.0, "kW"),
    "aquatic_exports_value": ((r"出口量[^。]{0,80}?出口额\s*([0-9.]+)\s*亿美元", r"出口额\s*([0-9.]+)\s*亿美元"), 100.0, "million USD"),
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
    catalog = source_catalog(world_bank["retrieved_on"].iloc[0])
    paths = {
        "world_bank": target / "world_bank_fao_china_fisheries_2014_2023.csv",
        "moa": target / "moa_national_fishery_statistics.csv",
        "catalog": target / "source_catalog.csv",
    }
    world_bank.to_csv(paths["world_bank"], index=False)
    moa.to_csv(paths["moa"], index=False)
    catalog.to_csv(paths["catalog"], index=False)
    return paths
