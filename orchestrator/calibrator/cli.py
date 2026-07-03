# -*- coding: utf-8 -*-
"""calibrator の CLI (タスク4b 実機実行)。

  python3 orchestrator/calibrate.py --binary <ycsb_*.exe> --env-tag linux-baremetal \\
      --threads 16 [--workload ycsb_zipf_skew=0,ycsb_rratio=50] [--numactl interleave=all]

確定した校正を env スコープ output/env/<env-tag>/calibration/ に書く (D13):
  - calibration_t<threads>_<workload>.json … 機械可読 (全測定点・飽和推移・noise floor の生値)
  - calibration_t<threads>_<workload>.md   … 「なぜそのレコード数?」の人間可読な根拠 (査読先回り)

絶対規律1: --binary は trace-disabled build (`build/`, -DTRACE=0) を指すこと。
絶対規律4: その binary は -DLinux スレッドピンニング済みを前提 (submodule master に還元済みで
常に有効 — cpu.hh setThreadAffinity。旧 patches/linux-thread-pinning.patch は D16 で還元後に削除)。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List, Optional

from .report import render_text, result_to_dict
from .sweep import MAX_RECORDS_DEFAULT, calibrate


def _parse_kv(s: Optional[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not s:
        return out
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        k, _, v = part.partition("=")
        out[k.strip()] = v.strip()
    return out


def _numactl_arg(s: Optional[str]) -> Optional[List[str]]:
    """'interleave=all' → ['numactl','--interleave=all']。'none'/'' → None。"""
    if not s or s.lower() == "none":
        return None
    parts = []
    for tok in s.split(","):
        tok = tok.strip()
        if not tok:
            continue
        parts.append("--" + tok if not tok.startswith("-") else tok)
    return ["numactl"] + parts if parts else None


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="calibrate",
        description="Izanagi calibrator — レコード数飽和点 + noise floor を実機で確定")
    p.add_argument("--binary", required=True,
                   help="ycsb_*.exe (trace-disabled / -DLinux ピンニング済み build)")
    p.add_argument("--env-tag", required=True,
                   help="環境タグ (例 linux-baremetal)。出力先 env スコープを決める")
    p.add_argument("--threads", type=int, required=True,
                   help="固定 thread 数 (飽和点は thread 依存 → 必ず明示)")
    p.add_argument("--workload", default="",
                   help="ycsb gflag の k=v をカンマ区切り (例 ycsb_zipf_skew=0,ycsb_rratio=50)")
    p.add_argument("--start-records", type=int, default=1_000_000)
    p.add_argument("--max-records", type=int, default=MAX_RECORDS_DEFAULT,
                   help="倍々スイープの上限。飽和を確認したら早期打ち切り (既定 16m)")
    p.add_argument("--extime", type=int, default=3)
    p.add_argument("--sweep-reps", type=int, default=3)
    p.add_argument("--noise-reps", type=int, default=10)
    p.add_argument("--clocks-per-us", type=int, default=None,
                   help="指定すれば TSC 実測をスキップしこの値を使う")
    p.add_argument("--numactl", default="interleave=all",
                   help="numactl メモリ方針 (例 interleave=all / membind=0 / none)")
    p.add_argument("--out-root", default=None,
                   help="出力ルート (既定 = リポジトリの output/)")
    return p


def _workload_tag(workload: Dict[str, str]) -> str:
    """ファイル名用の短い workload 署名。飽和点は workload (特に skew) で変わる
    ので、thread だけでなく workload でも出力を分ける (D13 の『入力非依存』前提が
    skew では崩れるため。worklog/insight 参照)。"""
    parts = []
    skew = workload.get("ycsb_zipf_skew")
    if skew is not None:
        parts.append("skew" + str(skew).replace(".", "p"))
    rratio = workload.get("ycsb_rratio")
    if rratio is not None:
        parts.append("rr" + str(rratio))
    rmw = workload.get("ycsb_rmw")
    if rmw is not None:
        parts.append("rmw" + str(rmw))
    return "_".join(parts) if parts else "default"


def _output_root(explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    # orchestrator/calibrator/cli.py → リポジトリルート/output
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(os.path.dirname(here))
    return os.path.join(repo, "output")


def _assert_trace_disabled_binary(binary: str) -> None:
    """--binary が trace-disabled build であることを nm で検査する (絶対規律1)。

    calibration は入力非依存の計測基盤 (以後の全 campaign の動作点) なので、trace-enabled
    バイナリで校正すると観測者効果が基盤全体へ静かに伝播する。buildcache.build() 経路の
    継続検査と同じ判定を、手渡し binary の入口にも置く (docstring の規約だけでは防壁が
    人間の注意力頼みになる)。nm 不在/失敗も fails-closed で停止する。
    ※ campaign.buildcache._assert_no_trace_symbols と同型の小検査。calibrator は campaign
    に依存しない層のため、import せず局所実装で重複させている (層の分離 > DRY)。"""
    import subprocess
    try:
        r = subprocess.run(["nm", "-C", binary], capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError) as e:
        raise SystemExit(f"規律1 検査不能: nm を起動できない ({e})。trace シンボル漏れを"
                         f"検査できない環境で calibration しない (fails-closed)")
    if r.returncode != 0:
        raise SystemExit(f"規律1 検査不能: nm が失敗 (rc={r.returncode}): "
                         f"{r.stderr[-200:]} (fails-closed で停止)")
    if any("izanagi_trace" in ln.lower() for ln in r.stdout.splitlines()):
        raise SystemExit(
            f"絶対規律1 違反: {binary} は trace-enabled build (izanagi_trace シンボル検出)。"
            f"calibration は trace-disabled build (build/, -DCCBENCH_TRACE=0) で行うこと")


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if not os.path.exists(args.binary):
        print(f"binary not found: {args.binary}", file=sys.stderr)
        return 2
    _assert_trace_disabled_binary(os.path.abspath(args.binary))

    result = calibrate(
        binary=os.path.abspath(args.binary),
        env_tag=args.env_tag,
        threads=args.threads,
        workload=_parse_kv(args.workload),
        start_records=args.start_records,
        max_records=args.max_records,
        extime=args.extime,
        sweep_reps=args.sweep_reps,
        noise_reps=args.noise_reps,
        numactl=_numactl_arg(args.numactl),
        clocks_per_us=args.clocks_per_us,
    )

    # env スコープに書き出す (D13)
    out_dir = os.path.join(_output_root(args.out_root), "env",
                           args.env_tag, "calibration")
    os.makedirs(out_dir, exist_ok=True)
    stem = f"calibration_t{args.threads}_{_workload_tag(_parse_kv(args.workload))}"
    json_path = os.path.join(out_dir, stem + ".json")
    md_path = os.path.join(out_dir, stem + ".md")

    with open(json_path, "w") as f:
        json.dump(result_to_dict(result), f, indent=2, ensure_ascii=False)
    with open(md_path, "w") as f:
        f.write("# calibration: " + args.env_tag +
                f" / threads={args.threads}\n\n")
        f.write("```\n" + render_text(result) + "\n```\n")

    print()
    print(render_text(result))
    print()
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    return 0
