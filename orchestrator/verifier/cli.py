# -*- coding: utf-8 -*-
"""verifier の CLI。

  python orchestrator/verify.py <trace_dir> [<trace_dir> ...]
  python -m verifier <trace_dir> ...

複数 trace ディレクトリを渡すと、それぞれを 1 run として検証し集約する
(roadmap §3.2 確率的検証: seed を変えた N run で毎回 cycle 無し → 信頼度 1-εⁿ。
Jitskit の reward-hack 対策とも合致)。

exit code (安全側): 0 = 全 run が certified serializable / 1 = いずれかで anomaly
(cycle) 検出 / 3 = いずれかが indeterminate (integrity 不良で認証不能) / 2 = 使用法・
パースエラー。--lenient で indeterminate を失敗扱いにしない (グラフ判定のみ)。
オーケストレータは exit 0 だけを「正しさゲート通過」とみなすこと (絶対規律2)。
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from .core import result_to_dict_v3, verify_trace_dir
from .parse import ParseError
from .report import render_text


def _nonnegative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("非負整数を指定すること") from None
    if parsed < 0:
        raise argparse.ArgumentTypeError("非負整数を指定すること")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="verify",
        description="Izanagi mini trace verifier (serializability / G2 cycle 検出)")
    p.add_argument("dirs", nargs="+", metavar="TRACE_DIR",
                   help="trace_*.log を含むディレクトリ (複数 = 複数 run/seed)")
    p.add_argument("--json", action="store_true",
                   help="結果を JSON で stdout に出す")
    p.add_argument("--max-report", type=int, default=20,
                   help="1 run あたり報告する witness cycle の最大本数 (default 20)")
    p.add_argument("--expected-commits", type=_nonnegative_int, default=None,
                   help="単一 run の trace 外 commit counter witness")
    p.add_argument("--protocol", default=None,
                   help="proof-surface assessment 対象 protocol")
    p.add_argument("--ccbench-root", default=None,
                   help="対象 protocol の cc/ を含む CCBench source root")
    p.add_argument("--lenient", action="store_true",
                   help="integrity 不良 (indeterminate) を失敗扱いにしない "
                        "(グラフ判定のみ見たいとき。既定は安全側=失敗)")
    p.add_argument("--quiet", action="store_true",
                   help="certified な run のテキスト詳細を抑制 (集約のみ)")
    return p


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.expected_commits is not None and len(args.dirs) != 1:
        parser.error("--expected-commits は単一 TRACE_DIR のときだけ指定できる")
    results = []
    try:
        for d in args.dirs:
            results.append(verify_trace_dir(
                d, max_report=args.max_report,
                expected_commits=args.expected_commits,
                protocol=args.protocol,
                ccbench_root=args.ccbench_root,
            ))
    except ParseError as e:
        print(f"parse error: {e}", file=sys.stderr)
        return 2

    n_cert = sum(1 for r in results if r.certified)
    n_anom = sum(1 for r in results if r.verdict == "non-serializable")
    n_indet = sum(1 for r in results if r.verdict == "indeterminate")

    if args.json:
        out = {
            "runs": len(results),
            "certified_serializable": n_cert,
            "non_serializable": n_anom,
            "indeterminate": n_indet,
            "results": [result_to_dict_v3(r) for r in results],
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        for r in results:
            if args.quiet and r.certified:
                print(f"[SERIALIZABLE] {r.trace_dir} "
                      f"(txns={r.n_txns}, edges={r.n_edges})")
            else:
                print(render_text(r))
                print()
        # 確率的検証の集約
        print(f"== {len(results)} run(s): {n_cert} serializable(certified), "
              f"{n_anom} non-serializable, {n_indet} indeterminate ==")

    # 安全側のゲート: 確定異常=1、認証不能(integrity 不良)=3。--lenient で後者を無視。
    if n_anom > 0:
        return 1
    if n_indet > 0 and not args.lenient:
        return 3
    return 0
