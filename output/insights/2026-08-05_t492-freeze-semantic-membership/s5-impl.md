実装 1〜5 を完了しました。コードとテスト 3 ファイルだけを変更し、docs・`output/`・既存期待値には触れていません。実装済み・未実走です。

## 現行挙動と変更差分

変更前:

- 生成層は述語が文字列で main/remeasure が完全一致すれば、32 正準集合外でも受理し得た。
- `_validate_schema()` は workload/entry の key だけを検査し、`system_gate` / `ident_all` の意味 membership は検査しなかった。
- 片側 drift、文字列型不正、source/generator hash 不一致、pairing・再構成不一致は拒否していた。

変更後:

- 生成・schema とも、3 workload × 2 configuration の6値を `trigger_gate_binding.is_canonical_predicate()` で検査する。
- 非正準値または record 非 Mapping は `FreezeError` で拒否する。
- 外周空白を含む既存権威の受理規則はそのまま。正規化や別表記は追加していない。
- 従来の拒否条件は削除しておらず、受理集合は canonical membership との積集合に狭まるだけ。
- `build_document()` 本体の AST は HEAD と同一で、dict 構築、field、順序、source 配列構成には変更なし。generator self-hash の既存規則も変更していないため、凍結成果物は再生成していない。

## 編集ファイル

- [s1_known_axes_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:26)
  - `trigger_gate_binding` import
  - `_require_canonical_trigger_predicate()` 追加
  - `_trigger_entries()` の system/ident 取得直後に検査追加
  - `_validate_schema()` に6値の record/membership 検査追加
- [test_s1_known_axes_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s1_known_axes_freeze.py:37)
  - mock 用 helper 3個
  - 新規 test 7本
- [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s8b_oracle_driver.py:2694)
  - 既存 G7 node の historical known-generator replay と限定 `ROOT` patch

## 新規 test 7本

- `test_current_six_frozen_trigger_predicates_pass_semantic_membership`
  - 現行6値が過剰拒否されないことを固定。
  - helper が恒偽化されると `_validate_schema()` が `FreezeError` になり赤くなる。

- `test_trigger_entries_rejects_coordinated_noncanonical_system_gate`
  - 全3 workload の main/remeasure 連動非正準 system gate を生成層で拒否する。
  - system_gate の helper call を消すと例外が出ず赤くなる。

- `test_trigger_entries_rejects_coordinated_noncanonical_ident_all`
  - 全3 workload の連動非正準 ident_all を生成層で拒否する。
  - ident_all の helper call を消すと例外が出ず赤くなる。

- `test_validate_schema_rejects_noncanonical_system_gate`
  - 各 workload の doc 内 system gate を1値ずつ改竄し、schema 単体で拒否する。
  - schema の6値走査または system_gate branch を消すと例外が出ず赤くなる。

- `test_validate_schema_rejects_noncanonical_ident_all`
  - 各 workload の doc 内 ident_all を1値ずつ改竄し、schema 単体で拒否する。
  - schema 走査または ident_all branch を消すと例外が出ず赤くなる。

- `test_generate_rejects_noncanonical_predicate_before_writing`
  - 完全 mock 下の公開 `generate()` が拒否し、出力ファイルを作らないことを固定。
  - producer が `_trigger_entries()` を迂回する、または書込み後に拒否するようになると赤くなる。

- `test_verify_document_rejects_noncanonical_predicate_before_rebuild`
  - `verify_document()` が schema 段階で正確な診断を返し、再構成へ進まないことを固定。
  - schema 配線を消すと診断完全一致または `build_document` sentinel が赤くなる。

既存 G7 は nodeidを変更していません。known generator の recorded bytes を Git 履歴から replayし、その digestを事前 assertしたうえで、`gate_check()` 周囲だけ `ROOT` を patchしています。holdout tamper、refusal 4件、known source mismatch 1件の期待値は変更していません。

## mock.patch と注入 seam

使用箇所:

- `_trigger_entries()` 負例: `_campaign_file`、`_load_json`、`s8a_trigger_sweep._genome`、`_source`、`_module_source`
- 公開 `generate()` 負例: 上記に加えて `_p2_entry`、`_fixed_gates_from_recon`、`_stock_common`
- verifier wiring: `build_document` を未到達 sentinel 化
- G7: `driver.s1_known_axes_freeze.ROOT`

`_trigger_entries()` と `generate()` には provenance/source resolver の正規注入 seam がありません。G7 の `source_resolver` は source records にしか適用されず、generator hash は先に module-global `ROOT / SCRIPT_REL` から読むため利用できません。このため `ROOT` patchを `gate_check()` の呼出し範囲だけに限定しました。

## 静的な波及確認

- `s1_measurement_freeze`: `known_axes.verify_document()` を直接呼ぶため新 schema gateが届く。legacy generator driftも引き続き拒否要因。
- `s8b_holdout_freeze`: known docを直接コピーし `_validate_schema()` を呼ばない。単体意味検査はscope外のまま。
- `s8b_oracle_driver`: legacy verifyとT-080 static adapterの `_verify_known_schema()` の双方に届く。never-issued G7のみfixture是正。
- `s1_direct_comparison`: 既存の独立 canonical sink gateを維持。新検査により upstreamで早期拒否され得る。
- `p3_s4_loop`: 同じ権威helperと既存 canonicalizationを使用するが、変更なし。
- `conftest`: 新規7本は frozen JSONまたは完全mockのみ。共有 ccbench reader/writerではないため serial allowlist追加不要。
- meta-test: `test_s1_known_axes_freeze.py` の素 runnerが新規testを自動発見し、`tmp_path`も注入する。README allowlistとreal-repo独立goldenは変更不要。

親docs未landによる新規testの想定赤はありません。親が source pin対象の既存 `RECON_REL`、`PHASE_MAIN_REL`、`SORT_INSIGHT_REL` を編集した場合のみ、legacy source hash検査の赤が別途増え得ます。

scope外と裁定された holdout意味検査、proof chainへの権威追加、`selection_rules` 文言、refreeze世代移行、name→mask束縛は実装していません。

## 静的検査

- `python3 -m py_compile`：変更3ファイル成功
- import循環・mock対象の実在：実 importと `hasattr` で確認
- `build_document()`：HEADとのAST同一を確認
- `git diff --check`：成功
- 現行6値：すべて canonicalかつstrip不要、非正準controlは拒否
- 凍結5成果物：着手前SHA-256と一致、`output/`差分なし
- pytest、`generate()`、`git add`、`git commit`：未実行

親が実測すべき中心nodeは、新規7本、変更済みG7、ならびに `test_reflux_ir.py::test_frozen_gate_predicates_match_six_records_with_three_distinct_masks`、T-080 schema、measurement、direct-comparison、p3_s4_loop、plain-runner/real-repo meta-testです。

## 総括

実装の骨子: canonical helperを生成層とschema層の二箇所へ配置し、現行出力を変えず受理集合だけを狭めました。

検査状態: 実装済み・未実走。py_compile、import/name解決、AST、diff、凍結SHAのみ静的確認済みです。

親の実測: 新規7 node＋G7を最優先に、freeze consumer群、T-080 active/legacy、allowlist/meta-testを計算ノードで実走してください。