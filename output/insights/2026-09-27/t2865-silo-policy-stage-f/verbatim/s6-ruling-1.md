# 段 6 裁定 1 — [T-2865] 段階 F (2026-09-27)

入力: codex/s6-review-A.md (NO-GO、must-fix 2・should-fix 2)、codex/s6-review-B.md (NO-GO、should-fix 3・nit 1)、親の点検。対象 = wave `6b4100077`。

| 所見 | 判定 | 採否 | 根拠 (親の確認) |
|---|---|---|---|
| A1 依存 prefix を `CMAKE_PREFIX_PATH` から明示引数に写す (区切り違い) | real | 採用 (fix F1) | `p3_s4_loop.py` の main は `dependency_prefix` を明示で渡さず (既定 "")、job body が export した環境変数を build 側が読む。方策 driver だけが写していた。p3_s4_loop と同じく明示引数を渡さない |
| A2 stock の `certified-stock` が src_token を確かめない | real | 採用 (F2) | 既存 `_run_stock_control_resolved` は variant と `BUILD_START.src_token == STOCK` を確かめる。同じ判定にし、外れは `non-stock-source` |
| A3 stock 不成立でも rc=0 | real | 採用 (F3) | `--stock-baseline` は `certified-stock` 以外で rc=1。pair も stock が `certified-stock` 以外なら rc=1 (p3_s4_loop の pair と同じ)。候補の gate 拒否・非直列化判定は正当な結果で rc を変えない |
| A4 実 source 判定 test が `g++-13` 固定で計算ノードでは skip | real | 採用 (F4) | runbook: 計算ノードは `g++-12`。`find_compiler()` (g++-13 → g++-12 → g++) で選ぶ |
| B1 候補が `stopped-before` (予算切れ) でも pair が stock を測り rc=0 | real | 採用 (F5) | 候補 attempt の無い pair は stock を起動せず rc≠0 |
| B2 README の準備手順が `p3_s4_loop.PIN` への checkout を指示 | real | 採用 (親 docs) | 方策 mode は方策軸の pin に合わせると明記 |
| B3 README の方策用 qsub が断片 | real | 採用 (親 docs) | 完全な pair の qsub 例を text fence で置く (bash fence はちょうど 1 本という既存 test の制約) |
| B4 job body の T-2849・B-5 env の重複走査 | nit | 不採用 | 受理集合・値を変えない |
| 親: 計測中の log を捨てる (`log=lambda *_: None`) | real | 採用 (F6) | stdout の 1 行 JSON 契約は守りつつ、log は stderr へ出す (job の stderr に失敗時の診断を残す) |

## fix の変異の事前登録 (fix 前)

| id | 壊す箇所 | 期待して落ちる test |
|---|---|---|
| M-F9 | stock の src_token 照合を外す (certified なら certified-stock) | 非 stock の src_token を持つ WAL で `non-stock-source` を期待する test |
| M-F10 | `--stock-baseline` の rc を常に 0 にする | stock 不成立で rc=1 を期待する test |
| M-F11 | pair で候補が `stopped-before` でも stock を評価する | 候補 ran=False で stock が呼ばれないことを期待する test |
| M-F12 | 依存 prefix を `CMAKE_PREFIX_PATH` から明示引数に写す | `run_campaign` に `dependency_prefix` が渡らないことを期待する test |

fix は単位 A (driver・test) の 1 本。docs は親。
