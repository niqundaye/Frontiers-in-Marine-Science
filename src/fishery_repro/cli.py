from __future__ import annotations

import argparse
from pathlib import Path

from .benchmark import run_smoke_benchmark
from .calibrated import write_calibrated_data
from .config import ROOT, load_config
from .dataset import write_audit
from .figures import make_all_figures
from .manifest import write_manifest
from .public_data import download_public_data


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reproduce the disclosed and reconstructable results of Frontiers 13:1809036")
    parser.add_argument(
        "command",
        choices=["data", "figures", "audit", "benchmark", "public-data", "all"],
        nargs="?",
        default="all",
    )
    parser.add_argument("--config", default=str(ROOT / "configs" / "paper.yaml"))
    parser.add_argument("--output-root", default=str(ROOT / "results"))
    return parser


def main() -> None:
    args = _parser().parse_args()
    config = load_config(args.config)
    output_root = Path(args.output_root)
    seed = int(config["seed"])
    reconstruction = config["reconstruction"]

    if args.command in {"data", "all"}:
        write_calibrated_data(output_root / "data", seed=seed, step=int(reconstruction["generations_step"]))
    if args.command in {"figures", "all"}:
        make_all_figures(
            output_dir=output_root / "figures",
            data_dir=output_root / "data",
            formats=tuple(reconstruction["export_formats"]),
            dpi=int(reconstruction["dpi"]),
            seed=seed,
            step=int(reconstruction["generations_step"]),
        )
    if args.command in {"audit", "all"}:
        write_audit(output_root / "tables" / "data_audit.csv")
    if args.command in {"benchmark", "all"}:
        smoke = config["benchmark"]
        run_smoke_benchmark(
            output=output_root / "benchmark" / "smoke_summary.csv",
            population=int(smoke["smoke_population"]),
            generations=int(smoke["smoke_generations"]),
            seed=seed,
        )
    if args.command == "public-data":
        download_public_data(ROOT / "data" / "public")
    manifest = write_manifest(output_root, output_root / "MANIFEST.csv")
    print(f"Reproduction outputs written to: {output_root.resolve()}")
    print(f"Manifest: {manifest.resolve()}")


if __name__ == "__main__":
    main()
