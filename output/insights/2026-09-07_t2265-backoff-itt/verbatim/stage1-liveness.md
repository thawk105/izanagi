# 段 1 の生死確認 (DW-G01) — 反実仮想の腕を計算ノードで初めて走らせた

**この確認は事前登録を凍結する前に行った。指定 outcome (窓の commit 速度・その比・`median_tps`・
`abort_rate`・方向的中率) は見ていない。** 見たのは構造と割当だけであり、検査器は field を allowlist で
絞ったうえで先に書いてから artifact を開いた。

**ただし「腕の出力を一切見ていない」とは言えない。** event 数・割当比・割当前の両方向可否・反転の
実現率はいずれも**処置に依存する構造量**であり、本文書はそれを主層の説明と反復数の説明に使っている
(段 3 の敵対相談 2 本の指摘。裁定は `s4-ruling.md` の R1・R6、開示は事前登録 §0.1)
(検査器の逐語は本文書の末尾 §「検査器の逐語」に置く。**実行可能 file として repo へ入れていない** —
D95 の実装面は Codex `role=author` が書く契約であり、親が書いた使い捨ての検査器は逐語で残す)。

## 投入

- 固定 checkout: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-backoff-itt/submit-tree`
  (detached、`cf4273f5671ecda87c6f1b76148df239ce043ead` = 着手時の local main、tracked-clean)
- job `0:981337.nqsv` / host `bnode009` / 2026-09-07 19:07〜19:09 JST
- 既登録の `tools/pegasus/probes/t2187_adaptive_const_probe.pbs` を**引数を 1 つも変えずに**使い、
  `IZANAGI_T2187_BACKOFF_TRACE=1` と反実仮想の 3 腕、workload 3 種、threads 24+48 を渡した。
  **投入経路の契約は 1 byte も変えていない** (pbs 135-143 行が反実仮想の cell 集合を既に受理形として
  持っている)。
- 出力: `/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/counterfactual-liveness/stage1-rep0-0_981337.nqsv.json`

## 束縛

| 項目 | 値 |
| --- | --- |
| `schema_version` | `izanagi-dynamic-backoff-trace/v3` |
| `throughput_scope` / `headline_eligible` | `diagnostic_only` / `False` |
| `counterfactual_preregistration` | `pending` (本 wave が sha256 束縛へ変える対象) |
| `repo_head` | `cf4273f5671ecda87c6f1b76148df239ce043ead` |
| patch A | `9b2153e0547e167888ba2616750951365c4a075a80f9a95be6000e60b6f8f54b` |
| patch B | `f3fe6b7e67931775bcef0a7831dda8c6cb53dfc7fc52a74f4508360e1fedf824` |
| patch C | `794b7b48dd19e30560dddc27f4408d67923d801241046df53257a8aefe82a396` |
| `patch_stack_sha256` | `192be42db83b314b0eddd399eb47d6a47ac7afb859bc7085cd5f035e8cd7433c` |
| job 所要 | `job_total_seconds` 137.55 / `wall_seconds` 127.45 / `cpu_seconds` 2158.18 |

## 構造と割当 (18 run、trace record はすべて v2、落ちた record 0 件)

| cell | workload | threads | policy | event 数 | Z=1 の割合 | 割当前に両方向可の割合 | 反転が実現した割合 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `cw-as-dyn-p0` | write-heavy | 24 | 0 | 961 | 0.000 | 0.282 | 0.000 |
| `cw-as-dyn-p1` | write-heavy | 24 | 1 | 385 | 1.000 | 0.990 | 1.000 |
| `cw-as-dyn-p2` | write-heavy | 24 | 2 | 538 | 0.526 | 0.976 | 0.520 |
| `cw-as-dyn-p0` | write-heavy | 48 | 0 | 812 | 0.000 | 0.869 | 0.000 |
| `cw-as-dyn-p1` | write-heavy | 48 | 1 | 553 | 1.000 | 0.246 | 0.492 |
| `cw-as-dyn-p2` | write-heavy | 48 | 2 | 583 | 0.521 | 0.967 | 0.509 |
| `cw-as-dyn-p0` | balanced | 24 | 0 | 906 | 0.000 | 0.249 | 0.000 |
| `cw-as-dyn-p1` | balanced | 24 | 1 | 306 | 1.000 | 0.987 | 1.000 |
| `cw-as-dyn-p2` | balanced | 24 | 2 | 406 | 0.530 | 0.973 | 0.527 |
| `cw-as-dyn-p0` | balanced | 48 | 0 | 1077 | 0.000 | 0.526 | 0.000 |
| `cw-as-dyn-p1` | balanced | 48 | 1 | 412 | 1.000 | 0.939 | 0.964 |
| `cw-as-dyn-p2` | balanced | 48 | 2 | 452 | 0.520 | 0.982 | 0.518 |
| `cw-as-dyn-p0` | read-heavy | 24 | 0 | 1163 | 0.000 | 0.248 | 0.000 |
| `cw-as-dyn-p1` | read-heavy | 24 | 1 | 581 | 1.000 | 0.991 | 1.000 |
| `cw-as-dyn-p2` | read-heavy | 24 | 2 | 603 | 0.517 | 0.982 | 0.516 |
| `cw-as-dyn-p0` | read-heavy | 48 | 0 | 1161 | 0.000 | 0.247 | 0.000 |
| `cw-as-dyn-p1` | read-heavy | 48 | 1 | 747 | 1.000 | 0.995 | 1.000 |
| `cw-as-dyn-p2` | read-heavy | 48 | 2 | 1157 | 0.523 | 0.971 | 0.516 |

`backoff_trace_symbol_count` = 4、`backoff_trace_string_count` = 2 が全 run で一定。
trace event の field は 16 個で、反実仮想の 4 項目
(`recommended_delta_sign` / `assigned_invert` / `inversion_realized` / `both_actions_feasible`)
が全 run に載っている。

## 読み取れたこと

1. **腕は 3 本とも設計どおり動いている。** policy 0 は一度も反転せず、policy 1 は毎回反転を割り当て、
   policy 2 は 0.517〜0.530 の割合で反転を割り当てる。**割当の無作為化は生きている。**
2. **policy 2 では割当の約 98% が実際の反転として実現する** (0.509/0.521 〜 0.527/0.530)。
   残りは clamp に当たった分である。
3. **policy 2 では「割当前に両方向とも可」が 0.967〜0.982 とほぼ全部である。** 一方 policy 0 では
   0.247〜0.282 (write-heavy 48 だけ 0.869) しかない。無作為に反転させると backoff が 0 の床から
   離れて滞在するためであり、これは腕の性質 (処置後の帰結) である。
   **結果として、主解析 (無条件) と副次の可否層別はほぼ同じ集合を見ることになる。**
4. **policy 1 の write-heavy 48 だけが異質である。** 割当は 1.000 なのに実現は 0.492 しかなく、
   割当前に両方向可なのは 0.246 しかない。常に反転する腕はこの regime で backoff を clamp 領域へ
   追い込む。**これは「常に反転」が同一軌跡上の反実仮想ではないことの直接の証拠**であり、
   主推定量を policy 2 に置く判断を支持する。
5. **policy 0 の「割当前に両方向可」は write-heavy 48 が最大 (0.869)** で、他は 0.25 前後である。
   段 1 の brief が既存 v1 診断から選んだ主層 (write-heavy 48) を、反実仮想の腕自身の構造データが
   独立に支持している。**ただし「他の regime には腕が届かない」とは言えない** — policy 2 では
   全 6 regime で両方向可が 0.967〜0.982 であり、処置は全 regime に届いている (裁定 R6)。
6. **主層の event 数は 583** (policy 2、write-heavy 48)。既存 v1 診断から見積もった約 850 より少ない。
   検出力の見積りはこの実数で置き直す。

## この artifact の位置づけ

**事前登録された証拠ではない。** driver が seed 引数と事前登録束縛を持つ前の版で走っており、
`counterfactual_preregistration` は `pending` のままである。本走はこの後、driver を直してから
別 directory へ 12 job を投入する。**この artifact の outcome は、本走の判定に使わない。**

## 検査器の逐語

実行したのは次のとおりである。job dir に置き、repo へは入れていない。

```python
"""生死確認だけを行う。outcome (窓 throughput・その比・median_tps・abort_rate・
directional_success) を一切表示しない。事前登録が凍結される前に結果を見ないため。"""
import json
import pathlib
import sys

p = pathlib.Path(sys.argv[1])
d = json.loads(p.read_text())
print("schema_version =", d.get("schema_version"))
print("throughput_scope =", d.get("throughput_scope"),
      "/ headline_eligible =", d.get("headline_eligible"))
print("repo_head =", d.get("repo_head"), "/ pbs_jobid =", d.get("pbs_jobid"),
      "/ host =", d.get("hostname"))
print("job_total_seconds =", d.get("job_total_seconds"))
print("counterfactual_preregistration =", d.get("counterfactual_preregistration"))
print("patch_stack =", [(x["path"], x["sha256"][:12]) for x in d.get("patch_stack", [])])
runs = d.get("trace_runs", [])
print("n trace_runs =", len(runs))
print()
print(f"{'cell':>14} {'workload':>11} {'th':>3} {'pol':>3} {'events':>7} "
      f"{'dropped':>7} {'v2':>5} {'Z1frac':>7} {'feasfrac':>8} {'realized':>8} "
      f"{'sym':>4} {'str':>4}")
for r in runs:
    ev = r.get("trace_events", [])
    n = len(ev)
    v2 = bool(ev) and all("assigned_invert" in e for e in ev)
    nan = float("nan")
    z1 = sum(e.get("assigned_invert", 0) for e in ev) / n if n and v2 else nan
    feas = sum(e.get("both_actions_feasible", 0) for e in ev) / n if n and v2 else nan
    real = sum(e.get("inversion_realized", 0) for e in ev) / n if n and v2 else nan
    s = r.get("trace_summary", {})
    print(f"{r['cell']:>14} {r['workload']:>11} {r['threads']:>3} "
          f"{str(r.get('step_policy')):>3} {n:>7} {str(s.get('dropped')):>7} "
          f"{str(v2):>5} {z1:>7.3f} {feas:>8.3f} {real:>8.3f} "
          f"{str(r.get('backoff_trace_symbol_count')):>4} "
          f"{str(r.get('backoff_trace_string_count')):>4}")
extra = set()
for r in runs:
    for e in r.get("trace_events", [])[:1]:
        extra |= set(e.keys())
print()
print("trace event の全 field:", sorted(extra))
print("(outcome 系の field は意図的に表示していない)")
```
