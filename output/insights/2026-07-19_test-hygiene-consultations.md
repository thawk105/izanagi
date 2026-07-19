# 2026-07-19 test-hygiene wave — codex 敵対相談 逐語凍結 (F20)

- 構成: codex exec, model=gpt-5.6-sol, reasoning=max, sandbox=read-only, cwd=repo (worktree s8b-c22-launch-cert, 基準 311b813)
- 相談 3 本: C1=重複統合の検算攻撃 / C2=弱テスト強化設計攻撃 / C3=プロセス・文書契約攻撃
- 親裁定: 全 13 所見 real (refuted 0)。反映後プラン v2 は本文末尾

## C1 プロンプト
```
あなたは敵対的レビュアーです。私 (オーケストレータ) のプランの U2 と U6 を攻撃してください。
手順: (1) 下記プラン全文と docs/handoff/2026-07-19-test-hygiene.md を読む。(2) orchestrator/tests/test_s8b_selector_freeze.py の :468 テストと :484 テストを精読し、「:484 が :468 の逐語上位集合 (floor/budget 除外 + binding 束縛の同一アサートを含む)」という削除根拠を独立に検算する。アサート単位で対応表を作り、:468 にしかない検査 (アサート・入力形・fixture 経路・例外経路) が 1 つでもあれば削除は危険と判定する。(3) test_s8b_oracle_driver.py の test_layer3_strict_consumer_accepts_optional_bench_wall_s を読み、「schema JSON の契約 pin であり実装コードは通らない」という docstring 追記文言が事実として正しいか検証する (本当に実装コードを通らないのか、import 経路を追う)。
出力: 所見ごとに {severity: high/medium/low, 攻撃シナリオ (何がどう壊れるか具体的に), 根拠 file:line, 提案}。所見ゼロならゼロと明言し、検算した対応表を示すこと。
# 実行プラン v1 (セッション: test-hygiene)
正本タスク: docs/handoff/2026-07-19-test-hygiene.md (全文を読むこと)。基準: 現 HEAD 311b813。
単位分割 (ファイル素集合は互いに素、codex 並列実行予定):
- U1: output/insights/2026-07-19_test-suite-hygiene-survey.md を新規作成 (調査結果の正本化。数値は handoff 記載 + git log から再導出)
- U2: orchestrator/tests/test_s8b_selector_freeze.py :468 の test_selector_basis_ignores_floor_budget_but_binds_variant_entries を削除、:484 の test_selector_basis_preimage_is_versioned_and_backward_compatible の docstring に統合の旨を 1 行明記。前提「逐語上位集合」は削除前に再検算する
- U3: 弱テスト強化: test_between_run_floor.py test_between_run_floor_admission_passes_when_no_competitor / test_execution_guard.py test_assert_machine_pin_accepts_matching_env_tag / test_p3_s4_loop.py test_value_literal_consistency_accepts_match
- U4: 弱テスト強化: test_s8b_ratified_verify.py test_transition_gn_to_gn1_allows_floor_change_unit と test_manifest_mode_100755_accepted_when_g_h_worktree_match (isinstance のみ) / test_s8b_verdict.py test_off_stock_check_accepts_valid_static_default
- U5: 弱テスト強化: test_s8b_oracle_manifest.py の「妥当入力で例外なし」だけの positive 呼び 4 件 (_snapshot / _validate_run_contract、調査時 :359,363,374,508 付近)
- U6: test_s8b_oracle_driver.py :1635 test_layer3_strict_consumer_accepts_optional_bench_wall_s の docstring に「schema JSON の契約 pin であり実装コードは通らない」旨を追記 (削除しない)
強化規律: 追加アサートのみ (既存アサート不変)、各追加アサートは 1〜2 個、戻り値/状態の内容アサート。各追加アサートは一度わざと壊して赤を確認してから戻す (red→green 実証、証跡を残す)。
完了検査: python3 tools/run_tests.py 全緑 (直近基準 1957 passed) + python3 tools/check_docs.py 緑 → worklog 1 エントリ + 本 handoff 削除 → 新 branch test-hygiene に commit (AI-Agent trailer)。push はしない (Pegasus 規約、ユーザー引き渡し)。
```
## C1 出力 (逐語)
結論: **U2 は現案のまま削除不可**です。U6 の意図は正しいものの、docstring 文言は字義上不正確です。現 HEAD `311b813f4b37` を基準に検証しました。

## 所見1 — U2 の「逐語上位集合」は成立しない

- severity: **medium**
- 攻撃シナリオ: `selector_basis_sha256()` に「直前の呼び出し結果を誤って返す」キャッシュ退行が入った場合、:484 は全アサートが緑のまま、binding 変更時に正しい hash を返せなくなります。一方 :468 は最初に固定した `baseline` と比較するため、この退行を検出します。variant binding を selector basis が束縛しない回帰を見逃し得ます。
- 根拠: [:468 の固定 baseline と2比較](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_selector_freeze.py:468)、[:484 の比較ごとの再計算](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_selector_freeze.py:484)、[現実装](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_selector_freeze.py:311)
- 提案: :484 に `baseline = selector_basis_sha256(freeze)` を導入し、floor/budget と binding の両アサートをその同一値と比較してから :468 を削除してください。既存アサートを変えない方針なら、:468 を残すべきです。

具体的な誤キャッシュでの呼び出し結果は次のとおりです。`h0` は元/floor変更の正しい hash、`h1` は binding 変更の正しい hash です。

- :468: `freeze→h0`, `floor→h0`, `binding→h0(stale)`。最後の `!= baseline` が赤になる。
- :484: `freeze→h0`, `floor→h0`, `freeze→h0`, `binding→h0(stale)`, `freeze→h1(stale)`。`h0 != h1` となり誤って全緑になる。

### アサート・経路対応表

| 検査 | :468 | :484 | 判定 |
|---|---|---|---|
| 元入力 | `_freeze()` :469 | `_freeze()` :485 | 同一 helper・同一 JSON 入力 |
| 基準 hash | `baseline` に一度保存 :470 | :494、:502、:509 で都度計算 | **:468 固有の安定基準** |
| floor/budget 入力形 | deepcopy 後に同じ2フィールドを置換 :472–474 | 同一操作 :499–501 | 同一 |
| floor/budget 除外 assert | `sha(changed) == baseline` :475 | `sha(changed) == sha(freeze)` :502 | 純粋関数なら同値だが逐語・状態依存時は非同値 |
| preimage からの明示的除外 | なし | `"floor"/"budget" not in preimage` :503 | :484 固有 |
| binding 入力形 | 同じ target/key/`future=1` :477–480 | 同一操作 :505–508 | 同一 |
| binding 束縛 assert | `sha(changed) != baseline` :481 | `sha(changed) != sha(freeze)` :509 | **安定基準との比較は :468 固有** |
| fixture 経路 | 引数なし、`_freeze()` が実ファイルを読む | 同じ | :468 固有なし |
| 例外経路 | `pytest.raises` なし、valid input の未捕捉例外のみ | 同じ。追加呼び出しあり | :468 固有の入力・明示例外なし。ただし呼び出し系列は異なる |

したがって、意図した2契約は :484 に存在しますが、要求された厳密な削除基準では **危険判定**です。

## 所見2 — U6 の「実装コードは通らない」は過度に広い

- severity: **low**
- 攻撃シナリオ: 対象だけを選択実行しても、collection 時に driver・pipeline 等の production module が import されます。その import が壊れれば schema が正しくてもテスト本体へ到達せず失敗するため、「実装コードは通らない」という説明で原因を schema に誤帰属する可能性があります。
- 根拠: [production module の module-level imports](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:21)、[対象 test body は JSON の直接読込と辞書 assert のみ](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:1635)、[実際の strict validator](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/layer3_report.py:177)、[builder からの validator 呼び出し](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/layer3_report.py:380)
- 提案: docstring を次のように限定してください。  
  `layer3_schema.json の runs 定義で bench_wall_s の型と非必須性を構造として pin する。layer3_report._validate_schema / build_report は呼び出さない。`

独立 import 確認では `campaign.s8b_oracle_driver`、`campaign.pipeline`、`campaign.s8b_oracle_manifest` はロードされましたが、`campaign.layer3_report` はロードされませんでした。したがって正確な判定は次のとおりです。

- 「schema JSON の契約 pin」: **正しい**
- 「関連する strict consumer を呼ばない」: **正しい**
- 「実装コードは一切通らない」: **字義上は誤り**
## C2 プロンプト
```
あなたは敵対的レビュアーです。私 (オーケストレータ) のプランの U3/U4/U5 (弱テスト 10 件の強化) を攻撃してください。
手順: (1) 下記プラン全文と docs/handoff/2026-07-19-test-hygiene.md を読む。(2) 対象 10 件それぞれのテスト本体と被検証実装を読み、次を検証する: (a) 「妥当入力で例外なしだけ」という弱さ診断は正しいか (実は意味あるアサートを既に持つ件はないか)、(b) 追加すべき「内容アサート」として何が意味を持つか — 具体的なアサート案を件ごとに 1〜2 個提案 (期待値は実装の現挙動の単なる写経 = change-detector にならないよう、契約・裁定・docstring に根拠づける)、(c) 恒真化のリスク (追加アサートが実装と同じ計算で期待値を作る自己参照になっていないか)、(d) red→green 実証手順の穴 (壊し方が別経路で赤くなるだけで当該アサートの実効性を示さないケース)。(3) 追加アサートのみ・既存アサート不変という制約で困難な件があれば指摘する。
出力: 対象ごとに {対象テスト, 診断の当否, 提案アサート (根拠 file:line 付き), 恒真リスク, severity}。10 件全部に言及すること。
# 実行プラン v1 (セッション: test-hygiene)
正本タスク: docs/handoff/2026-07-19-test-hygiene.md (全文を読むこと)。基準: 現 HEAD 311b813。
単位分割 (ファイル素集合は互いに素、codex 並列実行予定):
- U1: output/insights/2026-07-19_test-suite-hygiene-survey.md を新規作成 (調査結果の正本化。数値は handoff 記載 + git log から再導出)
- U2: orchestrator/tests/test_s8b_selector_freeze.py :468 の test_selector_basis_ignores_floor_budget_but_binds_variant_entries を削除、:484 の test_selector_basis_preimage_is_versioned_and_backward_compatible の docstring に統合の旨を 1 行明記。前提「逐語上位集合」は削除前に再検算する
- U3: 弱テスト強化: test_between_run_floor.py test_between_run_floor_admission_passes_when_no_competitor / test_execution_guard.py test_assert_machine_pin_accepts_matching_env_tag / test_p3_s4_loop.py test_value_literal_consistency_accepts_match
- U4: 弱テスト強化: test_s8b_ratified_verify.py test_transition_gn_to_gn1_allows_floor_change_unit と test_manifest_mode_100755_accepted_when_g_h_worktree_match (isinstance のみ) / test_s8b_verdict.py test_off_stock_check_accepts_valid_static_default
- U5: 弱テスト強化: test_s8b_oracle_manifest.py の「妥当入力で例外なし」だけの positive 呼び 4 件 (_snapshot / _validate_run_contract、調査時 :359,363,374,508 付近)
- U6: test_s8b_oracle_driver.py :1635 test_layer3_strict_consumer_accepts_optional_bench_wall_s の docstring に「schema JSON の契約 pin であり実装コードは通らない」旨を追記 (削除しない)
強化規律: 追加アサートのみ (既存アサート不変)、各追加アサートは 1〜2 個、戻り値/状態の内容アサート。各追加アサートは一度わざと壊して赤を確認してから戻す (red→green 実証、証跡を残す)。
完了検査: python3 tools/run_tests.py 全緑 (直近基準 1957 passed) + python3 tools/check_docs.py 緑 → worklog 1 エントリ + 本 handoff 削除 → 新 branch test-hygiene に commit (AI-Agent trailer)。push はしない (Pegasus 規約、ユーザー引き渡し)。
```
## C2 出力 (逐語)
結論：U3/U4/U5 の一括方針は修正必須です。10 件の内訳は次のとおりです。

- 8 件は `-> None` の純 validator。正常系の契約そのものが「例外を送出しない」であり、返却内容は存在しない。
- 1 件は既に重要な型状態 `LaunchValidatedFreeze` を assert 済み。
- 本当に返却内容を捨てているのは `_validate_run_contract` の 1 件だけ。

以下の severity はプラン欠陥について、S1=修正必須、S2=低価値化の懸念、S3=現案で実施可能、です。

### 1. `test_between_run_floor_admission_passes_when_no_competitor`

- 対象テスト: [`test_between_run_floor.py:65`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_between_run_floor.py:65)
- 診断の当否: 形式上は「例外なしだけ」だが、弱さ診断は過大。被検証関数は明示的に `-> None` の拒否 validator で、競合なしを受理することが正常系契約そのものです。[`p2_2.py:80`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/p2_2.py:80)。競合ありの拒否・メッセージ・routing は直前のテストが既に検査しています。[`test_between_run_floor.py:24`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_between_run_floor.py:24)
- 提案アサート: マージ価値がある内容アサートはなし。強いて戻り値契約を pin するなら `assert between_run_floor._assert_single_tenant() is None` だけですが、二重呼び出しか既存 call の置換が必要です。
- 恒真リスク: `assert runner.competing_bench_pids() == []` は stub 自身の確認で恒真。validator を `pass` にしても `is None` は緑で、guard の実効性は強まりません。`return True` を空 branch に入れる mutation なら新 assert だけを赤にできますが、証明されるのは return convention だけです。
- severity: S2

### 2. `test_assert_machine_pin_accepts_matching_env_tag`

- 対象テスト: [`test_execution_guard.py:37`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_execution_guard.py:37)
- 診断の当否: 形式上は正しいが、「弱い」は不適切。契約は env tag の完全一致なら通し、不一致なら例外、かつ戻り値なしです。[`execution_guard.py:54`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/execution_guard.py:54)。不一致側は直後で検査済みです。[`test_execution_guard.py:41`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_execution_guard.py:41)
- 提案アサート:
  - `assert _contract().env_tag == _ENV` — 正例 fixture が本当に一致ケースであることの pin。
  - `assert eg.assert_machine_pin(_contract(), machine_env_tag=_ENV) is None` — `-> None` の API pin。
- 恒真リスク: 前者は fixture の確認、後者は return convention にすぎません。関数を no-op にしても両方緑です。比較を `!=` から `==` に壊すと既存 call の時点で赤になるため、追加 assert の有効性は実証できません。
- severity: S2

### 3. `test_value_literal_consistency_accepts_match`

- 対象テスト: [`test_p3_s4_loop.py:318`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_p3_s4_loop.py:318)
- 診断の当否: 弱さ診断は誤り寄りです。既に整数 `20` と浮動小数表記 `20.0` の二つの意味ある正常境界を検査しています。契約は値と literal の数値一致を要求する raise-only validator です。[`p3_s4_loop.py:529`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/p3_s4_loop.py:529)、裁定根拠は [`decisions.md:1128`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/decisions.md:1128)。不一致・literal 不在は既に拒否テストがあります。[`test_p3_s4_loop.py:328`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_p3_s4_loop.py:328)
- 提案アサート: 内容アサートは不可能。強いて行うなら既存二呼び出しをそれぞれ `assert L.assert_value_literal_consistent(...) is None` とするだけです。
- 恒真リスク: validator を `pass` にしても `is None` は緑。regex で literal を再抽出して assert すると実装と同じ計算の自己参照になります。比較を壊して正例を拒否させれば既存 call が先に赤くなり、新 assert の証拠にはなりません。
- severity: S2

### 4. `test_transition_gn_to_gn1_allows_floor_change_unit`

- 対象テスト: [`test_s8b_ratified_verify.py:797`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:797)
- 診断の当否: raise-only 正常系としては妥当です。問題は assertion 不足ではなく、コメントが `floor_protocol`、`measurement_closure`、header まで受理すると謳う一方、実入力が変えているのは `floor` と `generation_number` だけな点です。許可表は [`s8b_ratified_freeze.py:121`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:121)、承認済み F5 は [`phase3-8b-descriptor-design.md:381`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3-8b-descriptor-design.md:381)。
- 提案アサート: assertion-only を守るなら、挙動ではなく契約表 pin に限定すべきです。
  - `assert {"/floor", "/floor_protocol", "/floor_source", "/measurement_closure", "/generation_number"} <= M._TRANSITION_GN_TO_GN1`
  - `assert "/env_tag" not in M._TRANSITION_GN_TO_GN1`
- 恒真リスク: これは実装と同じ diff 計算ではなく裁定由来の定数 pin ですが、`_assert_transition` が表を正しく消費することまでは示しません。`/floor_protocol` だけ表から除去すれば既存 call は緑、新 assert のみ赤となり実効性を示せます。挙動保証には field ごとの追加正常系が必要で、「追加アサートのみ」に収まりません。
- severity: S1

### 5. `test_manifest_mode_100755_accepted_when_g_h_worktree_match`

- 対象テスト: [`test_s8b_ratified_verify.py:1468`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:1468)
- 診断の当否: 「意味ある assert がない」は明確に誤りです。`LaunchValidatedFreeze` は全 launch 検証を通った型状態であり、consumer が要求する security boundary です。[`s8b_ratified_freeze.py:751`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:751)。さらに別ファイルに、実 mode が `"100755"` であることと同じ型昇格を両方検査する強い複合テストがあります。[`test_s8b_ratified_freeze.py:943`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:943)
- 提案アサート: 残すなら出力を増やすより正例の前提を局所 pin します。
  - `assert topology["mode_map"][topology["paths"]["manifest"]] == "100755"`
  - `assert validated.ratified is freeze`
  
  ただし現在は topology を `_` へ捨てているため、前者には既存 assignment の変更が必要です。
- 恒真リスク: fixture の `chmod` を無効化すると validator は合法な `100644` として成功し、mode assert だけ赤になるため、これは「正例が本当に 100755」の証明になります。一方、validator から 100755 許可を削る mutation は `launch_validate` で先に赤くなり、既存 `isinstance` だけで既に検出できます。
- severity: S1

### 6. `test_off_stock_check_accepts_valid_static_default`

- 対象テスト: [`test_s8b_verdict.py:630`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_verdict.py:630)
- 診断の当否: raise-only validator なので正常系として妥当です。off arm の契約は `static_default + c06 + stock_common`。[`phase3-8b-descriptor-design.md:288`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3-8b-descriptor-design.md:288)、実検査は [`s8b_verdict.py:210`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_verdict.py:210)。choice と binding の反例は既にありますが、`decision_method != "static_default"` の直接反例がありません。
- 提案アサート: 正常系への内容 assert は追加しない。正しい強化は、off row の `decision_method` を `"selector_agent"` に変え、`pytest.raises(VerdictError, match="static_default")` を要求する新しい拒否ケースです。これは「追加アサートのみ」制約に違反しますが、実際の未検査 branch を殺します。
- 恒真リスク: off row の三値を正常系後に assert しても `_valid_off_stock_rows()` の literal を再確認するだけです。`decision_method` 検査を実装から削除してもその assert は緑のままです。red は当該拒否 branch を削除し、新 negative test だけが失敗する形で取るべきです。
- severity: S1

### 7. `test_snapshot_accepts_valid_per_pair_floor`

- 対象テスト: [`test_s8b_oracle_manifest.py:359`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_manifest.py:359)
- 診断の当否: raise-only snapshot validator の baseline 正例なので、例外なしは本来の契約です。[`s8b_oracle_manifest.py:563`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:563)。ただし fixture 自身が `scalar_alt = max(pairs)` を計算しており、validator も同じ計算をします。[`s8b_v2_freeze_fixture.py:24`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/s8b_v2_freeze_fixture.py:24)、[`s8b_oracle_manifest.py:549`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:549)
- 提案アサート: merge 可能な validator 内容アサートはなし。`set(floor_h)=={"pairs","scale_ref","scalar_alt"}` や `scale_ref==100.0` は fixture-shape pin としては可能ですが、validator 強化とは称せません。実効的な追加は、例えば `budget["oracle_shared"]=False` を拒否する negative test です。契約実装は [`s8b_oracle_manifest.py:592`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:592)。
- 恒真リスク: `assert scalar_alt == max(pairs.values())` は fixture と実装の同一計算を三度目に書くだけです。validator を冒頭 `return` にしても全 input-state assert が緑になるため、内容保証になりません。
- severity: S1

### 8. `test_snapshot_accepts_explicit_null_pair`

- 対象テスト: [`test_s8b_oracle_manifest.py:363`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_manifest.py:363)
- 診断の当否: 「一部 non-stock pair だけ null、stock の `scale_ref` は有効」を受理する重要な境界正例です。裁定上、一構成の無効は当該 pair のみ null、`scalar_alt` は null です。[`2026-07-16_s8b-floor-protocol-package.md:74`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-16_s8b-floor-protocol-package.md:74)
- 提案アサート: case-shape pin としてなら次の二つ。
  - `assert {cfg for cfg, value in floor_h["pairs"].items() if value is None} == {a_pair}`
  - `assert floor_h["scale_ref"] is not None and floor_h["scalar_alt"] is None`
  
  ただし本当に必要なのは「pair を null にするが `scalar_alt` を非 null のまま残す」反例が拒否される negative test です。[`s8b_oracle_manifest.py:549`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:549)
- 恒真リスク: 提案二つは直前の代入をほぼ再確認するだけで、validator を no-op にしても緑です。`elif scalar_alt is not None` を削除する mutation を殺せるのは negative test だけです。
- severity: S1

### 9. `test_snapshot_accepts_all_null_holdout`

- 対象テスト: [`test_s8b_oracle_manifest.py:374`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_manifest.py:374)
- 診断の当否: stock 未確定 holdout の全 null 受理は意味ある正常境界です。契約は stock 無効なら全 pair null、`scalar_alt` null、`scale_ref` null。[`2026-07-16_s8b-floor-protocol-package.md:74`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-16_s8b-floor-protocol-package.md:74)
- 提案アサート: case-shape pin としてのみ、
  - `assert floor_h["pairs"] and set(floor_h["pairs"].values()) == {None}`
  - `assert floor_h["scale_ref"] is None and floor_h["scalar_alt"] is None`
- 恒真リスク: どちらも [`test_s8b_oracle_manifest.py:378`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_manifest.py:378) の代入結果を読むだけです。validator の早期 `return` mutant でも緑なので、「内容アサートによる強化」とは認定できません。
- severity: S1

### 10. `test_run_contract_accepts_bench_max_rounds_one`

- 対象テスト: [`test_s8b_oracle_manifest.py:508`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_manifest.py:508)
- 診断の当否: 正しい。これは唯一、本当に意味ある戻り値を捨てています。`_validate_run_contract` は検証済み deep copy を返し、builder はそれを manifest へ埋め込みます。[`s8b_oracle_manifest.py:341`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:341)、[`s8b_oracle_manifest.py:675`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:675)。`bench_max_rounds=1` は承認済み契約です。[`phase3-8b-descriptor-design.md:357`](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3-8b-descriptor-design.md:357)
- 提案アサート:
  - `assert validated["bench_max_rounds"] == 1`
  - `assert validated is not source`
  
  清潔な形は `source = _run_contract(1); validated = manifest._validate_run_contract(source)` と捕捉してから上記二つです。
- 恒真リスク: `validated == _run_contract(1)` だけでは input の写しであり、validator が入力をそのまま返しても通ります。`return copy.deepcopy(...)` を `return run_contract` に変える mutation なら既存の例外なし call は緑、identity assert だけ赤となり、追加 assertion の実効性を正しく示せます。
- severity: S3

総合的には、U3/U4/U5 でそのまま実施すべきなのは 10 番だけです。4 番は transition-table 契約 pin または追加挙動ケースへ変更、5 番は exact mode の局所 precondition pin に変更、6・7・8 番は未検査 branch の negative test に変更するのが妥当です。

red→green の共通基準も明文化が必要です。「期待値をわざと間違える」のは assertion が実行された証明にしかなりません。SUT または fixture を変異し、既存 call/assert は緑のまま、新 assertion だけが赤になる mutant を件ごとに事前登録すべきです。そうできない assertion は今回の「強化」には数えられません。
## C3 プロンプト
```
あなたは敵対的レビュアーです。私 (オーケストレータ) のプランのプロセス/文書契約面を攻撃してください。
手順: (1) 下記プラン全文と docs/handoff/2026-07-19-test-hygiene.md を読む。(2) 次を検証する: (a) output/insights/ への調査報告正本化は output/README.md の形式契約に適合するか (必要な構造・命名・禁止事項)、(b) worklog 1 エントリ + handoff 削除 + 同一 commit 要件 (CLAUDE.md 作業の進め方 6c: phase チェック同 commit) — この作業は phase3.md のどのチェック項目に対応するか、対応なしなら何もしなくてよいか、(c) tools/check_docs.py が今回の編集 (insight 追加・worklog 追記・handoff 削除) で赤くなる検査はないか、(d) 並列実行時の書き込み衝突 (U1〜U6 のファイル素集合が本当に素か、worklog/insights を実行単位に含めるべきか親が最後にやるべきか)、(e) branch test-hygiene を main 由来の現 HEAD から切る手順の穴 (worktree の制約、Pegasus 規約)、(f) 完了検査基準「1957 passed」の妥当性 (テスト数は変動する — 基準の立て方として正しいか)。
出力: 所見ごとに {severity, 攻撃シナリオ, 根拠 file:line, 提案}。所見ゼロの観点はゼロと明言。
# 実行プラン v1 (セッション: test-hygiene)
正本タスク: docs/handoff/2026-07-19-test-hygiene.md (全文を読むこと)。基準: 現 HEAD 311b813。
単位分割 (ファイル素集合は互いに素、codex 並列実行予定):
- U1: output/insights/2026-07-19_test-suite-hygiene-survey.md を新規作成 (調査結果の正本化。数値は handoff 記載 + git log から再導出)
- U2: orchestrator/tests/test_s8b_selector_freeze.py :468 の test_selector_basis_ignores_floor_budget_but_binds_variant_entries を削除、:484 の test_selector_basis_preimage_is_versioned_and_backward_compatible の docstring に統合の旨を 1 行明記。前提「逐語上位集合」は削除前に再検算する
- U3: 弱テスト強化: test_between_run_floor.py test_between_run_floor_admission_passes_when_no_competitor / test_execution_guard.py test_assert_machine_pin_accepts_matching_env_tag / test_p3_s4_loop.py test_value_literal_consistency_accepts_match
- U4: 弱テスト強化: test_s8b_ratified_verify.py test_transition_gn_to_gn1_allows_floor_change_unit と test_manifest_mode_100755_accepted_when_g_h_worktree_match (isinstance のみ) / test_s8b_verdict.py test_off_stock_check_accepts_valid_static_default
- U5: 弱テスト強化: test_s8b_oracle_manifest.py の「妥当入力で例外なし」だけの positive 呼び 4 件 (_snapshot / _validate_run_contract、調査時 :359,363,374,508 付近)
- U6: test_s8b_oracle_driver.py :1635 test_layer3_strict_consumer_accepts_optional_bench_wall_s の docstring に「schema JSON の契約 pin であり実装コードは通らない」旨を追記 (削除しない)
強化規律: 追加アサートのみ (既存アサート不変)、各追加アサートは 1〜2 個、戻り値/状態の内容アサート。各追加アサートは一度わざと壊して赤を確認してから戻す (red→green 実証、証跡を残す)。
完了検査: python3 tools/run_tests.py 全緑 (直近基準 1957 passed) + python3 tools/check_docs.py 緑 → worklog 1 エントリ + 本 handoff 削除 → 新 branch test-hygiene に commit (AI-Agent trailer)。push はしない (Pegasus 規約、ユーザー引き渡し)。
```
## C3 出力 (逐語)
結論: v1 はそのまま実行不可です。must-fix 6 件、should 2 件があります。特に branch 作成時点、Pegasus 上のテスト場所、並列 red→green、完了検査順が危険です。

### 1. 着手条件が未充足

- severity: must-fix
- 攻撃シナリオ: `ai-development-observability` handoff が残っており、再開時には worklog・docs・`check_docs.py` 編集を直列化すると宣言しています。test-hygiene の親が worklog を閉じる瞬間に再開されると競合します。現在の「この3計画以外は空」という自前の着手条件にも違反しています。
- 根拠: [test-hygiene.md:11](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:11)、[ai-development-observability.md:4](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:4)、[ai-development-observability.md:10](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-ai-development-observability.md:10)、[handoff/README.md:15](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/README.md:15)
- 提案: observability を完了させるか、明示的に予約停止して test-hygiene の着手条件を更新してから U1〜U6 を開始してください。ユーザー GO だけでは空ディレクトリ条件を満たしません。

### 2. handoff の状態値が契約外で checker も見逃す

- severity: should
- 攻撃シナリオ: `状態: 実行中` は許可値外です。セッションが落ちても `check_docs.py` の48時間 stale 検査は `作業中|計測中` にしか発火せず、死んだセッションが永続的に検出されません。実際、現状態で `check_docs.py` は緑です。
- 根拠: [test-hygiene.md:4](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:4)、[handoff/README.md:27](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/README.md:27)、[handoff/README.md:36](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/README.md:36)、[check_docs.py:217](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/check_docs.py:217)、[check_docs.py:220](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/check_docs.py:220)
- 提案: `状態: 作業中` にし、マネージャーセッション等の説明は別の進捗行へ移してください。

### 3. branch 作成が遅く、起点も現 main ではない

- severity: must-fix
- 攻撃シナリオ: 現 worktree は `test-runner-autoscale` の 311b813、`main` は別 worktreeで 240d1cc です。311b813 と main の tree は現時点では同一ですが、311b813 は main の merge commit より前です。最後まで既存 branch 上で並列編集すると、誤 commit・branch 切替失敗・既存 branch 汚染が起き得ます。
- 根拠: [test-hygiene.md:6](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:6)、[worktree HEAD:1](/home/SFC/tanab/github/izanagi/.git/worktrees/s8b-c22-launch-cert/HEAD:1)、[main ref:1](/home/SFC/tanab/github/izanagi/.git/refs/heads/main:1)、[test-runner-autoscale ref:1](/home/SFC/tanab/github/izanagi/.git/refs/heads/test-runner-autoscale:1)
- 提案: 並列編集前に、期待する handoff 差分だけであることを確認して `git switch -c test-hygiene main`。`main` 自体は別 worktree で使用中なので `git switch main` はしないでください。作成後に `HEAD == main` を確認します。

### 4. ファイル素集合でも red→green 実行は独立していない

- severity: must-fix
- 攻撃シナリオ: U1〜U6 の列挙対象ファイル自体は素ですが、同じ working tree 上で複数 unit が意図的に赤い assert を置きます。全ファイル・全スイートを走らせる unit があると、別 unit の一時変異で赤になり「自分の assert が効いた」と誤認できます。handoff にだけ証跡を置けば、正常終了時の削除で証拠も消えます。
- 根拠: [test-hygiene.md:29](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:29)、[handoff/README.md:8](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/README.md:8)、[handoff/README.md:15](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/README.md:15)、[handoff/README.md:18](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/README.md:18)、[CLAUDE.md:92](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/CLAUDE.md:92)
- 提案: 各 unit は担当 node ID だけを実行し、期待した追加 assert の failure diff まで照合してから復元すること。全走は全 unit join・全変異復元後に親だけが実行します。証跡は `{nodeid, 壊した期待値, 期待した失敗, 復元後green}` の表として insight に残してください。別 Codex セッションとして走らせるなら各 unit は固有 handoff を持ち、worklog・manager handoff・git index・branch 操作は親専有にします。

### 5. 完了検査の順序と必須検査が不足

- severity: must-fix
- 攻撃シナリオ: 現プランは `check_docs.py` の後に worklog を編集し handoff を削除します。つまり green が最終 commit 対象を検査していません。また `check_codex_agents.py` と commit 後の `check_ai_provenance.py` が欠落しています。単に「AI-Agent trailer」とするだけでは、並列相談・実装・レビューの異なる構成を復元できません。
- 根拠: [test-hygiene.md:41](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:41)、[AGENTS.md:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/AGENTS.md:26)、[AGENTS.md:28](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/AGENTS.md:28)、[ai-provenance.md:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/ai-provenance.md:14)、[ai-provenance.md:49](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/ai-provenance.md:49)、[ai-provenance.md:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/ai-provenance.md:116)
- 提案: `unit join・親diff監査 → 全走 → worklog最終化・handoff削除 → check_codex_agents + check_docs + 最終status/diff → commit → check_ai_provenance` の順に変更してください。trailer は実質寄与した各 product/model/reasoning/role/scope を列挙します。

### 6. Pegasus のログインノードで全走する穴

- severity: must-fix
- 攻撃シナリオ: 現環境は `pegasus02`、PBS allocation なしです。ここで `run_tests.py` を実行すると最大32 xdist workerをログインノードに起動し、Pegasus 規約に違反します。並列 unit が同時実行すればさらに悪化します。
- 根拠: [pegasus-runbook.md:247](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/pegasus-runbook.md:247)、[pegasus-runbook.md:323](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/pegasus-runbook.md:323)、[run_tests.py:8](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:8)、[run_tests.py:106](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:106)
- 提案: targeted red→green と最終全走を `qlogin`/`qsub` で確保した計算ノード上に明記してください。別 worktree を作る案なら、CCBench submodule 実体化も必要です。[pegasus-runbook.md:312](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/pegasus-runbook.md:312)

### 7. 「1957 passed」は acceptance gate にならない

- severity: must-fix
- 攻撃シナリオ: 1957 は 311b813 時点の観測値です。本タスクはテスト関数を1本削除するため、他が同じなら1956になります。固定件数は意図した削除を失敗扱いする一方、重要テストの消失を無価値な追加テストで相殺できます。
- 根拠: [worklog.md:796](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/worklog.md:796)、[test-hygiene.md:24](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:24)、[repo-refinement-consultations.md:16](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-17_repo-refinement-consultations.md:16)、[run_tests.py:101](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/run_tests.py:101)
- 提案: 1957 は参考値に降格。基準 commit と最終 tree の collected node-ID 集合を比較し、「削除対象 node ID だけが消え、他の追加・消失なし」を gate にします。加えて pytest exit 0、failed/error 0、skip/xfailed の分類・理由に予期しない変化なしを要求してください。

### 8. insight の数値 provenance が未規定

- severity: should
- 攻撃シナリオ: d4cbf91 の1573収集、7/14–18のgit統計、311b813の1957 passedを基準表示なしで一つの「現在の調査結果」にすると、再現不能な混成正本になります。
- 根拠: [test-hygiene.md:6](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:6)、[test-hygiene.md:16](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:16)、[output/README.md:42](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:42)、[output/README.md:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:47)
- 提案: insight 冒頭に、各指標の基準 commit/range、再導出コマンド、母数・分母、環境、confirmed/refuted、施策裁定を記録してください。「Izanagi 内部監査・CCBench 還元候補なし」も明記します。CCBench バグを主張する場合だけ `還元判断: ユーザー確認待ち` が必須です。[output/README.md:61](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:61)

### ゼロ所見

- insight の置き場と名前は適合しています。`output/insights/2026-07-19_test-suite-hygiene-survey.md` は `YYYY-MM-DD_<topic>.md` 契約どおりです。[output/README.md:52](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:52)
- U1〜U6 の明示された対象ファイル集合には直接重複なし。insight は U1 専有、worklog・manager handoff は親が最後に専有する分担で正しいです。
- この作業に対応する `phase3.md` のチェック項目はありません。現行の番号付き未完項は段7・8・9で、テスト衛生はどれも完了させません。[phase3.md:291](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:291)、[phase3.md:300](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:300)、[phase3.md:359](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3.md:359)  
  したがって phase チェックを捏造・変更せず、worklog 1エントリと handoff 削除を同一 commit に含めればよいです。
- 最終内容に対する `check_docs.py` の直接的な赤要因はありません。insight/worklog は living-doc 検査外、handoff 削除も glob 対象から消えるだけです。worklog は現在70,082Bで100,000B閾値まで余裕があります。[check_docs.py:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/check_docs.py:21)、[check_docs.py:200](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/tools/check_docs.py:200)
- push/PRを人間へ引き渡す点はPegasus境界に適合しています。[test-hygiene.md:49](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:49)

## 親裁定とプラン v2 (2026-07-19)

| 所見 | 裁定 | 反映 |
|---|---|---|
| C1-1 :484 は逐語上位集合でない (固定 baseline は :468 固有) | real | :484 に baseline 変数 + 追加アサート 2 本を足してから :468 削除 (E2) |
| C1-2 U6 docstring「実装コードは通らない」は過度に広い | real | 「layer3_schema.json の契約 pin。layer3_report の validator は呼ばない」に限定 (E2) |
| C2 #1/#2/#3 恒真リスク・診断過大 | real | 強化しない。raise-only validator の契約どおりと裁定、理由を survey insight に正本化 (E1) |
| C2 #4 遷移表の裁定由来 pin | real | _TRANSITION_GN_TO_GN1 の包含 pin + /env_tag 非包含 pin を追加 (E3) |
| C2 #5 mode 前提の局所 pin | real | topology 捕捉 + mode_map=="100755" pin + validated.ratified is freeze (E3) |
| C2 #6 decision_method 未検査 branch | real | 負例テスト新設 (E4) |
| C2 #7 oracle_shared=False 未検査 | real | 負例テスト新設。SUT が拒否しない場合は実装を変えず所見として凍結 (E5) |
| C2 #8 pair null + scalar_alt 非 null 未検査 | real | 負例テスト新設 (E5) |
| C2 #9 全 null 正例は強化不能 | real | 変更なし、理由を正本化 (E1) |
| C2 #10 _validate_run_contract 戻り値 | real | 戻り値捕捉 + bench_max_rounds==1 + is not source (E5) |
| C2 red→green 基準 (期待値壊しは実行証明のみ) | real | 各件に SUT/fixture mutant を事前登録、親が計算ノードで matrix 実行 (新アサートのみ赤を要求) |
| C3-1 着手条件字義未充足 / C3-2 状態値 / C3-3 branch / C3-4 並列 red→green / C3-5 検査順序 / C3-6 計算ノード / C3-7 件数 gate / C3-8 provenance | real | 逸脱記録の上続行 / 作業中 / main から test-hygiene 新設済み / mutant 親集約 / C3 提案順に変更 / 全テスト実行は qsub 計算ノード・codex は collect-only まで / node-ID 集合差分 gate / insight に指標ごとの基準 commit と再導出コマンド |

# 追補 (同日): codex 敵対レビュー 3 本の逐語凍結 (実行フェーズ後)

- 構成: codex exec, model=gpt-5.6-sol, reasoning=max, sandbox=read-only。R1=恒真・弱化 / R2=裁定準拠 / R3=事実性
- 親裁定: 全 13 所見 real (R1: 3, R2: 4, R3: 6)。反映: survey insight の事実性修正 (codex fix)、handoff の enum 修正 + v1 節 superseded 化、matrix へ M9/M10 追加 + M2 非判別の明示 + 第一失敗行の証跡化、insight 2 本の commit 同梱、.exec-registry は commit しない (証跡は survey へ転記)

## R1 プロンプト
```
あなたは敵対的レビュアー (恒真・弱化レンズ) です。branch test-hygiene の変更 (git diff main で見よ。テスト 5 ファイル + insights 2 + handoff 1) を攻撃してください。
検査項目: (1) 既存アサートの弱化・削除が「重複統合 (test_s8b_selector_freeze.py の 1 テスト削除)」以外に存在しないこと。(2) 追加アサート・新設負例テストが恒真でないこと — 特に、期待値を SUT と同じ計算で作る自己参照、fixture の自己確認どまり、DID NOT RAISE を検出できない形を疑え。(3) 新設負例テスト 3 本 (verdict 1, oracle_manifest 2) が実際に SUT の当該拒否分岐に到達するか (途中の別 validation で先に落ちて match だけ偶然一致する偽陽性経路を疑え)。(4) .exec-registry/E2.md〜E5.md の mutant 8 件の妥当性 — 各パッチは逐語適用可能か (対象行が実在するか必ず grep で確認)、期待 (「新アサートのみ赤」) は正しいか、判別 mutant を欠く新アサートはないか。特に E3 の 2 件目は変異対象が orchestrator/tests/test_s8b_ratified_freeze.py だが、被検テストは test_s8b_ratified_verify.py の _build_launch_repo を使う — fixture 経路が本当にそのファイルの chmod 行を通るか import/呼び出しを追って検証せよ。
出力: 所見ごとに {severity: high/medium/low, 攻撃シナリオ, 根拠 file:line, 提案}。所見ゼロの項目はゼロと明言。
```
## R1 出力 (逐語)
結論: high 0件、medium 2件、low 1件です。テスト本体の弱化や負例の偽陽性はありませんが、mutant matrix は現状のままでは完了証拠になりません。

## 所見

1. `{severity: medium}`

   攻撃シナリオ: E2 の2件目を実行すると、追加した fixed-baseline assert ではなく、それより前の既存 checksum assert で停止します。親が「target node が赤」を見るだけなら、追加 assert が実行されていないのに red→green 実証済みと誤認できます。

   根拠: [E2.md:31](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/.exec-registry/E2.md:31) は追加 floor/budget assert が赤になるとしますが、実際の最初の失敗は既存 assert [test_s8b_selector_freeze.py:480](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_selector_freeze.py:480) でした。対象の追加 assert は [同:489](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_selector_freeze.py:489) で未到達です。これは「新 assertion だけ赤」という基準 [consultations:194](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-hygiene-consultations.md:194) に違反します。

   提案: floor/budget の fixed-baseline assert を既存 checksum assert より先へ移すか、既存 assert をすべて通過して line 489 だけを殺す stateful-cache mutant に置換してください。証跡には exit codeだけでなく、最初に失敗した `file:line` を記録すべきです。

2. `{severity: medium}`

   攻撃シナリオ: 登録済み8 mutantを全部通しても、複数の新 assert を削除・恒真化でき、そのまま matrix が合格します。「各追加 assertion の実効性」という正本の主張を満たしません。

   根拠:

   - `/env_tag` 非包含 assert [test_s8b_ratified_verify.py:804](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:804) に対応する mutant がありません。E3-1 は包含集合の `/floor_protocol` だけを殺します。
   - `validated.ratified is freeze` [同:1480](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:1480) は E3-2 が line 1479 で先に止まるため未検査です。しかも同じ identity は既に [同:677](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:677) で固定済みです。
   - `validated["bench_max_rounds"] == 1` [test_s8b_oracle_manifest.py:528](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_manifest.py:528) は、E5-1では緑のままです。失敗するのは identity assertだけです。
   - floor fixed-baseline assertについては所見1のとおりです。

   提案: `/env_tag` を許可集合へ追加する mutant、検証後の返却 copy だけを `bench_max_rounds=2` にする mutantを追加してください。ratified identity は既存重複として強化件数から外すか、対象node限定の判別 mutantを登録してください。また「新 assertのみ赤」が対象node内か全suite内かを明記してください。

3. `{severity: low}`

   攻撃シナリオ: 中断・再開した作業者が live handoff の旧プランを正本として読み、既に否定された「逐語上位集合」を前提に削除したり、変更不要と再裁定した4テストまで再編集したりします。

   根拠: handoff は依然「吸収先が逐語上位集合」と記載しています [handoff:25](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:25)。また10件すべてへの内容assert追加と assertion-only を指示しています [同:30](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:30)、[同:51](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:51)。これは親裁定 [consultations:284](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-hygiene-consultations.md:284) 以降と矛盾します。

   提案: 「未完の作業」をプランv2へ置換するか、旧節全体を明示的に superseded としてください。

## 検査項目別判定

1. 既存assertの弱化・削除: 所見ゼロ。削除されたassertは、指定された selector test 1本の2assertだけです。`_validate_run_contract` の既存呼び出しも戻り値捕捉へ置換されただけで維持されています。

2. 恒真・自己参照・fixture自己確認: 恒真所見ゼロ。selectorは入力変異間の metamorphic relation、transitionは裁定由来literal、run contractは返却projectionを検査しています。mode pinも単なる引数echoではなく、Git `ls-tree` 由来の実modeを確認したうえでSUT呼び出しが完了しています。ただし判別mutant不足は上記所見2です。

3. 新設負例3本の拒否分岐到達: 所見ゼロ。直接実行した traceback の最終raiseは次のとおりでした。

   - verdict → [s8b_verdict.py:233](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_verdict.py:233)
   - `oracle_shared=False` → [s8b_oracle_manifest.py:593](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:593)
   - null pair + non-null scalar → [s8b_oracle_manifest.py:557](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:557)

   各対象branchを無効化すると後続validationも通るため、正しく `DID NOT RAISE` になります。

4. mutant 8件: 置換元は `grep -nF` で全8件とも実在・各1件でした。期待は E2-2だけ不成立、残り7件は対象nodeについて成立します。

   特記されたE3-2の経路も成立します。[verify側wrapper:558](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:558) → `B.build_production_emitter_g1` 呼び出し [同:567](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:567) → 実体 [ratified_freeze test:458](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:458) → 対象chmod [同:540](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:540) を通ります。変異後はG/A/worktreeがすべて`100644`となり、validatorは合法modeとして受理し、追加mode assertだけが赤になります。

なお、insights 2件と `.exec-registry/E2.md`〜`E5.md` は現在untrackedで、通常の `git diff main` には出ません。今回のレビューには含めました。
## R2 プロンプト
```
あなたは敵対的レビュアー (裁定準拠レンズ) です。branch test-hygiene の変更 (git diff main) が、裁定の正本 output/insights/2026-07-19_test-hygiene-consultations.md の「親裁定とプラン v2」表および docs/handoff/2026-07-19-test-hygiene.md の要求に完全準拠しているか攻撃してください。
検査項目: (1) 裁定表の全行が diff に反映されているか (漏れ・過剰実装・裁定外の変更)。(2) C1 提案の docstring 文言と実装の一致 (selector_freeze の統合明記 / oracle_driver の限定文言 — 「実装コードを一切通らない」と書いていないこと)。(3) E3 の F5 参照コメント (docs/phase3-8b-descriptor-design.md:381) が実際にその位置の裁定を指すか。(4) 新テストの命名・配置・コメント言語がスイート慣行 (周辺テスト) と整合するか。(5) handoff の「追加アサートのみ・既存アサートは触らない」精神との整合 — 変数捕捉 (topology / source) や import 追加が既存検査の意味を変えていないか。(6) 強化不要と裁定した 4 件 (#1 #2 #3 #9) に触れていないこと。
出力: 所見ごとに {severity, 攻撃シナリオ, 根拠 file:line, 提案}。所見ゼロの項目はゼロと明言。
```
## R2 出力 (逐語)
結論: **完全準拠ではありません。** E2〜E5 のテスト実装は裁定どおりですが、正本の追跡状態と完了証跡に merge-blocking な未完があります。所見は4件です。

## 所見

### 1. E1 と裁定正本が `git diff main` から脱落

- severity: **high / merge blocker**
- 攻撃シナリオ: 現在の tracked diff だけを commit・適用すると、handoff が参照する裁定正本と survey insight が消えます。#1/#2/#3/#9 を強化しない理由も永続化されず、次セッションが旧 handoff に従って再実装できます。
- 根拠: [handoff:7](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:7)、[handoff:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:22)、[親裁定:286](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-hygiene-consultations.md:286)、[survey:104](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:104)。両 insight は `git status` で `??`、`main` に存在せず、`git diff --name-status main` にも出ません。
- 提案: `2026-07-19_test-hygiene-consultations.md` と `2026-07-19_test-suite-hygiene-survey.md` の両方をレビュー対象・最終 commit に含める。.exec-registry は裁定外なので含めない。

### 2. red→green matrix・node-ID 差分・最終 gate の証跡がない

- severity: **high / merge blocker**
- 攻撃シナリオ: 新 assertion／負例が意図した SUT・fixture mutant だけを殺すか未証明です。通常 green だけでは、別経路で落ちるテストや恒真 assertion を「強化済み」と誤認できます。また削除 node が別の追加で相殺されても検出できません。
- 根拠: [親裁定:294](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-hygiene-consultations.md:294)、[親裁定:295](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-hygiene-consultations.md:295) に対し、[survey:135](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:135) は見出しだけです。handoff も実行を未来形で記載しています。[handoff:7](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:7)
- 提案: 計算ノードで各 node ID の事前登録 mutant、期待 failure、新検査だけが赤、復元後 green を表へ記録する。基準／最終 node-ID 集合差分、全走、`check_codex_agents.py`、最終文書に対する `check_docs.py`、worklog 吸収・handoff 削除、commit 後 provenance 監査まで完了させる。

### 3. handoff の詳細手順が親裁定 v2 と矛盾したまま

- severity: **medium**
- 攻撃シナリオ: 再開者が「未完の作業」を正本として読むと、逐語上位集合という否定済み前提で削除し、#1/#2/#3/#9 を強化し、oracle_driver に禁止された広い文言を復活させます。
- 根拠:
  - 「逐語上位集合」: [handoff:27](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:27) 対 [親裁定:284](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-hygiene-consultations.md:284)
  - 「弱テスト10件を強化」: [handoff:30](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:30) 対 [親裁定:286](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-hygiene-consultations.md:286)、[親裁定:292](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-hygiene-consultations.md:292)
  - 「実装コードは通らない」: [handoff:39](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:39) 対 [親裁定:285](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-hygiene-consultations.md:285)
- 提案: 詳細手順を v2 に書き換えるか、旧節を明確に「v1・廃止」とし、親裁定表だけを実行正本として指す。

### 4. handoff の状態値が exact enum でない

- severity: **low**
- 攻撃シナリオ: prefix を見る現 checker は通っても、exact 値を読む consumer では契約外になります。C3 が要求した「説明は別行へ」も満たしません。
- 根拠: [handoff:4](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:4) は `作業中 (...)`、契約は [handoff README:27](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/README.md:27)、[handoff README:36](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/README.md:36) の3値限定です。
- 提案: `- 状態: 作業中` のみにし、括弧内説明は進捗行へ移す。

## 6項目別判定

1. **裁定表の全行:** 上記所見1〜4。E2〜E5 のコード対応自体は漏れ・過剰実装・裁定外 production 変更ともゼロです。
2. **C1 docstring:** 実装所見ゼロ。selector は統合と固定 baseline を明記し、driver は呼ばない validator を限定しています。[selector:469](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_selector_freeze.py:469)、[driver:1636](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:1636)
3. **E3 F5 参照:** 所見ゼロ。コメントの `:381` は実際に F5 承認見出しと transition 裁定を指します。[test:799](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:799)、[phase doc:381](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/phase3-8b-descriptor-design.md:381)
4. **命名・配置・コメント言語:** 所見ゼロ。新負例は対応する正例・既存負例群の直近にあり、`accepts/rejects` 命名と日本語コメント慣行に整合します。
5. **既存検査の意味保存:** 所見ゼロ。`topology` は捨てていた返却値の捕捉だけ、`source/validated` は同じ validator を同じ入力で1回呼ぶままです。既存 assertion の削除・緩和はありません。[ratified:1476](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:1476)、[manifest:525](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_manifest.py:525)
6. **#1/#2/#3/#9 非変更:** テストコード所見ゼロ。#1〜#3 の各ファイルは diff なし、#9 の関数本体も不変です。理由の正本は survey にありますが、所見1のとおり未追跡です。[survey:106](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:106)

`git diff --check` と変更5テストファイルの AST parse は通過しました。pytest は裁定どおり、このログイン側レビューでは実行していません。
## R3 プロンプト
```
あなたは敵対的レビュアー (事実性レンズ) です。新規文書 output/insights/2026-07-19_test-suite-hygiene-survey.md の全主張を repo の一次情報と突合して攻撃してください。
検査項目: (1) 数値の再導出 — 文書記載の再導出コマンド (P3/P4/P6 等) を実際に実行し、23030 / 84.44% / 0.7349 / 28967 / 1573 / 1976 を検算せよ (乖離があれば計算方法の差を特定)。(2) 「調査時集計 23030 vs 現基準 28967」の差の説明が整合的か。(3) 施策 9 件の裁定表が handoff (棄却 2 件 = 比率目標化・フル CI 化) と矛盾しないか。(4) 弱テスト 10 件の再裁定記述が consultations insight の C2 と一致するか (番号の取り違え・裁定の反転を疑え)。(5) 「Izanagi 内部監査で CCBench 還元候補なし」の判断が output/README.md の insights 契約と整合するか。(6) プロセス逸脱節の記述の事実性 (特に GO の根拠の表現が過大でないか — ユーザーの指示は包括的なループ実行指示であり、この handoff 個別の明示 GO ではない)。(7) 実行証跡の空セクションが存在すること。
出力: 所見ごとに {severity, 攻撃シナリオ, 根拠 (file:line または実行したコマンドと出力), 提案}。所見ゼロの項目はゼロと明言。
```
## R3 出力 (逐語)
結論: **このままでは承認不可**です。指定された 6 数値自体は一致しましたが、期間表示・差分説明・比率の解釈・再導出手順・GO の provenance・実行証跡に 6 所見あります。

## 数値検算

| 値 | 検算結果 | 判定 |
|---:|---|---|
| `23030` | P3 掲載コマンド → `23030` | 一致 |
| `84.44%` | `19446 / 23030 * 100 = 84.437690%` | 丸め一致 |
| `0.7349` | `19446 / 26461 = 0.73489286` | 丸め一致 |
| `28967` | 現在 `main == 240d1cc` で P6 → `28967` | 数値一致、意味づけは所見1 |
| `1573` | Git blob の test 定義＋全 `parametrize` 静的展開 → `1573` | 一致 |
| `1976` | 同じ静的展開 → `1976` | 一致 |

P1/P5 の掲載コマンド自体も実行しましたが、この監査 sandbox は read-only のため次で停止しました。

```text
mktemp: failed to create directory ... Read-only file system
exit 1
```

代替の Git blob 直接解析結果は以下です。

```text
d4cbf91: test_defs=1260 WORKLOADS=3 EQUALITY_CHAIN_ADJACENCY=29 collected=1573 unresolved=0
240d1cc: test_defs=1498 WORKLOADS=3 EQUALITY_CHAIN_ADJACENCY=29 collected=1976 unresolved=0
```

現在の dirty tree を capture/cache 無効で収集すると `1978 tests collected`、作業差分は test 定義 `+3/-1 = +2` なので、clean `240d1cc` の `1976` とも整合します。ただし、文書が記す P5 の「pytest exit 0」は今回独立確認できていません。

## 所見1 — P6 は「7/14〜18」の値ではなく、差の説明も誤り

- severity: **high**
- 攻撃シナリオ: 読者が `28967` を同じ 7/14〜18 窓の更新値だと解釈し、7/19 の大量追加を過去の期間へ誤帰属する。さらに「丸め」「方法差」が `5937` 行差を生んだように見える。
- 根拠: [survey.md:42](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:42)、[survey.md:76](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:76)、[survey.md:86](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:86)。`d4cbf91..240d1cc` の寄与を展開すると、**すべて 2026-07-19 の 12 commit**で合計 `5937` 行。`28967 - 23030 = 5937` と完全一致した。明示的な 7/14〜18 窓では次の結果だった。

```text
git log --since='2026-07-14T00:00:00+09:00' \
  --before='2026-07-19T00:00:00+09:00' ... 240d1cc
23030
```

- 提案: `28967` を残すなら期間を「7/14〜19」に直し、差は「7/19 の後続 12 commit による `+5937`」と記す。7/14〜18 を維持するなら現基準値も `23030`。P6 の `main` は可動 ref なので `240d1cc` に固定し、日時にも `+09:00` を付ける。「丸め・clean commit・方法差」は差の理由から削除する。

## 所見2 — `23030` は純増ではなく累積 added-line churn

- severity: **medium**
- 攻撃シナリオ: 「約 `+23000` 行」をスイートの純増と読み、実際の規模増加を過大評価する。numstat の追加行合計は、同期間中に削除・再追加された行も数える。
- 根拠: [survey.md:9](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:9)、[survey.md:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:38)。同じ numstat を削除込みで集計した結果:

```text
added=23030 deleted=1501 net=21529
```

開始・終了 snapshot の diff でも `net=21529`。
- 提案: `23030` を「累積追加行 churn」と明記し、純増は `+21529` と併記する。feat 同梱率も「追加 churn の比率」と限定する。

## 所見3 — 「0.74 の帯に保たれた」は単一 aggregate に反し、実測でも不成立

- severity: **medium**
- 攻撃シナリオ: 全期間の加重 aggregate `0.7349` を時系列安定性と誤認し、commit ごとの大きな偏りを隠す。
- 根拠: [survey.md:9](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:9)。P4 と同じ定義を feat commit ごとに展開すると、例えば:

```text
0 / 71     = 0.0000   af829260...
238 / 122  = 1.9508   45bf232e...
3134 / 2489 = 1.2591  d4cbf91...
```

全体は `19446 / 26461 = 0.7349` だが、commit 別は `0.0000〜1.9508`。
- 提案: 「帯に保たれていた」を「期間 aggregate は `0.7349`」へ修正する。安定性を主張するなら、事前定義した日別／commit 別の帯と分布を提示する。

## 所見4 — P7/P8 掲載コマンドは表の値を再導出しない

- severity: **medium**
- 攻撃シナリオ: 再導出可能に見えるが、実際には無関係な C3 見出しを数え、C2 親裁定や施策 9 件を取りこぼす。`1/10/1`、`6/4`、`7/2` のどれも機械的に得られない。
- 根拠: [survey.md:43](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:43)、[survey.md:81](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:81)。掲載コマンドの実出力は、C2 見出し 10 件、C3 見出し 8 件、親表の C1/C3 行 3 件、計 21 行。C2 親表は `C2 #...` なので `C[123]-` に一致せず、施策表は別ファイルなので一行も対象にならない。
- 提案: P7 は初回 scan のコマンド・候補台帳と C1/C2 裁定表を別々に再導出する。P8 は本書の「施策 9 件」節を範囲指定して table row と裁定を数えるコマンドに差し替える。

## 所見5 — 「ユーザーの明示した GO」は事実を過大表現

- severity: **high**
- 攻撃シナリオ: 後続監査者が、この handoff 個別の着手条件をユーザーが明示的に免除したと誤認する。実際には包括的ループ指示を個別 GO と解釈して進めたプロセス逸脱である。
- 根拠: [survey.md:132](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:132)。handoff は「ループ実行指示を GO とみなし」と記録している一方、個別 GO は「提案・裁定待ち」としている。[handoff:8](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:8)、[handoff:13](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:13)。C3 も「ユーザー GO だけでは空ディレクトリ条件を満たさない」と明記する。[consultations.md:220](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-hygiene-consultations.md:220)
- 提案: 「ユーザーの包括的ループ実行指示を本 handoff の着手 GO と解釈した。個別の明示 GO ではない」と修正する。

## 所見6 — 実行証跡節が空で、完了証明がない

- severity: **high**
- 攻撃シナリオ: 新 assertion／負例が対象 mutant を本当に殺したか、別テストの失敗を誤帰属していないか、復元後 green か、最終全走が通ったかを検証できない。
- 根拠: [survey.md:135](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-suite-hygiene-survey.md:135) が EOF で、実行結果はゼロ。

```text
nonempty_lines_after_heading=0
```

C3 は `{nodeid, 壊した期待値, 期待した失敗, 復元後green}` の保存を要求している。[consultations.md:241](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-hygiene-consultations.md:241)
- 提案: red→green matrix、node-ID 集合差分、targeted/full run の node・コマンド・exit・件数を追記するまで文書を draft／未完扱いにする。

## 所見ゼロの検査項目

- **(3) 施策 9 件:** 所見ゼロ。実測 `total=9, adopted_or_conditional=7, rejected=2`。棄却は比率目標化とフル CI 化だけで、handoff の記述と一致する。[handoff:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-test-hygiene.md:22)
- **(4) 弱テスト 10 件:** 所見ゼロ。強化 `#4,#5,#6,#7,#8,#10`、変更不要 `#1,#2,#3,#9` で、C2 親裁定と番号・向きとも一致する。[consultations.md:286](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-hygiene-consultations.md:286)、[consultations.md:293](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/insights/2026-07-19_test-hygiene-consultations.md:293)
- **(5) insights 契約:** 所見ゼロ。`output/insights` は CCBench 還元候補だけでなく探索妥当性文書も許容し、「還元判断: ユーザー確認待ち」は CCBench バグを主張するときだけ必須。本件の内部監査・還元候補なしという分類は契約と矛盾しない。[output/README.md:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:47)、[output/README.md:61](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:61)、[output/README.md:63](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/output/README.md:63)

# 追補 2 (同日): 事前登録 mutant registry (逐語、実行ワーカー E2〜E5 起草)

レビュー R1 裁定後の親改訂: M2 は非判別 (第一失敗は既存 checksum アサート) と明示、M9 (env_tag 許可表混入) と M10 (返却 copy の bench_max_rounds 改変) を親が追加登録。matrix 実行は gen_S 計算ノード、判定 scope は対象 node 内。

## .exec-registry/E2.md
### orchestrator/tests/test_s8b_selector_freeze.py::test_selector_basis_preimage_is_versioned_and_backward_compatible

- 変異: `orchestrator/campaign/s8b_selector_freeze.py` の逐語
  ```python
  def selector_basis_sha256(freeze: Mapping) -> str:
      """floor/budget と独立な workload・binding・catalog 対応の versioned 部分 hash。"""
      return _canonical_sha256(selector_basis_preimage(freeze))
  ```
  を
  ```python
  _previous_selector_basis_sha256: str | None = None


  def selector_basis_sha256(freeze: Mapping) -> str:
      """floor/budget と独立な workload・binding・catalog 対応の versioned 部分 hash。"""
      global _previous_selector_basis_sha256
      current = _canonical_sha256(selector_basis_preimage(freeze))
      if _previous_selector_basis_sha256 is None:
          _previous_selector_basis_sha256 = current
          return current
      previous = _previous_selector_basis_sha256
      _previous_selector_basis_sha256 = current
      return previous
  ```
  へ置換し、直前呼び出しの結果を返す stale-cache を注入する。
- 期待: 単独 node 実行で、追加した `assert selector_basis_sha256(binding_changed) != baseline` が赤になる。既存の `selector_basis_sha256(binding_changed) != selector_basis_sha256(freeze)` を含む既存アサートと、追加した floor/budget の固定 baseline アサートは緑のまま。
- 復元: 上記の置換後 block を置換前 block へ逆置換する。

### orchestrator/tests/test_s8b_selector_freeze.py::test_selector_basis_preimage_is_versioned_and_backward_compatible

- 変異: `orchestrator/campaign/s8b_selector_freeze.py` の逐語 `return _canonical_sha256(selector_basis_preimage(freeze))` を `return _canonical_sha256(freeze)` へ置換し、floor/budget を selector basis hash に誤って含める。
- 期待: 追加した `assert selector_basis_sha256(floor_budget_changed) == baseline` が赤になる。既存の preimage checksum アサートと floor/budget の都度計算アサートも赤になる。
- 復元: `return _canonical_sha256(freeze)` を `return _canonical_sha256(selector_basis_preimage(freeze))` へ逆置換する。

## .exec-registry/E3.md
### orchestrator/tests/test_s8b_ratified_verify.py::test_transition_gn_to_gn1_allows_floor_change_unit
変異: `orchestrator/campaign/s8b_ratified_freeze.py` の `    "/floor", "/budget", "/floor_protocol", "/floor_source", "/measurement_closure",` → `    "/floor", "/budget", "/floor_source", "/measurement_closure",`
期待: `_TRANSITION_GN_TO_GN1` が裁定由来の必須 pointer 集合を含まなくなり、新しい部分集合 pin アサートのみが赤くなる。既存の遷移呼び出しは `/floor` と `/generation_number` しか変更しないため緑のまま、`/env_tag` 非包含 pin も緑のまま。
復元: `    "/floor", "/budget", "/floor_source", "/measurement_closure",` → `    "/floor", "/budget", "/floor_protocol", "/floor_source", "/measurement_closure",`

### orchestrator/tests/test_s8b_ratified_verify.py::test_manifest_mode_100755_accepted_when_g_h_worktree_match
変異: `orchestrator/tests/test_s8b_ratified_freeze.py` の `        target.chmod(target.stat().st_mode | 0o111)` → `        target.chmod(target.stat().st_mode & ~0o111)`
期待: manifest の fixture mode が `100755` ではなく `100644` になり、新しい `topology["mode_map"][topology["paths"]["manifest"]] == "100755"` アサートのみが赤くなる。validator は `100644` も合法として受理するため、既存の型アサートと新しい identity アサートは緑のまま。
復元: `        target.chmod(target.stat().st_mode & ~0o111)` → `        target.chmod(target.stat().st_mode | 0o111)`

## .exec-registry/E4.md
### orchestrator/tests/test_s8b_verdict.py::test_off_stock_check_rejects_non_static_default_decision_method

変異: `orchestrator/campaign/s8b_verdict.py` の `if row.get("decision_method") != "static_default":` を `if False and row.get("decision_method") != "static_default":` へ置換し、off arm の decision_method 検査 branch を無効化する。

期待: `decision_method="selector_agent"` の off row が拒否されなくなるため、新設する `test_off_stock_check_rejects_non_static_default_decision_method` の `pytest.raises(VerdictError, match="static_default")` のみが「DID NOT RAISE」で赤くなる。

復元: `if False and row.get("decision_method") != "static_default":` を `if row.get("decision_method") != "static_default":` へ逆置換する。

## .exec-registry/E5.md
### orchestrator/tests/test_s8b_oracle_manifest.py::test_run_contract_accepts_bench_max_rounds_one

変異: `orchestrator/campaign/s8b_oracle_manifest.py` の `return copy.deepcopy(dict(run_contract))` → `return run_contract`

期待: `validated is not source` の追加アサートのみが失敗し、`validated["bench_max_rounds"] == 1` は成功する。

復元: `return run_contract` → `return copy.deepcopy(dict(run_contract))`

### orchestrator/tests/test_s8b_oracle_manifest.py::test_snapshot_rejects_oracle_shared_false

変異: `orchestrator/campaign/s8b_oracle_manifest.py` の `if budget.get("oracle_shared") is not True:` → `if False:`

期待: `oracle_shared=False` が拒否されなくなり、この新設負例テストのみが `DID NOT RAISE ManifestError` で失敗する。

復元: `if False:` → `if budget.get("oracle_shared") is not True:`

### orchestrator/tests/test_s8b_oracle_manifest.py::test_snapshot_rejects_null_pair_with_nonnull_scalar_alt

変異: `orchestrator/campaign/s8b_oracle_manifest.py` の `elif scalar_alt is not None:` → `elif False:`

期待: pair に null を含み scalar_alt が非 null の相関違反が拒否されなくなり、この新設負例テストのみが `DID NOT RAISE ManifestError` で失敗する。

復元: `elif False:` → `elif scalar_alt is not None:`

