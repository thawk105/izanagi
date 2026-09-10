## 所見 1 — admission の rule/stage が critic 射影で消える

**所見:** P3 producer は `rule_id` と `admission_stage` を WAL digest に追加するが、critic は `sort-swo-oracle` の `rule_id` を空文字へ落とし、`admission_stage` はデータ型にも持たない。新 reason ID 自体の閉集合追随は済んでいるが、producer 出力全体の consumer 追随は未完である。

**根拠 (file:line):** [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/p3_s4_loop.py:472)、[digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/critic/digest.py:291)、[digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/critic/digest.py:901)、[digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/critic/digest.py:968)。新 critic test は reason 集合だけを見る。[test_critic.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_critic.py:1584)

**成果物影響 1 行:** certified 選択と受理集合は変わらず raw WAL には残るが、材料レポートでは grammar rule/stage の参照が失われる。

**must-fix か nit か:** must-fix。

**推奨:** sort IR の `rule_id` を exact allowlist で保持し、`admission_stage` も閉じた射影として P3→WAL→critic の既存 consumer test で固定するか、producer から未消費 field を出さない。

## 所見 2 — ledger 未更新だけでは赤になる検査がない

**所見:** この wave は現在の ledger にない nodeid を少なくとも 26 件作るが、`test_t1574_changed_suite_ledger_node_delta_is_exact` は current collection を読まず、未更新 ledger 自身を旧 count/digest と比較する。そのため、ledger 未更新だけを原因として赤になる exact-set 検査は **0 本**である。

内訳は `test_critic.py` 4 node、`test_p3_s4_loop.py` 1 node、`test_p3_s4_loop_sort.py` 2 node、`test_sort_swo_oracle.py` 19 node。ledger は旧名も保持している。

**根拠 (file:line):** [test_update_acceptance_duration_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_update_acceptance_duration_ledger.py:329) は ledger だけを読み、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_update_acceptance_duration_ledger.py:397) で ledger key を hash する。旧名は [acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/acceptance_duration_ledger.json:10515) と [同 ledger](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/acceptance_duration_ledger.json:6851) に残る。real collection 検査も exact ではなく 90% 閾値である。[test_acceptance_schedule_order.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_acceptance_schedule_order.py:660)

oracle environment registry と独立 golden は新 batch node、件数 29 へ双方追随済みである。[conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/conftest.py:580)、[test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_real_repo_serialization.py:385)

**成果物影響 1 行:** certified 値と受理集合は変わらないが、acceptance duration ledger は新 node 参照を欠き、旧参照を残したまま scheduling に使われる。

**must-fix か nit か:** must-fix。

**推奨:** 実測 JUnit 取得後に ledger を再生成し、同時に suite count/digest を current collection へ更新する。値の合成はしない。

## 所見 3 — R9 の M10 指定 node は機構固有 sink になっていない

**所見:** R9 の予定名は全て実在する。代替 sink を含めれば identity-only の変異も 0 件である。ただし M10 に指定された node は admission を一度も呼ばず、15 件が renderer 集合に含まれることしか検査しない。M10 を実際に落とすのは別 node の全79 roundtrip である。

| 変異 | 実在する機構固有 node | 判定 |
|---|---|---|
| M1 | `test_public_oracle_rejects_non_ir_before_environment[duplicate-field]` | 有効 |
| M2 | 同 `[generic-lambda]` | 有効 |
| M3 | `test_sort_ir_domain_roundtrips_all_79_values` | 有効 |
| M4 | `test_trusted_evaluator_matches_real_tu_for_all_79_ir_values` | 有効、未実走 |
| M5 | 同 batch、`test_contract_digest_binds_sort_ir_grammar_and_pointer_mapping` | 有効、batch 未実走 |
| M6 | 同 batch | 有効、未実走 |
| M7 | `test_compiled_relation_mismatch_is_unavailable_not_pass` | 有効 |
| M8 | `test_contract_digest_binds_sort_ir_grammar_and_pointer_mapping` | 有効 |
| M9 | `test_materialized_hole_is_canonical_form` | 有効 |
| M10 | 指定 subset node は無効。全79 roundtrip が実効 sink | R9 の帰属と不一致 |

**根拠 (file:line):** subset node は集合比較だけである。[test_sort_swo_oracle.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:295)、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:310)。負例、mismatch、batch、contract node は [同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:347)、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:423)、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:487)、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:2027)。M9 は [test_p3_s4_loop_sort.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_p3_s4_loop_sort.py:231)。

contract ID pin であり kill 根拠から除外すべき node は次の10件である。

- `test_sort_swo_oracle.py::test_contract_manifest_hashes_and_literal_are_exact_snapshot`
- `test_critic.py::test_invalid_oracle_finding_renders_only_fixed_anomaly_code`
- `test_critic.py::test_sort_swo_oracle_contract_and_receipt_roundtrip_through_consumer_limit`
- `test_critic.py::test_current_v4_and_legacy_v3_v2_loaders_are_generation_exact`
- `test_critic.py::test_sort_swo_non_axiom_kinds_have_dedicated_fixed_rendering` の current 6展開: `structure`、`compile`、`timeout`、`execution`、`protocol`、`nondeterministic`

**成果物影響 1 行:** 全79 roundtrip を走らせれば過剰拒否は検知できるが、現状の変異台帳は M10 の落ち先を誤って帰属する。

**must-fix か nit か:** must-fix。

**推奨:** M10 指定 node で権威15件を実際に admission し、各結果が受理されることを固定する。上記 identity pin は全変異の kill 集計から引く。

## 所見 4 — R10 の現行値は正しいが、検査は独立していない

**所見:** production と receipt docstring は旧非保証を削除し、trusted matrix、real TU byte exact、非動的 gate を明記しており、現実装は R10 に適合する。しかし検査は producer 定数を期待値へ再利用し、正の substring しか確認しない。旧 `reported-relation...does-not-guarantee` を新文言へ追記しても、機構固有検査は緑のままで、落ちるのは contract ID pin だけになりうる。

**根拠 (file:line):** production は [sort_swo_oracle.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/sort_swo_oracle.py:91)、receipt 文言は [s8b_sort_swo_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/campaign/s8b_sort_swo_receipt.py:8)。oracle test は正の包含と producer 値からの自己計算である。[test_sort_swo_oracle.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:1996)。receipt test も producer 定数を fixture と期待値の双方へ入れる。[test_s8b_sort_swo_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_s8b_sort_swo_receipt.py:29)

**成果物影響 1 行:** 受理集合と certified 値は変わらないが、portable receipt と材料レポートが新保証と旧非保証を同時に名乗る矛盾した参照を許す。

**must-fix か nit か:** must-fix。

**推奨:** 既存 R10 test へ保証境界の独立 exact bytes、または旧非保証 token の不在を固定する。

## 所見 5 — R6 の compile count assert は恒真

**所見:** batch node は79値、2 corpus、3 order、18×18セルを実際に走査する。一方 `compile_count = 1` の直後に `assert compile_count == 1` としており、この部分だけは compile seam を何も観測しない恒真 assertion である。

**根拠 (file:line):** [test_sort_swo_oracle.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:505)、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:511)、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2145-sort-oracle-ir/orchestrator/tests/test_sort_swo_oracle.py:515)

**成果物影響 1 行:** nit。現コードは静的には単一 batch TU と153,576セルを満たし、成果物の値・受理集合・参照は変わらない。

**must-fix か nit か:** nit。

**推奨:** 定数 assertion を削るか、同じ node 内で実際の compile 呼出し回数を観測する。

## 総括

(1) must-fix は4件: critic の rule/stage 脱落、ledger exact meta の不発、R9 M10 の誤帰属、R10 検査の自己参照。R1、R2、R4〜R8、R10 の現 production は静的には裁定どおり。  
(2) nit は1件。禁止4ファイル、`CANDIDATES`、`docs/` の差分は0。HEAD は `82a259c0a` のまま、14ファイルが staged かつ未commitである。  
(3) 親の実走必須: batch 79値 node、全 sort oracle/P3/S1/receipt/critic focus、oracle registry meta、`test_t1574_changed_suite_ledger_node_delta_is_exact`。pytest 実走は依然0 nodeで、結果は未知。