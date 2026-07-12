#!/usr/bin/env python3
"""s6_c4_region_draw — D52 提案ラウンド束 C4 アームの hole 位置選定 (無作為抽出)。

凍結済み edit_surface_map (n=1 provenance の projected_input、pinned HEAD) を母集団に、
seed 固定 RNG で領域一様・復元抽出を n ラウンド分行い、抽出列を provenance 込みで出力する。
正本 = docs/phase3-main-experiment.md「2026-07-13 着手時確定」節 (C4 抽出粒度) +
output/insights/2026-07-13_s6-round-execution-design.md §3.2/§3.3 (運用設計 v2)。

seed の決定権は準備者にない (v2 must-fix 4): --master-seed は人間が承認 gate で独立確定した
整数を受け取り、用途別 seed を決定的導出する (sha256("izanagi-s6:<s>:c4-draw") 先頭 8 バイト)。
抽出は決定的で、確定値と抽出全列は提案生成開始前に凍結コミットされる — 事後の引き直しは
コミット履歴で検証可能。

用法: python3 s6_c4_region_draw.py --master-seed <int> [--write PATH]
  --write なし = stdout に JSON。--write で凍結先ファイルに書き込む。
"""

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

N_ROUNDS = 20  # n = 20/アーム (着手時確定、変更禁止)
EXPECTED_POPULATION_SIZE = 17  # n=1 凍結時の領域数 — 違えば fails-closed で停止
SEED_DERIVATION = "int.from_bytes(sha256('izanagi-s6:<master>:c4-draw')[:8], 'big')"

PROVENANCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "output/insights/2026-07-10_s8a-n1-provenance.json"
)


def derive_seed(master_seed: int, purpose: str) -> int:
    digest = hashlib.sha256(f"izanagi-s6:{master_seed}:{purpose}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def load_population(provenance_path: Path) -> list[str]:
    with open(provenance_path) as f:
        prov = json.load(f)
    regions = [e["region"] for e in prov["projected_input"]["edit_surface_map"]]
    if len(regions) != len(set(regions)):
        sys.exit("fails-closed: edit_surface_map に重複領域がある")
    if len(regions) != EXPECTED_POPULATION_SIZE:
        sys.exit(
            f"fails-closed: 領域数 {len(regions)} != 凍結時 {EXPECTED_POPULATION_SIZE}"
            " — 母集団が n=1 凍結版と一致しない。人間判断を仰ぐこと"
        )
    return sorted(regions)  # 辞書順固定 (抽出の再現性は列の順序に依存する)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--master-seed", type=int, required=True,
        help="人間が承認 gate で独立確定した整数 (準備者は候補を提示しない)",
    )
    ap.add_argument("--write", metavar="PATH", help="凍結先ファイルに書き込む")
    args = ap.parse_args()

    regions = load_population(PROVENANCE_PATH)
    population_sha256 = hashlib.sha256(
        json.dumps(regions, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()
    draw_seed = derive_seed(args.master_seed, "c4-draw")
    rng = random.Random(draw_seed)
    drawn = rng.choices(regions, k=N_ROUNDS)  # 領域一様・復元

    result = {
        "what": "D52 提案ラウンド束 C4 アームの hole 位置選定 (領域一様・復元・seed 固定)",
        "authority": [
            "docs/phase3-main-experiment.md 2026-07-13 着手時確定 (C4 抽出粒度)",
            "output/insights/2026-07-13_s6-round-execution-design.md §3.2/§3.3 (v2)",
        ],
        "master_seed": args.master_seed,
        "master_seed_provenance": "人間確定 (承認 gate)。準備者は候補提示・試算をしていない",
        "seed_derivation_rule": SEED_DERIVATION,
        "derived_draw_seed": draw_seed,
        "n_rounds": N_ROUNDS,
        "population_source": str(PROVENANCE_PATH.name),
        "population_sorted": regions,
        "population_sha256": population_sha256,
        "python_version": sys.version.split()[0],
        "drawn_regions": drawn,
        "note": "抽出は決定的 (同 master seed・同母集団で全再現可能)。ラウンド i の C4 呼び出しは"
        " drawn_regions[i] を hole_region_directive とする",
    }
    text = json.dumps(result, ensure_ascii=False, indent=1) + "\n"
    if args.write:
        Path(args.write).write_text(text)
        print(f"written: {args.write}")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
