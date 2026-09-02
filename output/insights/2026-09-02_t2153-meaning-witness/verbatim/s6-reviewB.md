## 所見

1. **重大度: MUST-FIX**

   **問題:** `screening_driver` は裁定が数えた「成果物が縮む第4 driver」ではない。8 macro は裸マクロであるため、`Genome.cmake_defines()` が生成する `-DCCBENCH_<MACRO>=...` は `CMAKE_CXX_FLAGS` route と一致せず、admission 作成前に拒否される。さらに gate 結果は `evaluate_candidate()` で保存されない。

   **根拠:** `orchestrator/campaign/model.py:61-63`、`orchestrator/campaign/screening_driver.py:81-104,108-138,205-218,542-548`、`orchestrator/tests/test_screening_driver.py:201-211`、`s4-adjudication.md:14`。

   **成果物影響:** S3・S5・T152 の材料 JSON は縮むが、screening の certified 選択・材料レポート・台帳には元から対応 admission が残らないため、値・受理集合・参照の縮小は0件。

   **是正案:** 裸マクロを generic pipeline へ通してはならないため、裁定を「実効 driver は3面」に訂正し、screening の無効な配線と対応テストを外す。残すなら、別裁定で証拠の永続化と安全な実 build route を設計する。

2. **重大度: MUST-FIX**

   **問題:** `test_condition_meaning_gate.py` は51 nodeから71 nodeへ、正確に20 node増えたが、所要時間台帳には旧51 nodeしかない。段7での追随は必要だが、裁定の「node key pin 更新」という説明は不正確で、この suite は exact suite pinにも add-only凍結prefixにも含まれない。

   **根拠:** `orchestrator/tests/test_condition_meaning_gate.py:583-807`、`orchestrator/tests/acceptance_duration_ledger.json:639-689,19523`、`orchestrator/tests/test_update_acceptance_duration_ledger.py:364-404`、`tools/update_acceptance_duration_ledger.py:21-30`、`s4-adjudication.md:17`。

   **成果物影響:** certified 選択と材料レポートは不変だが、所要時間台帳は20 nodeの参照と実測durationを欠き、受入スケジューラでは全20件が未知コストになる。

   **是正案:** 親の受入実測後、20 nodeを実測値でadd-only追加する。現行契約では suite件数/hash pinの更新は不要であり、裁定文も「台帳entry追随」と訂正する。

## 受入で赤になる予測

- 条件付き候補は `orchestrator/tests/test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`。20 nodeが未登録なので、変更前の被覆余裕が18 node相当未満なら90%を割る。静的検査だけでは現在の全collection件数を確定できないため、赤を断定しない。
- `orchestrator/tests/test_update_acceptance_duration_ledger.py::test_t1574_changed_suite_ledger_node_delta_is_exact` は赤にならない見込み。exact pin対象8 suiteに `test_condition_meaning_gate.py` は含まれない。
- それ以外は無し。`MEANING_SUPPORTED_MACROS`、proof kind、reason code、`__all__` のrepo内独立reader、生成箇所pin、変更ファイルのbytes pinは見つからなかった。`test_ccbench_spawn_sites.py` は親実測で18 passed。
- AI provenanceは未commitのため未判定。commit後の監査が必要であり、緑とは報告しない。

## 4 driver の成果物影響

- `s3_lock_coverage`: `IZANAGI_BREAK_LOCK_COVERAGE`、`IZANAGI_BREAK_EARLY_UNLOCK`を各1/0で要求。各 admission の未確立一覧はそれぞれ`("<macro>",)`から`()`へ変わり、`s3_lock_coverage.json`内のmeaning record、admission ID、参照IDが変わる。
- `s5_permutation_coverage`: `IZANAGI_BREAK_PERMUTATION`、`IZANAGI_BREAK_PERMUTATION_SWAP`を各1/0で要求。各未確立一覧は単要素から空へ変わり、`s5_permutation_coverage.json`の同じ参照群が変わる。
- `t152_write_intent_coverage`: `ERASE`、`FORGE`、`OPSWAP`、`PTRSWAP`の4 macroを各1/0で要求。4個の個別admissionがそれぞれ単要素から空へ変わり、characterization JSONの`condition_gates`が更新される。
- `screening_driver`: genomeとの積集合として8 macroすべてを要求可能だが、実経路では裸マクロのbuild route不一致でadmission前に拒否され、結果も保存されない。したがって実成果物の未確立一覧は縮まらない。

同一macroが、受理済みの永続成果物間でgreenとunestablishedに分裂する面は見つからなかった。screeningは反対側の成果物を発行せず、単に到達不能である。なおmodule内CLIを含めるとproduction call expressionは22件であり、裁定の21件は外部driverだけを数えた値である。

## 編集面の逸脱

無し。差分は裁定許可のproduction 5 + test 4の9ファイルだけである。

本文bytes期待値、witness kind分類、新語彙field、新台帳、S1、他driver、patch、CCBench sourceの編集はない。既存assertの削除・緩和、skip、xfail追加もない。8件の選定と、動かさない13件の技術的理由は実patchと一致する。

## 総括

BLOCKERは0件、MUST-FIXは2件。  
3個の専用driverでは8 macroすべての材料成果物が実際に縮む。  
screeningを第4の縮小面とした裁定は実コードと不一致である。  
20 test nodeの台帳追随と裁定訂正前には、この9ファイルのままlandすべきではない。