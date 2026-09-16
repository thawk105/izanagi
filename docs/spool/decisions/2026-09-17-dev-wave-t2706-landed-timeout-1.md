---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2706-landed-timeout
seq: 1
---

## {{D:landed-checker-command-timeout-from-measurement}}. 着地判定器の per-command 上限は実測分布の最大への倍率で有界に決め、受理述語には触れない

**決定:** `tools/check_branch_landed.py` の `COMMAND_TIMEOUT_SECONDS` (各 git 子プロセスの
`subprocess.run(timeout=min(上限, 残り全体予算))`) を 5.0 から **45.0** にする。値は次の事前登録した規則で決めた。

1. 母集合 = `docs/unreachable-object-ledger.md` の到達不能 commit 30 件。判定器の `Git.run` を包んで上限だけを 300 秒へ
   持ち上げ、Git 操作別の完了時間を記録する (2,935 本、打切り 0)。
2. 全 command の最大 (26.87 秒、`log --full-history --max-count=1 --find-object=<oid> <main>`) × 1.5 = 40.3 を格子
   {10, 15, 20, 30, 45, 60} へ切り上げる → 45。倍率 1.5 は同じ操作が負荷で 2 倍動く観測から置いた判断値。
3. 重い 3 操作の反復点検 (path log 69 本 = 最大 35.94 秒、find-object 3 本 = 最大 20.76、cherry 3 本 = 最大 6.87) の
   最大が候補を超えなければ据え置く (超えれば次の格子)。35.94 ≤ 45。
4. 有界 = `0 < 上限 ≤ DEFAULT_TIMEOUT_SECONDS (60)`。60 は `min(上限, 残り)` で上限が無意味になるので採らない。

**決定 2:** 受理述語 (D922 項 2・4) は不変で、本決定はそれに触れない。timeout は証拠ではない: 決定的探索の打切りは
`AssessmentError(outcome="truncated")` → `indeterminate` にしか落ちず、`landed` は exact tree state か fold receipt
の一致から、`not-landed` は closed-world の負証拠 (pure-add + 同 path 候補ゼロ + any-path 探索の不一致 + 完全な
history scan + 終端 ref 一致) からだけ出る。上限が変えるのは「時間内に証拠を集め切れる入力の集合」であり、証拠を
受理する条件ではない。観測層 (`cherry`、ledger、verbatim) の timeout は捕捉されて続行するので、観測層の待ちが延びて
終端 ref 確認が予算切れになる逆向きも理論上ある。実測は insight に置く。

**決定 3:** 正例・負例を test で対にする。正例 = 定数が有界で `Git.run` の既定引数と同値、および同じ偽 git 経路で
遅延させなければ証拠どおり `landed` / `not-landed` を返す。負例 = PATH 先頭の偽 git が実 `subprocess.TimeoutExpired`
を起こしたとき `assessment-timeout` / `truncated` になり、proof の path log と any-path の find-object のどちらを
遅延させても `indeterminate` で `negative_paths` は空。

**理由:**

- 旧 5 秒は本 repo (main 11,246 commit、packed 176,575 object) の `log -- <path>` の p95 (9.1 秒) にも
  `--find-object` の最小値 (13.2 秒) にも届かず、30 件すべてが `assessment-timeout` で、負判定は構造的に出せなかった
  (entry 1552 の起票)。
- 上限の役割は「1 本の git が固まったとき全体予算を待たずに返す」だけで verdict の質に寄与しないので、実測分布の
  裾を余裕で覆う値にしてよい。上限 30 以上で観測 2,935 本の超過は 0 だが、反復点検で path log が 35.9 秒に達したため
  30 は採らない。
- 判定器既定の全体予算 60 秒では 30 件のうち 16 件しか完走せず (確定 4)、残りは unit 数 × path log の合計が予算を
  超える律速で、上限を上げても変わらない。全体予算・rescue の内部予算 8 秒の見直しは名指しの変更の外 (D2104) で、
  次の一手に置く。

**却下した選択肢:**

- CLI に `--command-timeout` を足す — 予算の配分責任が呼び手へ移るだけで、既定値の根拠は依然要る。
- 上限 = 全体予算 (60) — `min` で per-command 上限が消え、固まった git を全体予算まで待つ。
- `log --full-history` を `--first-parent` 等で速くする — 探索方式の変更は受理集合に触れる。
- 無制限 retry・timeout 管理基盤 — 依頼で明示的に除外。
