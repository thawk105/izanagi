#!/usr/bin/env python3
"""codex 子のトークン消費を rollout ログから測る (read-only)。"""
import json
import os
import glob
import sys
from collections import Counter, defaultdict

ROOT = os.path.expanduser("~/.codex/sessions")


def main(since):
    files = sorted(glob.glob(os.path.join(ROOT, "**", "rollout-*.jsonl"), recursive=True))
    files = [f for f in files if os.path.basename(f)[8:18] >= since]
    print(f"rollout {len(files)} 本 (>= {since})")
    tot_in = tot_cached = tot_out = tot_reason = 0
    per_sess = []
    models = Counter()
    efforts = Counter()
    turn_counts = []
    for p in files:
        last = None
        n_turn = 0
        model = eff = None
        try:
            fh = open(p, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                pl = r.get("payload") or {}
                ty = r.get("type") or pl.get("type")
                if ty == "turn_context" or "model" in pl:
                    model = pl.get("model") or model
                    eff = pl.get("effort") or pl.get("model_reasoning_effort") or eff
                info = pl.get("info") or {}
                tu = info.get("total_token_usage") or pl.get("total_token_usage")
                if tu:
                    last = tu
                if ty == "event_msg" and pl.get("type") == "token_count":
                    n_turn += 1
        if not last:
            continue
        i = last.get("input_tokens", 0) or 0
        c = last.get("cached_input_tokens", 0) or 0
        o = last.get("output_tokens", 0) or 0
        rt = last.get("reasoning_output_tokens", 0) or 0
        tot_in += i
        tot_cached += c
        tot_out += o
        tot_reason += rt
        models[model or "?"] += 1
        efforts[str(eff)] += 1
        turn_counts.append(n_turn)
        per_sess.append((os.path.basename(p)[8:24], i, c, o, rt, n_turn, model, eff))

    n = len(per_sess)
    print(f"usage を持つ rollout : {n}")
    print(f"入力 (cached 含む)   : {tot_in:,}")
    print(f"  うち cached        : {tot_cached:,}  ({100*tot_cached/max(tot_in,1):.0f}%)")
    print(f"  非 cache 入力      : {tot_in-tot_cached:,}")
    print(f"出力                 : {tot_out:,}")
    print(f"  うち reasoning     : {tot_reason:,}  ({100*tot_reason/max(tot_out,1):.0f}%)")
    print(f"1 子あたり 入力中央値: {sorted(x[1] for x in per_sess)[n//2]:,}")
    print(f"1 子あたり 出力中央値: {sorted(x[3] for x in per_sess)[n//2]:,}")
    print(f"1 子あたり turn 中央値: {sorted(turn_counts)[n//2]}")
    print()
    print("model:", models.most_common(6))
    print("effort:", efforts.most_common(6))
    print()
    print("=== 入力トークン上位 15 子 ===")
    print(f"{'session':<18}{'入力':>12}{'cached':>12}{'出力':>10}{'reason':>10}{'turn':>6}  model/effort")
    for s in sorted(per_sess, key=lambda x: -x[1])[:15]:
        print(f"{s[0]:<18}{s[1]:>12,}{s[2]:>12,}{s[3]:>10,}{s[4]:>10,}{s[5]:>6}  {s[6]}/{s[7]}")
    print()
    tot = tot_in + tot_out
    print(f"codex 合計 (入力+出力) : {tot/1e6:,.1f} M tokens")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "2026-08-01")
