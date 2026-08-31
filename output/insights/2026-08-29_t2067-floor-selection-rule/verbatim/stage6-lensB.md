静的レビュー結果は must-fix 1 件です。pytest は実走しておらず、緑とは判定しません。`git diff --check` と変更 6 file の `ast.parse` のみ成功を確認しました。

## 変異事前登録の実在確認

裁定 7 節の 8 変異は、production の変異位置と、それを殺すテストがすべて存在します。

| id | production 位置 | KILL テスト | mask 判定 |
|---|---|---|---|
| `min-to-max` | [`min(...)`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_holdout_freeze.py:1858) | [`[min-to-max]`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_holdout_freeze.py:1945) | なし。mutant は selected B を選んで受理し、`pytest.raises` が赤になる |
| `drop-candidate-selection` | [candidate からの呼出し](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_holdout_freeze.py:1958) | 同じ `[min-to-max]` node | なし。呼出し削除で candidate が受理される |
| `drop-launch-selection` | [`LaunchValidatedFreeze` 分岐](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_ratified_freeze.py:3303) | [`test_launch_validate_rejects...`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_ratified_verify.py:854) | なし。loader は selection を検査せず、`calls` で到達も確認 |
| `drop-loader-projection` | [投影 equality](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_ratified_freeze.py:1056) | [`test_loader_rejects...`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_ratified_freeze.py:1477) | なし。exact reason/cause まで検査 |
| `use-reported-eligible` | [derived bit の取得と使用](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_holdout_freeze.py:1835) | [helper の実導出テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_holdout_freeze.py:1892)と[`[use-reported-eligible]`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_holdout_freeze.py:1945) | exact mutant は殺せる。ただし統合テスト側は導出を stub |
| `drop-cert-time-binding` | [certificate 検証](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_holdout_freeze.py:1654) | [`test_v2_candidate_rejects_selected_certificate...`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_holdout_freeze.py:2028) | なし。既存 candidate gate は certificate を読まない |
| `underivable-to-skip` | [例外の fail-closed 化](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_holdout_freeze.py:1852) | [`test_v2_candidate_fails_closed...`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_holdout_freeze.py:1983) | wrapper mutant は殺せる。ただし実 admission 破損ではなく例外 stub |
| `historical-policy-leak` | [`result_type is LaunchValidatedFreeze`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_ratified_freeze.py:3303) | [`test_historical_reverify...`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_ratified_verify.py:872) | なし。Reverified へ漏らすと incomplete earlier が fail-closed で拒否される |

正例は次の状態です。

- `positive-single-run`: [`test_v2_candidate_build_and_generate_synthetic_g1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_holdout_freeze.py:1797) が public candidate builder を実際に通す。実効性あり。
- `positive-resumed-earlier`: 名前上のテストは存在するが、裁定どおりの入力は実在しない。詳細は must-fix。

## テストが機構を通っているか

loader projection、certificate binding、single-run、historical reverify は production entrypoint と production predicate を実際に通しています。

candidate/launch の selection テストは、列挙、identity 比較、public entrypoint は実体ですが、earlier の admission 導出をすべて monkeypatch しています。

- eligible negative: [`_derive_floor_selection_eligibility` を True stub](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_holdout_freeze.py:1963)
- underivable negative: [例外 stub](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_holdout_freeze.py:1991)
- resume positive: [False stub](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_holdout_freeze.py:2014)
- launch negative: [True stub](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_ratified_verify.py:860)

したがって、選択層と admission 導出層の単体テストはあるものの、両者を結ぶ引数配線は未検証です。例えば earlier に selected の `path_info` を誤って渡す変異は、現在の分割テストでは生存できます。

## 負例の先取り

candidate の検査順は、既存資格検査、certificate、selection、closure の順です。[`build_v2_g1_candidate`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_holdout_freeze.py:1948)

- selection 負例は selected B 自体が既存資格検査と certificate を通る。`observed` に earlier path が入るため selection 到達も確認できる。
- certificate 負例は certificate の時刻だけを変えており、既存資格検査には先取りされない。
- loader projection 負例は新設 equality の exact reason/cause を確認しており、transition gate に先取りされない。
- launch selection 負例は selected artifact の既存 full validation 後に selection が呼ばれ、stub の呼出し記録も残る。
- underivable 負例は既存 gate には先取りされないが、「admission evidence を壊す」という裁定入力を作らず、例外を直接 stub している。

既存 gate に先取りされて証拠にならない負例はありません。ただし underivable の実入力耐性は未証明です。

## 正例の実効性

`positive-single-run` は有効です。single-run の production builder を通り、candidate の生成まで確認します。後発 artifact を過剰拒否しない正例も [`test_v2_candidate_ignores_later...`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_holdout_freeze.py:2077) にあります。

`positive-resumed-earlier` は無効です。

- earlier helper は [result.json だけを複製](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_holdout_freeze.py:1856)し、manifest、journal、resume admission evidence を作らない。
- positive は earlier の reported bit を True のままにして、[導出結果だけ False に stub](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_holdout_freeze.py:2005)している。
- [resume 導出の実テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_holdout_freeze.py:1908)は別 node であり、earlier run ではなく selected run の evidence を改変して private helper を直接呼ぶだけである。

これは、裁定が要求した「resume 由来 earlier が存在しても later candidate を受理する」正例ではありません。

## inventory / meta-test の追随

静的には inventory 更新を要する差分は見つかりませんでした。

- `test_official_perf_closure.py`: 両 production file は既に reviewed inventory にある。[inventory](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_official_perf_closure.py:44) 新関数は tracked perf call を増やしていない。
- `test_s8b_protocol_builder.py`: [`FLOOR_PROTOCOL_REL` の exact-one 内容 pin](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_protocol_builder.py:1228)は不変。
- `test_frozen_artifacts.py`: hash pin は [output artifact](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_frozen_artifacts.py:41)だけ。output 差分は 0。
- `test_s8b_repo_scan_invariant.py`: production scanner を通すが、新規文字列に rr20/rr80 の三軸 conjunction はない。[検査本体](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_repo_scan_invariant.py:27)
- `test_campaign_import_invariant.py`: 全内容を AST 走査する。[走査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_campaign_import_invariant.py:1002) 新規 import はすべて相対 import で、新 exception は不要。
- `test_hold_inventory.py`: completeness は registered layers only であり、新規通常 test は inventory 対象ではない。[契約](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_hold_inventory.py:444)
- その他、process-spawn exact inventory と campaign driver AST inventoryも確認した。新関数は process launch や `run_campaign` callsite を追加していない。

acceptance duration ledger には新規 11 test function、parametrize 展開後 13 nodeid がすべて未登録です。ただし契約は exact coverage ではなく [実 collection の 90%以上](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_acceptance_schedule_order.py:660)です。したがって未登録自体は違反ではありません。現在値が閾値を維持するかは live collection が必要であり、本レビューでは緑を主張しません。

## 共有 fixture の波及

`s8b_v2_freeze_fixture.py` の直接 import は次の 4 file です。

- [`test_s8b_holdout_freeze.py:26`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_holdout_freeze.py:26)
- [`test_s8b_oracle_driver.py:63`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_oracle_driver.py:63)
- [`test_s8b_oracle_manifest.py:26`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_oracle_manifest.py:26)
- [`test_s8b_oracle_report.py:28`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/test_s8b_oracle_report.py:28)

変更された certificate は [`candidate_repository`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/tests/s8b_v2_freeze_fixture.py:367)内だけで使われ、この factory の caller は `test_s8b_holdout_freeze.py` に限られます。他の 3 file は変更されていない `fill` / `per_pair_floor` だけを利用するため、certificate 変更の直接波及はありません。

ratified fixture 側の floor 投影変更は、`test_s8b_ratified_verify`、oracle driver/report が共有する production-emitter builderにも追随済みです。未修正の別 g1 手組み fixture は静的検索では見つかりませんでした。

## 過剰実装の混入

禁止された機構の混入はありません。

- 署名、nonce、新しい一回性台帳、予約、墓標: なし
- 新 schema / artifact key / CLI: なし
- 版文字列 scan: なし。規則版は error detail/cause にだけ使用
- namespace 全体一致: なし。[selected より早い時刻だけを列挙](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-floor-selection-rule/orchestrator/campaign/s8b_holdout_freeze.py:1739)
- `EQUALITY_CHAIN_ADJACENCY`、凍結 output、docs、external の変更: なし
- admission 台帳は既存 inspector の再利用であり、新しい台帳ではない

## must-fix / should-fix / nit

must-fix:

- `positive-resumed-earlier` と実 admission 破損負例を、result-only fixtureと `_derive_floor_selection_eligibility` stub で代用している。full earlier artifact、resume 由来 admission evidence、manifest、journal を作り、production candidate builderを stub なしで通す必要がある。同じ fixture で fresh eligible、resume ineligible、破損 underivable、current launch の各経路も通すべき。
  - 成果物影響: D1124 の再発防止と earlier admission 配線が機械証明されず、resume 後の正当な later candidate を拒否する退行が緑のまま land し得る。

should-fix:

- `drop-candidate-selection` は `[min-to-max]` node に相乗りして殺せるが、事前登録 ID が node 名やコメントに現れない。変異台帳との機械的な対応を明示すると追跡性が上がる。
- 新規 13 nodeid の duration は未登録である。これは直ちに契約違反ではないが、親の実走後に coverage 実測と ledger 更新要否を判断すること。

nit:

- なし。

## 総括

8 変異の実装位置と exact mutant を殺すテストは確認でき、既存 gate に先取りされた負例もありません。loader projection、certificate binding、historical/current 分離、single-run、後発 run 非過剰拒否は静的に妥当です。

ただし、裁定が最重要正例とした `positive-resumed-earlier` は実際の resume earlier を作らず、導出 bit の stub で代用しています。段 5 報告の「resume earlier を記述した」という主張は、機構を通るテストとしては成立しません。この must-fix を解消するまで、段 6 レンズ B の検証は未充足です。