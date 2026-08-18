# 段 1 brief — [T-1352] C07 consumer `s8c_result_judge.py` 新設

## scope

1. 新規 `orchestrator/campaign/s8c_result_judge.py`。entrypoint は契約 C07 が凍結済みの
   `verify_floor_bytes` / `judge` / `publish_result_table` ちょうど 3 つ。
2. `orchestrator/campaign/s8c_preregistration_evidence.py` へ `_evaluate_c07` を実装。
3. `orchestrator/tests/test_s8c_preregistration_predicates.py` へ nc_c07 fixture と
   `_negative_control_case` 分岐、および `_evaluate_c07` を直接叩く専用テスト。
4. docs は親所有。台帳は `docs/spool/` fragment。

## 確定済みユーザー裁定 (逐語の所在)

- [T-1336] 床値比較を撤去、反復単位の対比とその分散へ置換 + 順位と性能主張の二層化
  (`rulings-inbox/2026-08-18-rulings-full7-15rulings.md`)。
- 判定の正本は `docs/phase3-8b-descriptor-design.md` §10.1 / §10.3 (§6 の条件 3 と結論行を上書き)。
  judge が消費してよい主量は **対差の有限な平均と有限な標本 SD だけ** (SD の分母は n-1)。
  3 表 = 生値順位表 (`descriptive_only`) / 公式性能表 (三値 `official_status`) / 独立した選択評価表。
- 3 条件 = on/off 予測差・swapped 追従・反復単位の対比。結論行は条件ではなく連言。
- full8 「条件を迂回する機構を作らない」「EVIDENCE_UNDEFINED 7 件の証拠契約を定義する」。

## 親が実測した新事実 (段 4 で再裁定する)

`_MACHINE_EVALUATORS` への C07 登録と「契約 JSON の `machine_checkable` を反転しない」は
**両立しない**。worktree で実編集・即時復元して実測 (2026-08-18 18:03 JST、request 921751.nqsv)。
登録 + `NEGATIVE_CONTROL_CASES` 追加だけで 4 node が赤:

- `test_machine_checkable_contract_and_evaluator_registry_are_bijective`
- `test_satisfiable_predicate_requires_negative_control`
- `test_current_repository_gap_reason_snapshot_requires_cross_wave_review`
- `test_noop_and_token_only_fixtures_never_satisfy[nc_c07_floor_or_result_cell_removed-C07]`

反転側も不可能である。契約 C07 の `reachable_from` は `accept_trial` を含むが、この名前は
repo に実在せず (C09 は既に `assert_trial_registry_acceptance` へ改名済み、
`test_machine_contract_rejects_prewave_accept_trial_name` が pin)、反転すると
`test_machine_contract_function_names_exist_and_checked_set_is_exact` も落ちる。
さらに g7 (`evidence_contract_sha256`) が契約 bytes を pin しており反転は g8 を要求する。
**よって「反転しない」という指示は正しく、譲るのは「登録」の側**である。

## provisional 裁定 (攻撃対象)

- **(P1)** `_evaluate_c07` は実装するが `_MACHINE_EVALUATORS` へ登録しない。`NEGATIVE_CONTROL_CASES`
  dict へも追加しない。純増検出力は「nc_c07 fixture を `_evaluate_c07` へ直接与えて
  UNSATISFIED を得る専用テスト」で確保する。staged registry のような**別経路は新設しない**
  (条件を迂回する機構の新設に当たる)。活性化 (登録 + dict 追加 + 契約反転 + g8) は束ね wave。
- **(P2)** `verify_floor_bytes` は floor artifact の `path` / `sha256` / `env_tag` /
  `measurement_head` を**出所検証だけ**する。返り値は `judge` の入力にしない (§6 条件 7
  「床値 artifact は本条件の入力にしない」)。judge の出力が floor 値に不変であることを
  テストで pin する。
- **(P3)** `publish_result_table` は出力先を caller から受け取り、repo 内 path を hard-code
  しない (t1333 wave 裁定「正式 run の出力先を repo 外へ強制する」に整合)。
- **(P4)** judge は完全 block・反復添字の欠測/重複/不連続・n の exact 不一致・非有限値・
  パラメータ未記入を**判定不能**へ倒す。行を削って対を作り直さない。unpaired 退避を実装しない。

## 不変条件 (破ったら停止)

- `s8c_preregistration_evidence_contract.v1.json` と `output/s8c-preregistration/condition-freeze/`
  は 1 byte も触らない。`docs/phase3-8c-preregistration.md` §5 / §6 の本文も触らない。
- 既存テストの期待値を反転・緩和・skip・削除しない。判定条件を 3 未満にしない。
  result cell 集合の欠落を許す受理形を作らない (規律 2)。
- `FROZEN_MANIFEST` 23 件に `.py` は 0 件、契約 JSON も非該当 (DW-O09 閉包検査済み)。
  gate 入力の実在 (DW-O13) は `_FLOOR_LEDGER_KEYS` に `env_tag` / `measurement_head` /
  `protocol_sha256` が実在することで確認済み。

## 成果物影響 (DW-G05)

実装しなければ C07 は `floor-judge-contract-undefined` のまま固定され、8c 事前登録は発効せず
正式系列が 1 回も起動しない。すなわち certified な選択結果が 0 件のまま止まる。
本 wave 単体では発効しない (登録は束ね wave) が、束ね wave が反転できる形を作るのが本 wave の値である。

## 変更面アンカー

| file | anchor |
|---|---|
| `orchestrator/campaign/s8c_result_judge.py` | 新規 |
| `orchestrator/campaign/s8c_preregistration_evidence.py` | `_evaluate_c12` (1765) の後、`_MACHINE_EVALUATORS` (1806) の手前 |
| `orchestrator/tests/test_s8c_preregistration_predicates.py` | `_negative_control_case` (653)、`NEGATIVE_CONTROL_CASES` (735) 周辺 |
| `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` | **不可侵** (条件 7 は 245-300 行) |

## 分割方針

編集ファイル所有が素集合になる 2 単位。単位 A = `s8c_result_judge.py` (新規)。
単位 B = `s8c_preregistration_evidence.py` + 予測テスト。B は A の関数名に依存するので
A を先行完了させてから B を投入する (逐次)。規模が小さければ 1 単位で可。

## 受入・実測環境

Pegasus login ノード。焦点走は `python3 tools/run_tests.py <file>` の bounded local。
受入全走は `python3 tools/run_tests.py` の素の相対 argv ちょうど。
