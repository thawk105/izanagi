| 変異 | 殺す／候補 nodeid | 静的判定 | 根拠 |
|---|---|---|---|
| M1 | `orchestrator/tests/test_s8b_ratified_verify.py::test_public_reverify_accepts_recorded_g1_under_g2_current_while_live_refuses` | **殺せる** | current を g2 に固定し、historical resolver が g1 hash で 1 回呼ばれることまで検査する。current lookup へ戻すと正例が拒否される。 |
| M2 | `orchestrator/tests/test_s8b_ratified_verify.py::test_public_reverify_resolver_refusals_do_not_fallback_to_current[cross-env]` | **殺せる** | `expected_env_tag` が落ちた場合だけ resolver が g1 を返して再検証が成功し、`pytest.raises` が外れる。 |
| M3 | 候補: `orchestrator/tests/test_s8b_ratified_verify.py::test_public_reverify_resolver_refusals_do_not_fallback_to_current[dishonest-resolver]` | **殺せない（SURVIVE）** | resolver は same-env/wrong-hash ではなく pegasus entry を返すため、hash 検査を消しても env 検査で拒否される。外側にも同じ hash 再検査がある。 |
| M4 | `orchestrator/tests/test_s8b_ratified_verify.py::test_public_reverify_accepts_recorded_g1_under_g2_current_while_live_refuses` | **殺せる** | live wrapper が historical resolver を使うと `launch_validate` が成功し、live refusal の期待が外れる。resolver の総 call count も 2 になる。 |
| M5 | `orchestrator/tests/test_s8b_oracle_report.py::test_build_observations_accepts_recorded_g1_under_g2_current` | **殺せる** | production resolver の call count・g1 hash・`expected_env_tag`・g1 calibration object を固定。current wrapper なら g2/hash 不一致で正例が崩れる。 |
| M6 | `orchestrator/tests/test_s8b_ratified_verify.py::test_public_reverify_calibration_refusals_do_not_fallback_to_current[missing-calibration]` | **殺せる** | `AttestationError` を `None` return で握り潰すと、期待する `RatifiedFreezeError(reason=journal-state-invalid, cause=receipt-contract)` にならない。 |
| M7 | `orchestrator/tests/test_s8b_ratified_verify.py::test_run_cmd_projection_uses_passed_contract_as_structural_pin` | **殺せる（構造 pin）** | sentinel contract で構築した argv を current/base contract では拒否する。current lookup へ戻すと最初の正 assertion が落ちる。受理集合 kill ではない。 |

pytest は実行していない。以下は `fac84353` に対する静的判定である。

## 所見 R2-1 — M3 は事前登録どおりに殺せない

**根拠 (path:line):** 段4は M3 を「戻り entry の hash 再検査だけ削除」と定義している（`s4-ruling.md:96-104`）。実装の内側検査は `s8b_ratified_freeze.py:2794-2799`、外側の重複検査は同 `:2822-2826`。ところが負例は pegasus entry を返す（`test_s8b_ratified_verify.py:765-773`）ため、hash 条件を削除しても env 不一致で同じ `protocol-invalid` になる。

**成立条件:** M3 が事前登録どおり単一箇所の `contract_sha256 == recorded` 検査だけを削除する。

**成果物への影響 1 行:** M1〜M7 の静的 mutation score は **6/7** であり、dishonest resolver の hash-bound 保証をテスト済みとは記録できない。

**推奨 (must-fix):** `_resolve_historical_contract_sha256` を直接呼び、same-env だが recorded と異なる hash の `GenerationEntry` を返す resolver で拒否を固定する。M3 の正確な変異箇所も内側／外側のどちらかに確定する。

## 所見 R2-2 — C4 の主要 assertion は空 rows に対して恒真

**根拠 (path:line):** 正例は `all(status == "completed" ...)`（`test_s8b_oracle_report.py:1949`）、拒否 matrix は二つの `all(...)`（同 `:2044-2046`）だけで、rows の件数を固定しない。成果物型も単なる `dict` marker であり、production は rows をそのまま格納する（`s8b_oracle_report.py:1687-1702`）。

**成立条件:** resolver/calibration は呼ばれるが、その後の射影で対象 rows が脱落して空になる誤実装。

**成果物への影響 1 行:** C4 が observation を 0 件に落としても配線 assertion と `all([])` がすべて通り、受理・拒否の成果物を生成した証拠にならない。

**推奨 (must-fix):** 両テストで先に `len(rows) == len(observations["expected_cells"]) > 0`、可能なら manifest schedule の期待件数との完全一致を固定してから status/reason を検査する。

## 所見 R2-3 — reverify の calibration 二ケースは同一 mock error である

**根拠 (path:line):** `missing-calibration` と `calibration-hash-mismatch` は、case ID を文字列にした同じ `AttestationError` を loader から投げるだけである（`test_s8b_ratified_verify.py:800-825`）。実ファイル欠落と実 hash 不一致を組むのは C4 側だけである（`test_s8b_oracle_report.py:2005-2026`）。

**成立条件:** `_validate_journal` が任意の `AttestationError` を拒否へ翻訳できる一方、実 calibration path/hash の異常をこの public reverify 経路では踏んでいない。

**成果物への影響 1 行:** M6 は殺せるが、二つの nodeid は「実欠落」「実 hash 不一致」の public reverify 証拠としては過大表示である。

**推奨 (must-fix):** temp repo 内の calibration を削除／改変する実ケースへ置換するか、nodeid を generic `attestation-error` に改名し、具体的二境界は dependency test との合成証拠だと明示する。

## 所見 R2-4 — public 正例の production 配線 pin は有効

**根拠 (path:line):** reverify 正例は実 resolver を `wraps` し、call count、hash、env、C2/C3/result/occurrence に渡った同一 g1 object を検査する（`test_s8b_ratified_verify.py:725-751`）。C4 正例も実 resolver/loader を `wraps` し、production caller の引数を検査する（`test_s8b_oracle_report.py:1933-1954`）。CLI test も mock の中から実 `reverify_published_freeze` を実行する（同 `:1139-1183`）。

**成立条件:** 実装が patch 対象を使わなくなれば spy の call count が 0 になる。

**成果物への影響 1 行:** mock 自体を検査する恒真テストではなく、M1/M4/M5 と同一 contract object の production 配線を固定できている。

**推奨 (nit):** 修正不要。call count・引数・object identity の assertion は維持する。

## 所見 R2-5 — 既存テストの弱体化は診断 assertion 1 件

**根拠 (path:line):** `test_manifest_contract_sha256_mismatch_with_registry_is_protocol_violation` は、親版の reason 完全一致（`fac84353^:orchestrator/tests/test_s8b_oracle_report.py:1931-1935`）から `"未知の contract_sha256"` の部分一致へ緩和された（現行 `:2067-2070`）。ほかの既存 test 変更は CLI の入口差替え、必須 `contract` 引数追随、lookup seam から resolver seam への追随で、assertion の意味は維持されている。削除・skip・xfail・test 名変更はない。

**成立条件:** reason に未知 hash 以外の診断が混在しても該当 substring だけ残る。

**成果物への影響 1 行:** 拒否自体は固定されるが、診断カテゴリの純度は以前より弱い。

**推奨 (nit):** 揮発する hash/path 全文は焼き込まず、安定した reason code または正規化済み完全メッセージを固定する。現行 hash を fixture に差し込んだ形跡はない。

## 所見 R2-6 — C3 構造 pin と禁止語は裁定どおり

**根拠 (path:line):** docstring は明示的に「構造 pin であって受理正例ではない」と書く（`test_s8b_ratified_verify.py:1308-1310`）。実装は渡された contract の `clocks_per_us` / `numactl` を読む（`s8b_ratified_freeze.py:2287-2311`）。変更 5 ファイルの code・docstring・test 名に `versioned predicate dispatch` の混入はない。

**成立条件:** M7 は正当な successor では作れない clocks 差を sentinel でだけ作る。

**成果物への影響 1 行:** M7 は裁定どおり構造 pin としてのみ数えられ、世代別 run_cmd の受理正例を偽称していない。

**推奨 (nit):** 修正不要。

## 所見 R2-7 — 残る被覆の穴

**根拠 (path:line):** 段4は expansion を reverify/C4 に限定し、それ以外を 1 bit 不変とした（`s4-ruling.md:82-89`）。直接の live counterfactual は `launch_validate` にのみある（`test_s8b_ratified_verify.py:702-753`）。driver の exact type gate は production に存在する（`s8b_oracle_driver.py:737-750`）が、`ReverifiedFreeze` を実際に渡す test はない。`s8b_floor_campaign` は current lookup を維持する（`s8b_floor_campaign.py:308-322`）が、g2/current・g1/recorded の拒否 test はない。

**成立条件:** 今後、historical 経路が untouched consumer に誤配線される、または driver が `ReverifiedFreeze` を受理するよう広がる。

**成果物への影響 1 行:** `launch_validate` 以外の `s8b_floor_campaign`、loop、pipeline、`p3_s4_loop_trigger_gating`、静的 generation semantics、driver token 境界は、段4の「不変」列挙に対する専用回帰 test がない。

**推奨 (nit):** 少なくとも driver へ `ReverifiedFreeze` を渡す拒否 test を追加し、残る untouched consumer は source-level current-binding pin または小さい counterfactual matrix で固定する。既存 g1/current=g1 baseline は `test_s8b_ratified_verify.py:684-699` に残っている。

## 総括

最も重い所見は次の 3 件である。

1. **R2-1:** M3 が SURVIVEし、事前登録 7 変異を完殺できない。
2. **R2-2:** C4 の acceptance/refusal assertion が空 rows で恒真になる。
3. **R2-3:** reverify の calibration 二ケースが同じ mock error で、具体的境界を実際には踏んでいない。

M1/M2/M4/M5/M6/M7、public resolver 配線、C3 構造 pin、禁止語、g1/current=g1 baseline は静的には妥当である。しかし **現状は land 不可**。最低でも M3 を殺す same-env/wrong-hash test と、C4 rows 件数 pin が必要である。