# -*- coding: utf-8 -*-
"""P2-5 誘導アーム: critic-in-the-loop の試行ハーネス (replay、新規直列計測ゼロ)。

1 試行 = critic が「これまで評価した genome の online digest」だけを見て次に評価する genome を
1 つずつ選び、winner-tied set に到達するまで (または全 8 評価し尽くすまで) 進む過程。各 genome の
fitness/LI は P2-2 WAL から replay で配る (新規 bench は走らせない、規律4)。

**リーク制御 (規律6/D14):**
- critic に見せるのは「評価済み genome だけ」が育つ誘導専用 WAL から作った digest と、未評価候補の
  **ラベルだけ** (fitness は伏せる)。winner-tied set への到達/未到達も **critic には伝えない**
  (実探索では「これが最適だ」と分かる手段は無い — 到達は事後に Python が軌跡から測る)。
- `online_digest` が『digest の genome 数 ≤ 評価回数』を実行時 assert (layout 取り違え等の配線ミスへの
  sanity。両辺が同一誘導 WAL の STAGE_COMMIT 由来ゆえ恒真で独立防壁ではない — D26 / online_digest.py
  docstring 参照。中立性の真の担保は WAL 分離 + import 物理分離)。
- critic が候補外/重複/空間外 (livelock (0,0)) を指したら **検疫して拒否** (S4 配線まで止めるトリガ)。
- 初手は critic 信号が無いので **seed 固定のランダム** (誘導も random も初手は同条件 = 公平)。

CLI (critic エージェントは start→(evaluate)*→停止 を Bash で回す):
  start    --workload <tag> --seed <n> --trial <id> [--root <dir>]   初手評価 + 状態表示
  evaluate --trial <id> --genome <label> [--root <dir>]             1 genome 評価 + 状態表示
  result   --trial <id> [--root <dir>]                              到達コスト/軌跡 (Python 用、critic 非公開)
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from campaign import ident, replay, wal                           # noqa: E402
from campaign.genome import SILO_SPACE                            # noqa: E402
from campaign.layout import CampaignLayout, repo_output_root      # noqa: E402
from campaign.model import (CampaignConfig, STAGE_BENCH_DONE,     # noqa: E402
                            STAGE_BUILD_START, STAGE_COMMIT,
                            STAGE_VERIFY_DONE)
from campaign.p2_2 import BETWEEN_RUN_CV, ENV_TAG, WORKLOADS      # noqa: E402
from campaign.search_baselines import reached_cost               # noqa: E402
from critic.online_digest import online_digest_text              # noqa: E402

BUDGET = len(SILO_SPACE.enumerate())          # 予算上限 N=8 (最悪 = 全探索に縮退)


def _workload_of(tag: str) -> dict:
    for t, wl in WORKLOADS:
        if t == tag:
            return wl
    raise KeyError(f"未知の workload: {tag} (選択肢 {[t for t, _ in WORKLOADS]})")


def _trial_layout(trial: str, root: str = "") -> CampaignLayout:
    base = root or repo_output_root()
    return CampaignLayout(root=os.path.join(base, "campaigns", f"p2-5-guided-{trial}"))


def _meta_path(layout: CampaignLayout) -> str:
    return os.path.join(layout.root, "meta.json")


def _read_meta(layout: CampaignLayout) -> dict:
    with open(_meta_path(layout), encoding="utf-8") as f:
        return json.load(f)


def _write_meta(layout: CampaignLayout, meta: dict) -> None:
    os.makedirs(layout.root, exist_ok=True)
    with open(_meta_path(layout), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)


def _trial_config(meta: dict, trial: str) -> CampaignConfig:
    """guided trial の meta を identity lock の正準 pre-image へ射影する。"""
    required = {"tag", "workload", "seed", "trial"}
    if not isinstance(meta, dict) or set(meta) != required:
        raise ValueError("guided meta schema が exact 4 keys でない")
    if meta.get("trial") != trial:
        raise ValueError(
            f"guided meta trial が引数と不一致: stored={meta.get('trial')!r}, "
            f"requested={trial!r}")
    tag = meta["tag"]
    workload = meta["workload"]
    seed = meta["seed"]
    if not isinstance(tag, str) or not isinstance(workload, dict):
        raise ValueError("guided meta の tag/workload 型が不正")
    return CampaignConfig(
        spec_slug="p2-5-guided", search_tag="critic-replay",
        spec_content="P2-5 critic-in-the-loop replay trial",
        ccbench_commit="p2-2-replay-landscape",
        search_config={"tag": tag, "workload": workload, "seed": str(seed)},
        trial=trial,
    )


def _surface_repair(result: wal.WalTailRepairResult) -> None:
    if result.status == "repaired":
        print(json.dumps({
            "wal_tail_repair": {
                "status": result.status,
                "original_size": result.original_size,
                "final_size": result.final_size,
                "removed_bytes": result.removed_bytes,
                "removed_sha256": result.removed_sha256,
                "preview": result.preview,
                "receipt_path": result.receipt_path,
            }
        }, ensure_ascii=False, sort_keys=True))


def _evaluated_canon(layout: CampaignLayout) -> List[str]:
    """誘導 WAL の commit 順 = 評価順 (variant = canonical genome 文字列)。"""
    return [r.variant for r in wal.read_records(layout) if r.stage == STAGE_COMMIT]


def _log_eval(layout: CampaignLayout, res: replay.GenomeResult) -> None:
    """1 genome の評価を replay 値で誘導 WAL に記録 (build_start→verify→bench→commit)。"""
    v = res.genome                                # variant id = canonical
    wal.log(layout, v, STAGE_BUILD_START, ENV_TAG, {"genome": res.genome})
    wal.log(layout, v, STAGE_VERIFY_DONE, ENV_TAG,
            {"certified": res.certified,
             "verdict": "serializable" if res.certified else "unknown"})
    wal.log(layout, v, STAGE_BENCH_DONE, ENV_TAG,
            {"median_tps": res.fitness_tps, "tps": res.tps,
             "leading_indicators": res.leading_indicators})
    wal.log(layout, v, STAGE_COMMIT, ENV_TAG, {"fitness_tps": res.fitness_tps})


def _print_state(layout: CampaignLayout, tag: str, workload: dict) -> None:
    """critic に見せる状態: 評価済み digest + 未評価候補ラベル (fitness/到達は伏せる)。"""
    evaluated = _evaluated_canon(layout)
    n = len(evaluated)
    text = online_digest_text(layout, tag, workload, n)            # 配線 sanity assert 込み (恒真、D26)
    all_labels = [replay.genome_label(g.flags) for g in SILO_SPACE.enumerate()]
    eval_labels = {replay.genome_label(replay.parse_flags(c)) for c in evaluated}
    remaining = [lab for lab in all_labels if lab not in eval_labels]
    print(f"=== 評価済み {n}/{BUDGET} (workload={tag}) ===")
    print(text)
    print(f"未評価候補 (次に評価できる genome): {remaining}")
    if remaining:
        print("次に評価する genome を 1 つ選び "
              "`evaluate --trial <id> --genome <label>` を呼べ。"
              "leading indicators から帰属し、最速と確信したら停止してよい。")
    else:
        print("全 genome 評価済み。停止せよ。")


def cmd_start(args) -> int:
    layout = _trial_layout(args.trial, args.root)
    # lstat/fstat の失敗を os.path.exists で False に畳まず、lock より先に拒否する。
    wal.wal_bytes_present(layout)
    if os.path.exists(layout.wal_file):
        print(f"trial {args.trial!r} は既存。別 trial 名を使うか dir を消せ。", file=sys.stderr)
        return 2
    layout.ensure()
    tag = args.workload
    workload = _workload_of(tag)
    meta = {"tag": tag, "workload": workload,
            "seed": args.seed, "trial": args.trial}
    # 既存 WAL 拒否 → lock 原子獲得 → meta の順。競合敗者は meta/WAL に触れない。
    if not ident.ensure_campaign_identity(_trial_config(meta, args.trial), layout):
        print(json.dumps({
            "rejected": "campaign.lock は別 start が先に獲得済み",
            "reason": "campaign-lock-already-acquired",
            "trial": args.trial,
        }, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 2
    _write_meta(layout, meta)
    landscape = replay.load_landscape(tag)        # P2-2 の実 landscape (real output root)
    replay.assert_complete(landscape, tag)
    rng = random.Random(int(args.seed))           # 初手 = seed 固定ランダム (critic 信号なし)
    first = rng.choice(SILO_SPACE.enumerate())
    _log_eval(layout, replay.replay_evaluate(landscape, first))
    _print_state(layout, tag, workload)
    return 0


def cmd_evaluate(args) -> int:
    layout = _trial_layout(args.trial, args.root)
    if not os.path.exists(_meta_path(layout)):
        print(f"trial {args.trial!r} が無い。先に start せよ。", file=sys.stderr)
        return 2
    meta = _read_meta(layout)
    cfg = _trial_config(meta, args.trial)  # trial exact 検査より前に repair しない
    _surface_repair(ident.ensure_resumable_wal(cfg, layout))
    tag, workload = meta["tag"], meta["workload"]
    landscape = replay.load_landscape(tag)
    evaluated = set(_evaluated_canon(layout))
    # 検疫層 (規律6): 空間外/不正ラベルは拒否 (livelock (0,0) 等を黙って評価しない = S4 トリガ)。
    try:
        g = replay.genome_from_label(args.genome)
    except ValueError as e:
        print(json.dumps({"rejected": str(e),
                          "note": "候補リストにあるラベルから選べ (空間外は評価しない)"},
                         ensure_ascii=False))
        return 3
    if g.canonical() in evaluated:
        print(json.dumps({"rejected": f"{args.genome} は評価済み (重複は予算の無駄)",
                          "note": "未評価候補から選べ"}, ensure_ascii=False))
        return 3
    if len(evaluated) >= BUDGET:
        print(json.dumps({"rejected": "予算上限 (全 genome 評価済み)"}, ensure_ascii=False))
        return 3
    _log_eval(layout, replay.replay_evaluate(landscape, g))
    _print_state(layout, tag, workload)
    return 0


def trial_result(trial: str, root: str = "") -> dict:
    """1 試行の到達コスト + 軌跡 (Python/解析用。critic には公開しない指標)。"""
    layout = _trial_layout(trial, root)
    meta = _read_meta(layout)
    tag = meta["tag"]
    landscape = replay.load_landscape(tag)
    tied = replay.winner_tied_set(landscape, BETWEEN_RUN_CV)
    order = _evaluated_canon(layout)
    traj = [replay.genome_label(replay.parse_flags(c)) for c in order]
    rc = reached_cost(order, tied)
    reached = bool(order) and order[rc - 1] in tied
    return {"trial": trial, "tag": tag, "seed": meta.get("seed"),
            "trajectory": traj, "n_evaluated": len(order),
            "reached_cost": rc, "reached": reached,
            "tied_set": sorted(replay.genome_label(landscape[c].flags) for c in tied),
            "final_pick": traj[-1] if traj else None}


def cmd_result(args) -> int:
    print(json.dumps(trial_result(args.trial, args.root), ensure_ascii=False, indent=1))
    return 0


def main(argv) -> int:
    p = argparse.ArgumentParser(description="P2-5 誘導アーム試行ハーネス")
    p.add_argument("--root", default="", help="誘導 WAL の出力 root (試験用。既定=リポジトリ output)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start"); s.add_argument("--workload", required=True)
    s.add_argument("--seed", required=True); s.add_argument("--trial", required=True)
    e = sub.add_parser("evaluate"); e.add_argument("--trial", required=True)
    e.add_argument("--genome", required=True)
    r = sub.add_parser("result"); r.add_argument("--trial", required=True)
    args = p.parse_args(argv[1:])
    return {"start": cmd_start, "evaluate": cmd_evaluate,
            "result": cmd_result}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
