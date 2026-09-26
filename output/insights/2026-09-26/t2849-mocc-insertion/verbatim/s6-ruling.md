# 段 6 裁定 — レビュー 2 本の所見 (2026-09-26、親)

入力: codex/review-A.md (正しさ・整合・silo 不変、GO・must-fix 0)、codex/review-B.md (実効性・過剰・削除、NO-GO・must-fix 2)。対象 = 統合 commit `955bfed71`。

| # | 所見 | 判定 | 裁定 |
|---|---|---|---|
| A-s1 | T7 は `make_define_request` の単体だけで、`p3_s4_loop._require_condition_gate` が genome の protocol を渡すことを検査しない (`protocol=genome.protocol` が落ちても T7 は緑) | real・fix 1 で採用 | `_require_condition_gate` を mocc の stock / 候補 genome で呼んだとき、意味検査へ渡る request が mocc の owner `cc/mocc/transaction.cc`・target `ycsb_mocc.exe` になることを確かめる試験を足す。意味検査の機構は stub しない。request を観測するための実物委譲の wrapper か、request 構築の後で止める既存の seam は可。放置時: 呼出しの protocol が落ちると MOCC 候補が silo の TU で検査され、値 <v> の実効が未確認のまま台帳に載る |
| A-s2 | T1 の一部は新実装同士の比較 | refuted (既存で足りる) | silo 既定の search_config は既存の loop golden (`test_p3_s4_loop.py`) と既存の job contract の exact argv 試験が固定している。追加しない |
| A-nit | `setup.replace(...)` の無言 no-op | 既存 T8 で検出 | 変更なし |
| B-m1 | M4 (呼出し位置を B-5 版へ戻す) は T5 (関数の直接呼出し) では落ちない | real・変異の再照準 | M4 を harness の `_stock_established` 関数本体で protocol を捨てる変異 (`_genome(-1, protocol)` → `_genome(-1)`) に移す。呼出し位置の変異は登録しない |
| B-m2 | 複数の変異が複数の試験を落とす (M1〜M3・M7・M9) | real・登録の形で解消 | 変異は「1 つの意味変更」を単位とし、期待 node は probe で観測した完全集合を登録する (DW-M08)。試験の分割はしない。M9 は job body の未設定分岐だけを変異させる |
| B-d1 | `calibrated_perf` の protocol 引数と 2 値検査は値を変えない | 採用 (fix 1 で削除) | `calibrated_perf(workload)` の signature は変更前に戻し、MOCC 出典の comment だけ残す。巡 tool は `calibrated_perf(workload)` を呼ぶ |
| B-d2 | harness `_header` の MOCC `perf_config` 再構築は同値の上書き | 採用 (fix 1 で削除) | `protocol` の追加だけ残す |
| B-d3 | `make_define_request` の「mocc なら BACKOFF_FIXED 以外を拒否」 | 不採用 (残す) | mocc の spec は BACKOFF_FIXED しか持たないので、他 macro に mocc を渡すと silo の spec で黙って通る。拒否は受理集合を広げない向きで、1 行 |
| B-d4 | `h.get("protocol", "silo")` の散在・spec 選択の重複 | 不採用 (nit) | 成果物の値を変えない。fix の差分を増やさない |

fix 1 の範囲: A-s1 の試験 1 本 (必要なら既存 test file 内)、B-d1、B-d2。既存 test の期待値は変えない。
