#!/usr/bin/env python3
"""requestId 単位で正しく数え直す (read-only)。

transcript は 1 API 応答を content block ごとに複数 record へ割る。usage は各 record に
複製されるので、record を数えると二重計上になる。requestId で dedupe する。
"""
import json
import os
import glob
import re
import sys
from collections import defaultdict, Counter

D = "/home/SFC/tanab/.claude/projects/-work-1-SFC-tanab-izanagi"
CH = 3.6
REDUCER = re.compile(r"\|\s*(head|tail|sed|awk|cut|sort|uniq|wc|grep)\b")


def bchars(b):
    t = b.get("type")
    if t == "text":
        return len(b.get("text") or "")
    if t == "thinking":
        return len(b.get("thinking") or "") + len(b.get("signature") or "")
    return len(json.dumps(b, ensure_ascii=False))


def main(paths):
    tot_req = 0
    tot_ctx = 0
    tot_out = 0
    tools_per_req = Counter()
    ctx_by_k = Counter()
    accum = defaultdict(int)
    tool_res = defaultdict(int)
    tool_cnt = defaultdict(int)
    bash_out_unbounded = 0
    bash_out_total = 0
    bash_n = 0
    sess_rows = []
    first_ctx = []

    for p in paths:
        req_ctx = {}
        req_out = {}
        req_tools = defaultdict(int)
        order = []
        id2name = {}
        id2cmd = {}
        s_accum = defaultdict(int)
        with open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.startswith("{"):
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                m = r.get("message") or {}
                c = m.get("content")
                rt = r.get("type")
                if rt == "assistant":
                    q = r.get("requestId") or m.get("id")
                    u = m.get("usage") or {}
                    if q and q not in req_ctx and u:
                        req_ctx[q] = (u.get("cache_read_input_tokens", 0) or 0) + \
                                     (u.get("cache_creation_input_tokens", 0) or 0) + \
                                     (u.get("input_tokens", 0) or 0)
                        req_out[q] = u.get("output_tokens", 0) or 0
                        order.append(q)
                if isinstance(c, str):
                    s_accum[f"{rt}:string"] += len(c)
                    continue
                if not isinstance(c, list):
                    continue
                for b in c:
                    if not isinstance(b, dict):
                        continue
                    bt = b.get("type")
                    n = bchars(b)
                    s_accum[f"{rt}:{bt}"] += n
                    if bt == "tool_use":
                        q = r.get("requestId") or m.get("id")
                        req_tools[q] += 1
                        id2name[b.get("id")] = b.get("name")
                        if b.get("name") == "Bash":
                            id2cmd[b.get("id")] = (b.get("input") or {}).get("command") or ""
                        s_accum[f"in:{b.get('name')}"] += n
                    elif bt == "tool_result":
                        nm = id2name.get(b.get("tool_use_id"), "?")
                        tool_res[nm] += n
                        tool_cnt[nm] += 1
                        if nm == "Bash":
                            bash_n += 1
                            bash_out_total += n
                            if not REDUCER.search(id2cmd.get(b.get("tool_use_id"), "")):
                                bash_out_unbounded += n
        nreq = len(order)
        if nreq < 20:
            continue
        sctx = sum(req_ctx.values())
        tot_req += nreq
        tot_ctx += sctx
        tot_out += sum(req_out.values())
        first_ctx.append(req_ctx[order[0]])
        for q in order:
            k = min(req_tools.get(q, 0), 4)
            tools_per_req[k] += 1
            ctx_by_k[k] += req_ctx[q]
        for k, v in s_accum.items():
            accum[k] += v
        sess_rows.append((os.path.basename(p)[:8], nreq, sctx, sum(s_accum.values())))

    print(f"=== 正しい計数 (requestId 単位, {len(sess_rows)} セッション) ===")
    print(f"API 応答数 (= round-trip)  : {tot_req:,}")
    print(f"Σ 入力 context (cache 含む): {tot_ctx/1e6:,.0f} M tokens")
    print(f"Σ 出力                     : {tot_out/1e6:,.1f} M tokens")
    print(f"平均 context / round-trip  : {tot_ctx//max(tot_req,1):,} tokens")
    print(f"初回 context 中央値 (固定 base): {sorted(first_ctx)[len(first_ctx)//2]:,} tokens")
    print(f"入力 : 出力 = {tot_ctx/max(tot_out,1):.0f} : 1")
    print()
    print("=== 1 応答あたりの tool_use 個数 ===")
    print(f"{'個数':>5}{'応答数':>9}{'割合':>8}{'読んだ context':>16}")
    for k in sorted(tools_per_req):
        lbl = f"{k}" if k < 4 else "4+"
        print(f"{lbl:>5}{tools_per_req[k]:>9,}{100*tools_per_req[k]/tot_req:>7.1f}%{ctx_by_k[k]/1e6:>13,.0f} M")
    ntools = sum(k * v for k, v in tools_per_req.items())
    withtool = sum(v for k, v in tools_per_req.items() if k > 0)
    print(f"\ntool 呼び出し総数 {ntools:,} / tool を含む応答 {withtool:,} = "
          f"平均 {ntools/max(withtool,1):.2f} tool/応答")
    print()
    print("=== 蓄積 context の内訳 ===")
    g = sum(v for k, v in accum.items() if not k.startswith("in:"))
    g += sum(v for k, v in accum.items() if k.startswith("in:"))
    shown = {k: v for k, v in accum.items()}
    tot_all = sum(shown.values())
    for k, v in sorted(shown.items(), key=lambda x: -x[1])[:14]:
        print(f"  {k:<26}{v:>13,} chars  ~{int(v/CH):>9,} tok  {100*v/tot_all:>5.1f}%")
    print(f"  {'合計':<26}{tot_all:>13,} chars  ~{int(tot_all/CH):>9,} tok")
    print(f"  1 セッションあたり蓄積 ~{int(tot_all/CH/max(len(sess_rows),1)):,} tok")
    print()
    print("=== Bash 出力 ===")
    print(f"  呼び出し {bash_n:,} 回 / 出力 {bash_out_total:,} chars")
    print(f"  うち reducer 無し: {bash_out_unbounded:,} chars "
          f"({100*bash_out_unbounded/max(bash_out_total,1):.0f}%)")
    print()
    base = sorted(first_ctx)[len(first_ctx) // 2]
    print("=== 感度 (この実測に基づく) ===")
    print(f"  round-trip を 1 本消す      → 約 {tot_ctx//max(tot_req,1):,} tok")
    print(f"  round-trip を 10% 消す      → 約 {int(0.10*tot_ctx)/1e6:,.0f} M tok "
          f"(全体の 10%、応答 {int(tot_req*0.1):,} 本)")
    print(f"  固定 base を 5k tok 削る    → 約 {5000*tot_req/1e6:,.0f} M tok "
          f"(全体の {100*5000*tot_req/tot_ctx:.1f}%)")
    print(f"  蓄積を 20% 削る             → 約 {0.20*(tot_ctx-base*tot_req)/1e6:,.0f} M tok "
          f"(全体の {100*0.20*(tot_ctx-base*tot_req)/tot_ctx:.0f}%)")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    files = sorted(glob.glob(os.path.join(D, "*.jsonl")), key=os.path.getmtime, reverse=True)[:n]
    main(files)
