### [RB-1] `closed_world: true` は実際の未認証 artifact 集合と一致しない

**確信度**: high  
**must-fix / nit / backlog**: must-fix

**根拠**: 事実として、宣言は未認証 artifact を4種類だけ列挙して `closed_world: true` とする（`tools/codex_reasoning_ab.py:10233-10242`）。一方、同じ adjudication 経路には `verdict_freeze` が必須入力として存在し（`:8704-8712`）、`freeze-verdicts` が独立した frozen artifact を生成し（`:10609-10616`, `:10922-10931`）、`revealed_map` がその digest を参照する（`:10743-10757`）。それでも `verdict_freeze` は未認証一覧に無い。さらに receipt、score、snapshot oracle/after なども一覧外である。推測ではなく、少なくとも `verdict_freeze` の欠落だけで「4種類が閉集合」という読みは成立しない。

**成果物影響**: 緑の材料レポートが、一覧外の未認証 `verdict_freeze` を持ちながら `certification_scope.closed_world=true` と虚偽表示する。

**修正案**: 当面 `closed_world` を `false` にするか、対象宇宙を例えば `adjudication_intermediate_artifacts` と明示し、その場合でも `verdict_freeze` と custodian mapping を含めて全 artifact kind を列挙する。段4の確定形自体との衝突なので、実装だけでなく裁定文も訂正する。

### [RB-2] tuple key と成功時のみ cache 登録を殺す回帰 node が無い

**確信度**: high  
**must-fix / nit / backlog**: nit

**根拠**: 実装は `(resolved path, descriptor SHA, case)` を key にして canonical 一致時だけ登録している（`tools/codex_reasoning_ab.py:10033-10046`）。しかし MUT-6 の node は同じ descriptor、同じ case の成功 identity だけを共有する（`orchestrator/tests/test_codex_reasoning_ab.py:7695-7702`）ため、path-only key への退行を殺さない。mismatch を注入する別 node では、各 attempt が固有 oracle path を持つ（`:1499-1507`, `:7638-7667`）ため、「mismatch identity を cache しない」条件も観測しない。

**成果物影響**: 現行レポート値は変わらないが、tuple key または成功時限定登録が退行しても受入証拠が緑のまま残り得る。

**修正案**: 共有 path を異なる case で処理して `verify_snapshot` が2回呼ばれる node と、同一 identity の1回目を canonical mismatch、2回目を成功させ、再検証回数と forwarded run 集合を直接確認する node を追加する。

### [RB-3] module fixture は効いているが、新規 node が full manifest を2回再構築する

**確信度**: high  
**must-fix / nit / backlog**: backlog

**根拠**: `benchmark_snapshots` 自体は module scope で一度だけ構築される（`orchestrator/tests/test_codex_reasoning_ab.py:719-768`）。一方 `_full_manifest` は5 blockを毎回 supervisor に通し（`:1446-1461`）、新規2 node が別々に呼ぶ（`:7616-7618`, `:7681-7683`）。各 block は probe 1回（`tools/codex_reasoning_ab.py:7118`）と2 runの pre/post 各1回（`:6854`, `:7014`）なので、構築だけで計50回の `verify_snapshot`。その後の replay も静的には10回と9回×2で、合計約78回の追加 snapshot 観測になる。親実測の106秒増と整合する。

**成果物影響**: 材料レポート値と受理集合は変わらないが、受入全走へ重い直列 snapshot 観測が追加され、所要台帳にも新 node が未登録である。

**修正案**: 新規 wiring/pre-post node では `_full_manifest` 構築中の `verify_snapshot` を fixture の canonical oracle を返す fake に限定し、replay 側も目的に応じた deterministic spy にする。実 verifier 結合は既存 end-to-end nodeへ残す。最適化後の実測値で `acceptance_duration_ledger.json` も更新する。

## 所見外の確認

- 受理集合を広げる経路は見つからない。`valid` は引き続き `not reasons`（`tools/codex_reasoning_ab.py:9563-9567`）で、新処理は reason の追加か検査回数の増加だけである。`snapshot_checks_passed` の未設定経路は例外として既存 replay reasonになり、赤を緑にはしない。
- Python の直接参照は指定された7ファイルで尽きる。追加の動的メタ consumer は `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` と `::test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order`（`:647-719`）。記録済み被覆率は98.6%（`docs/failures.md:13263-13267`）で、4 node追加だけでは別の赤にならない。
- test file 集合を列挙する `test_plain_runner_coverage.py:44-86` は既存ファイル内の node 追加に反応しない。growth/flaky hold のメタテストも未登録 node を要求する形ではない。既知の fixture closure failure 以外に同型の exact golden failure は見つからない。
- `SCHEMA_VERSION`、packet-state、custodian mapping、verdict freeze/revealed map の `_write_frozen_json` 入力は差分外。snapshot oracle、receipt、score の canonical 比較も `tools/codex_reasoning_ab.py:10041-10072` のままである。
- ただし新規 `verify` / `aggregate` の stdout bytes は宣言追加分だけ必ず変わり、schema は2のまま。既存 frozen reportとの自動 byte 比較を行う repo 内 Python consumerは見つからない。CLI名 `verify` と `aggregate` は宣言と一致する（`:10901-10907`）。

## 総括

must-fix は `closed_world` の虚偽表示1件。  
現行コードに赤を緑へ変える受理集合拡大は見つからない。  
tuple cache の二条件は実装済みだが回帰証拠が不足している。  
新規 node は共有 snapshot fixtureを再利用しても、full manifest構築を重複させている。  
既知の serial-node closure failure以外に、node追加で赤くなる別の exact meta goldenは見つからない。  
pytestは実行せず、指定どおり静的検査のみで判断した。