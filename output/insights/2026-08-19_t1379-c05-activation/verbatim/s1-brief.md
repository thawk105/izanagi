# T-1379 段1 brief — 8c 条件 C05 の activation

## Scope

D529 の不可分改訂単位を **1 commit** で実装する。

1. 契約 JSON `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json`
   condition_number=5 の `machine_checkable` を `false` → `true`。
2. `orchestrator/campaign/s8c_preregistration_evidence.py` の `_MACHINE_EVALUATORS`
   辞書へ `5: _evaluate_c05,` を追加 (1 行。`_evaluate_c05` は entry (662) で実装済み、
   line 1631 に現存)。`_evaluate_undefined` の `elif number == 5:` 分岐、
   `PredicateRegistry.evaluate` 本体は変更しない (下記「不変条件」参照)。
3. `orchestrator/campaign/s8c_preregistration.py:51` の `DECIDER_VERSION` を
   `s8c-decider/v3` → `s8c-decider/v4`。
4. `prepare_revision(ruling_reference="D529", revision_reason=...)` で凍結世代
   g8 を発行 (`output/s8c-preregistration/condition-freeze/condition-freeze.v1.g8.json`)。
5. §5 `master_seed` 欄記入 (`docs/phase3-8c-preregistration.md:192`)。
6. `output/s8c-preregistration/schedule.v1.json` を
   `orchestrator/campaign/s8c_schedule.regenerate(master_seed, authority=...)` で
   新規生成し commit。
7. メタテスト追随 (`orchestrator/tests/test_s8c_preregistration_predicates.py`):
   - `nc_c05_initial_state_hash_bitflip` を `NON_MACHINE_CHECKABLE_NEGATIVE_CONTROL_CASES`
     (line 929) から `NEGATIVE_CONTROL_CASES` (line 918) へ移す。
   - `test_satisfiable_predicate_requires_negative_control` (line 2390) のハードコード
     期待集合を 7 条件→8 条件 (`C05` 追加)、`exercised == 7` → `8` に更新。
   - `_negative_control_case` (line 824-915) に C05 用の token-only / mutated ソース
     ペアを新規実装 (現状 C05 分岐が無く `raise AssertionError` に落ちる)。
   - `test_noop_and_token_only_fixtures_never_satisfy` の `expected_reasons` (line 2433) へ
     C05 の reason_code を追加。

## 確定済みユーザー裁定 / 設計判断

- D529: 契約反転・registry 登録・DECIDER_VERSION bump・新世代発行は不可分の 1 改訂単位。
- F393: 契約を変えた commit を祖先に残さない。手順は「未 commit の変更 (または
  `git reset --soft <変更前 HEAD>`) の状態で `prepare_revision(commit=<変更前 HEAD>)`
  を呼び g8 を生成 → 契約・コード・g8・§5・schedule artifact を **まとめて 1 commit**」。
  本 brief 作成時に隔離 worktree で実測済み (下記)。

## 不変条件

- `_evaluate_c05` は静的到達可能性検査のみで **SATISFIED を返す分岐が無い** (実装を通読して確認)。
  よって `SATISFIABLE_CONDITION_IDS` (現在空 frozenset) への追加は不要。
- `_evaluate_undefined` の `elif number == 5:` 分岐は削除しない。判定対象は
  「指定 commit の tree」であり、activation 前の historical commit を評価する経路
  (`machine_checkable=false` のまま) が今後も生き続けるため。
- 規律 2/3 (正しさゲート・シグナルの後付け禁止) は緩めない。

## 実測済み事実 (前提の是正)

- **稼働中 8c wave の実態**: 引数が挙げた 4 件のうち `dev-wave-t1352-c07-result-judge` と
  `dev-wave-t1348-c09-c10-consumer` は既に main (`a31832d9`) へ merge 済みで非稼働。
  真に稼働中なのは `worktree-dev-wave-s8c-c12-c04-c11` (C12/C04/C11) と
  `worktree-dev-wave-t1353-c03-c08` (C03/C08) の 2 件で、どちらも「受入前に local main を
  取り込む」commit まで進行済み (受入に近い)。
- **ファイル面の重複**: 契約 JSON・`_MACHINE_EVALUATORS` 辞書本体・`DECIDER_VERSION` 定義行・
  凍結世代 dir・`schedule.v1.json`・`docs/phase3-8c-preregistration.md` はこの 2 wave と
  非重複 (diff hunk 境界を実測)。**ただし** `test_s8c_preregistration_predicates.py` 内の
  `test_satisfiable_predicate_requires_negative_control` / `_negative_control_case` /
  `NEGATIVE_CONTROL_CASES` は `t1353-c03-c08` が C03/C08 向けに構造ごと書き換え中で重複する。
  両 wave は受入に近い進行度のため、**段 5 着手前に main を再確認し、着地済みなら取り込んでから
  実装する**運用で吸収する (先着地を待って強制ブロックはしない)。
- **DECIDER_VERSION の並行 wave**: 別セッション T-1355 (条件 4/7 evaluator 改訂、同じく
  DECIDER_VERSION bump を予定) と資源確認済み。main の DECIDER_VERSION は既に v3
  (v2→v3 は別 wave が消費・着地済み)。次に使えるのは v4。**T-1355 と合意済み: 本 wave (C05) が
  先に v4 で着地する前提で進め、T-1355 側は実装時に main を再確認して次の未使用版を使う。**
- **生死実験 (隔離 worktree で実編集・即時復元、TEMP commit は `a31832d9` へ reset 済み)**:
  契約反転 + registry 登録 + DECIDER_VERSION bump + g8 発行 + `schedule.v1.json` 生成まで
  フルに行い、library 経由 (`core.activation_report_at`) で確認した。
  **CLI (`python3 -m ... check`) は evaluator bytes 比較の罠で全 12 条件を `evaluator-exception`
  へ潰すため診断に使わない。** 結果: C05 は `status=UNSATISFIED`,
  `reason_code=schedule-consumer-unreachable`。理由は `p3_autonomous_workload_trial.py` の
  `run_trial` が `load_schedule` / `verify_schedule` / `consume_schedule` を一切呼んでいない
  ため (T-1380 が扱う配線が未実装、worklog 622 行)。**本 wave は C05 を発効させない**
  (entry 667 の C07 と同型 — ただし C07 の `_evaluate_c07` 自体は main に現存し「未登録」なだけで
  「削除済み」ではない。s8c-c12-c04-c11 / t1353-c03-c08 の diff で 693 行の削除に見えたのは、
  両 branch が `_evaluate_c07` 新設 commit [T-1352] より前の main snapshot を最後の取り込みと
  しているためで、削除でも共有編集でもない — diff の基準点の問題。T-1355 とのやり取りで気付き訂正済み)。

## DW-G05 成果物影響

- 実装しない場合: C05 は現状の `EVIDENCE_UNDEFINED` / `schedule-consumer-undefined` のまま。
  8c 前提条件の受理集合・certified 選択・台帳行は不変。
- 実装した場合 (本 scope): C05 は機械検査対象に載るが `UNSATISFIED` /
  `schedule-consumer-unreachable` のままで発効しない。certified 選択・台帳行は増えない。
  拒否理由の意味だけが「証拠不足 (EVIDENCE_UNDEFINED)」から「到達不能 (UNSATISFIED)」へ変わる。

## 並列分割方針

実装単位 1 本 (コード: 契約 JSON + `s8c_preregistration_evidence.py` +
`s8c_preregistration.py` + `test_s8c_preregistration_predicates.py`)。
凍結世代発行 (`prepare_revision` 実行) ・§5 記入・`schedule.v1.json` 生成・統合 commit は
親が担当 (docs 編集 + データ生成 + commit は凍結境界により実装子の権限外)。

## (P1)(P2) 攻撃対象

- **(P1)** `schedule.v1.json` の `authority` は本物の `WORKLOADS` / `ROLE_FILES` /
  `ROLE_CONTRACTS` / `GATING_SPEC` (`p3_autonomous_workload_trial.py` に実在) から構築する
  想定。テストヘルパー `_c05_authority()` 相当のダミー値をそのまま本番へ転用しない
  (§5 記入規約「seed だけを先に固定しない」の精神 — authority が暫定だと将来 T-1380 実装後に
  再生成 = 実質再抽選になるリスク)。ただし `_evaluate_c05` の結果 (到達不能で UNSATISFIED) は
  authority の中身に依存しないため、technically は暫定値でも通る。プラン起草で
  実現可能性を詰める。
- **(P2)** `master_seed` の値は暗号学的に十分な乱数を 1 回生成し固定する (結果を見る前に選ぶ)。

## 変更面 実アンカー表

| path | 変更 | 担当 |
|---|---|---|
| orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:227 | machine_checkable→true | 実装子 |
| orchestrator/campaign/s8c_preregistration_evidence.py:2607-2615 | `_MACHINE_EVALUATORS` へ 1 行追加 | 実装子 |
| orchestrator/campaign/s8c_preregistration.py:51 | DECIDER_VERSION→v4 | 実装子 |
| orchestrator/tests/test_s8c_preregistration_predicates.py:824-931,2390-2443 | 期待集合・負対照更新 | 実装子 |
| docs/phase3-8c-preregistration.md:192 | master_seed 記入 | 親 |
| output/s8c-preregistration/condition-freeze/condition-freeze.v1.g8.json | 新規発行 | 親 |
| output/s8c-preregistration/schedule.v1.json | 新規生成 | 親 |
