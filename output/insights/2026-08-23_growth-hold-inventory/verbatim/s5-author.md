裁定どおり実装しました。ただし Pegasus の実行基盤障害で指定 pytest は child 未起動のため、`closed` とは申告しません。

## 受理・拒否挙動

変更前は 16 function、parametrize 展開後 20 item が既定で skip され、正確な opt-in token の場合だけ実行されました。

変更後は 14 function、18 item が既定実行へ戻ります。次の 2 件だけが引き続き既定 skip です。

- `test_forbidden_commits_are_unreachable_in_both_cases`
- `test_parent_numstat_controls_remain_pinned`

不正な token は引き続き拒否されます。また 2 件が残るため、plain import に対する module-level guard も維持されます。

prompt replacement test は、再帰的 `_find_rollout` から固定 `_REAL_ROLLOUT` 参照と POS SHA 検証へ変わりました。

## 実装範囲

- [growth_test_holds.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/growth_test_holds.py:108)
  - 14 hold 行を削除
  - 2 行を維持
  - 未参照となった reason 定数 2 個を削除
  - 両入力軸、call 秒、D451 非該当、防壁 node、canonical sentinel を個別 reason に記録
- [test_codex_reasoning_ab.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_codex_reasoning_ab.py:6105)
  - `_REAL_ROLLOUT` 直接参照と `_verify_rollout_sha(..., "POS")` に置換
- [test_growth_test_holds_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_growth_test_holds_contract.py:43)
  - 指定された 3 定数だけを更新
  - count: `45`
  - key SHA: `5a5f7a4f918684cbde6b9267d5535455974d441fa847ab8f070cc8b2e77d3429`
  - row SHA: `8cf20b5f685a38bd9aee4e306792a509d5ebc0314a436a1e16c0fc129466d945`

commit、stage、docs 編集はしていません。変更 path はこの 3 ファイルだけです。

## 検査結果

事前指定した期待赤集合は空集合でした。

- `orchestrator/tests/test_growth_test_holds_contract.py` 全体
  - `tools/run_tests.py` 経由で試行
  - `qstat -Q preflight rc=1`、child 未起動、`rc=16`
  - 実装済み・未実走
- `test_codex_reasoning_ab.py::test_prompt_replacement_count_zero_expected_and_excess`
  - `[0, 9, 10]` の 3 item 範囲
  - 同じ dispatch 障害で child 未起動、`rc=16`
  - 実装済み・未実走
- 指定 inventory import probe
  - 実走成功
  - `count=45`、新 key SHA を出力

追加の軽量検査は成功しました。

- registry 差分: `removed=14 / added=0 / reason-only changed=2`
- sentinel 2 件: compact、sorted-key、ASCII JSON と一致
- 残存 `test_codex_reasoning_ab.py` hold 数: `2`
- 固定 `_REAL_ROLLOUT` の POS SHA 検証: 成功
- 3 pin の独立再計算: 一致
- 3 ファイルの AST parse: 成功
- `git diff --check`: 成功

## 静的波及

- [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/conftest.py:874): collection skip、summary、complete-collection 検査は registry を動的参照します。14 件が既定実行へ移る意図した変化です。
- `enforce_held_functions`: 対象 file に 2 件残るため zero-hold `ValueError` は発火しません。他の guard 利用 12 module も残存数 `1–11` で不変です。
- 共有 `benchmark_snapshots`: 再導入 14 件中、M2 と prompt replacement を除く 12 件が consumer です。
- [hold_inventory.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/tools/hold_inventory.py:81): count、digest、holds を動的出力するため `45` へ追従します。
- [test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_real_repo_serialization.py:1211): 12 fixture consumer は独立した real-repo serial 集合に残ります。payer/memo の hold subset 契約は今回の削除対象を含みません。
- `test_pytest_collection_config.py`: synthetic registry を monkeypatch する consumer で、今回の件数変更に非依存です。
- 回帰 finding: [test_hold_inventory.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-growth-hold-inventory/orchestrator/tests/test_hold_inventory.py:44) が旧 59 件と旧 reason を hard-code しています。14 stale extra と残存 2 件の reason mismatch があり、この consumer test は赤になる見込みです。許可 path 外なので編集していません。

## 総括

編集 3 点は裁定どおり実装済みです。inventory probe、registry 差分、pin、sentinel、固定 rollout SHA、構文、diff 検査は成功しました。指定 pytest 2 範囲は Pegasus dispatch infrastructure failure により実装済み・未実走です。静的 consumer は全列挙し、zero-hold 問題なしと、所有外 `test_hold_inventory.py` の hard-coded expectation 回帰を確認しました。