## must-fix

なし。

## nit

- **real** — `orchestrator/tests/test_s1_direct_comparison.py:890-951`: `_capture_prepare_quarantine` は `resolve_evidence` を double にするため、`_bind_sort_oracle_contract_id` の preimage 計算自体は通らない。この入力では production の `orchestrator/campaign/s1_direct_comparison.py:898-915,928-943` は通るが、binder 内部は `"fixture-sort-source"` に置換される。ただし `test_prepare_sort_best_binds_attested_oracle_contract_into_src_token` が exact な契約 ID と返却 token を seam 上で固定しており、既存 binder の内部契約は D1630 側テストへ委ねてよい。
  成果物影響: M1〜M6 の検出力には影響しない。

- **real** — `s4-adjudication.md:26` の M3 期待は run_role 側も赤になるとしているが、`orchestrator/tests/test_s1_direct_comparison.py:711-725` は独自 prepare double から契約 ID を設定する。production の `prepare_cell` だけを None 返却へ変異させると、run_role node は緑のままで `test_prepare_sort_best_binds_attested_oracle_contract_into_src_token` の `:1473` だけが赤になる。DW-M01 の単一理由性としてはこちらの方が明瞭。
  成果物影響: M3 は確実に殺されるため影響なし。

## refuted

- **real、0 個仮説は不成立** — `orchestrator/tests/test_s1_direct_comparison.py:196-209` の freeze は 3 workload × 1 `sort_best`、つまり sort_best 3 個、全体 18 個。正例は恒真ではない。
  成果物影響: sort_best の転送欠落を実際に検出する。

- **real、zip 誤対応仮説は不成立** — 同 file `:711-729` で configuration は prepare の yield 前、kwargs はその同じ逐次 iteration の evaluate 内で追加される。`:740` が双方 18 件を要求し、失敗や retry のない入力なので `:741` の zip 順は一致する。
  成果物影響: configuration と kwargs の取り違えによる偽陰性はない。

- **real、非 PASS 後の resolve 仮説は不成立** — `orchestrator/campaign/s1_direct_comparison.py:898-913` で契約外値、契約不一致、UNAVAILABLE、REJECT、将来の未知 status はすべて `resolve_evidence` の `:928-932` より前に raise する。checker 自身が `SortSwoOracleUnavailable` を投げても同様。追加テストが直接固定するのは REJECT だけだが、現実装では他の非 PASS も非呼出。
  成果物影響: oracle 不通過後に束縛済み token が生成される経路はない。

- **real、既存 assertion 弱化仮説は不成立** — author patch 上、旧 helper は `prepared` を受け取らず、sort_best の `prepared.src_token == "fixture-source"` assertion は存在しなかった。既存 comparator テスト `orchestrator/tests/test_s1_direct_comparison.py:1418-1440` の主張は quarantine への comparator、marker、source の転送であり不変。REJECT テストは `:1507-1540` の非呼出 assertion が追加され、強化されている。
  成果物影響: 既存 sort_best 契約の検出力低下はない。

- **real、射影内では第三 pin 仮説は不成立** — `orchestrator/tests/test_s8b_oracle_manifest.py:89` の materializer sha は literal 1 個、spec sha は `:64` の literalを `:1166,1173-1174` で変数参照、schedule sha は `:61` と raw 内 `:100` の意図された2箇所だけ。既知 F-P1 は除外した。`s6-adjudication.md` も spec sha の repo-wide 値検索を1件と記録している。指定射影外は独立再検索していない。
  成果物影響: F-P1 以外に追随漏れとして直す pin は確認されない。

- **real、揮発値混入仮説は不成立** — 新規期待値の path は `tmp_path` から動的に組み立て、契約 ID、fixture token、ccbench pin、sha は固定契約または golden。時刻や実 worktree 絶対パスは焼き込まれていない。
  成果物影響: 実行場所や時刻による不安定化はない。

## 変異対応表

| 変異 | 殺す node と assertion | 新規検出力 |
|---|---|---|
| M1 | `test_prepare_sort_best_binds_attested_oracle_contract_into_src_token` — `test_s1_direct_comparison.py:1459` の `resolve_calls == []`。`resolve()` に戻すと直ちに赤。 | 新規 |
| M2 | 同 node — `:1467-1471` の kwargs exact 一致。別文字列なら `sort_oracle_contract_id` が不一致。 | 新規 |
| M3 | 同 node — `:1473` の `prepared.sort_oracle_contract_id == ORACLE_CONTRACT_ID`。run_role node は production prepare を使わないため赤にならない。 | 新規、単一 node |
| M4 | `test_run_role_forwards_sort_contract_only_when_prepared_cell_has_one` — `:743` の exact 値参照。転送を落とすと key 欠落で赤。 | 新規 |
| M5 | 同 node — 非 sort_best 15 cell で `:745` の key 非存在 assertion が赤。さらに既存 `test_run_role_available_perf_keeps_evaluate_call_shape_exact` の `:693-698` も kwargs 集合の増加で赤。 | 新規検出力ではない |
| M6 | `test_prepare_non_sort_cells_keep_unbound_resolve_path` — `:1105-1108` の fail-double が赤。さらに既存 `test_prepare_cell_passes_site_cxx_to_source_digest` の `:1142-1144` も `resolve` 呼出が消えるため赤。 | 新規検出力ではない |

## 総括

M1〜M6 はすべて殺せる。M1〜M4 は新規検出力、M5〜M6 は既存テストでも落ちる。  
M3 は prepare 側だけが production 変異を殺し、run_role 側とは理由が分離されている。  
freeze の sort_best は3個で、zip の対応も逐次実行により安定している。  
既知 F-P1〜F-P4 を除く must-fix はない。pytest は実走していない。