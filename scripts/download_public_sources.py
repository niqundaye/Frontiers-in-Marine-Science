from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data" / "external"
SOURCES = {
    "frontiers_article.pdf": "https://www.frontiersin.org/journals/marine-science/articles/10.3389/fmars.2026.1809036/pdf",
    "moa_2023_fishery_communique.html": "https://yyj.moa.gov.cn/gzdt/202407/t20240705_6458486.htm",
}


def main() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    manifest = []
    for filename, url in SOURCES.items():
        target = TARGET / filename
        request = urllib.request.Request(url, headers={"User-Agent": "fishery-reproduction/0.1"})
        with urllib.request.urlopen(request, timeout=60) as response:
            content = response.read()
        target.write_bytes(content)
        manifest.append({"file": filename, "url": url, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()})
    (TARGET / "source_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

