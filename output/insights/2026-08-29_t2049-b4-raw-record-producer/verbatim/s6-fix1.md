## 直したもの

- [test_p3_b4_raw_record_producer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix1/orchestrator/tests/test_p3_b4_raw_record_producer.py:72)
  - off campaign の v1 lock を、environment contract、activation tuple、captured loader binding を持つ v2 lock に変更。
  - `encode_campaign_lock_v2()` と `CampaignLockAuthority` を使用し、production と同じ authority 形を生成。
- [test_p3_b4_raw_record_producer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix1/orchestrator/tests/test_p3_b4_raw_record_producer.py:660)
  - 2 本の 201-block test から未登録の `slow` marker を除去。静的走査で残存 0 件。
- production producer は段 5 成果物から変更していない。commit、add、stash、branch 操作も未実施。

## 根本原因の確認

親の診断は正しかった。

on campaign は共有 fixture が v2 lock を生成していた一方、off campaign を複製する `_copy_precursor_with_writers` だけが identity preimage を直接 `wal.write_lock()` に渡し、v1 lock を生成していた。

そのため off critic の `CERTIFIED_ACCEPTANCE` が authority 不在を E0、`v1-authority-absent` と判定して拒否していた。21 件すべてがこの共有経路を通るため、単一根本原因という診断とも一致する。

## 実走した検査

指定された全 file 走を実行した。

```text
python3 tools/run_tests.py orchestrator/tests/test_p3_b4_raw_record_producer.py -q
```

結果は rc=16。`qstat -Q` が `Unknown user-id` を返し、`child_started=false` だったため pytest node は実行されていない。

- 実走範囲指定: test file 全体
- pytest 緑: 0
- pytest 赤: 0
- pytest error: 0
- infrastructure failure: 1
- 未実走: 22 node

したがって修正後の緑は未確認であり、緑とは申告しない。runner が作った今回分の dispatch 診断 directory は内容確認後に除去し、`output/` に変更を残していない。

静的検査結果:

- production/test 2 file の AST parse: 2 passed
- U+0300〜U+036F: 0 件
- test node: 22 件
- `slow` marker: 0 件
- production file: 段 5 成果物と byte 一致
- tracked file の差分: なし
- untracked file: 許可された段 5 成果物 2 file のみ

## 変異 M01〜M18 の node 対応

変更なし。M01〜M18 の node 名、18 件の一対一 mapping、各 test の期待値を維持している。test の削除、skip、xfail、期待値変更は行っていない。

## 受理集合の変化

production の受理・拒否集合は変えていない。

fixture 内では次のように変化した。

- 修正前: off campaign が v1 authority 不在となり、certified read は必ず E0 拒否。
- 修正後: off campaign も正式な v2 authority を持ち、記録 closure と activation tuple の既存検査を通過できる。
- authority 不正、closure 不整合、activation 不整合に対する既存拒否はそのまま。
- `HISTORICAL_RAW` への変更や epoch gate の迂回は行っていない。

marker 除去は受理集合に影響しない。

## 波及可能性

- 変更した helper はこの新規 test file 内だけの private fixture。
- production caller、consumer、共有 fixture、既存 test の期待値には変更なし。
- v2 fixture は production と同様、current activation state と enforcement closure を取得できない環境では fail-closed になる。
- 201-block 正例も同じ helper を反復利用するため、修正後の全走確認は queue 認証復旧後に必要。

## 総括

fixture の v1 lock を正式な authority 付き v2 lockへ修正し、未登録 marker も全除去した。親が特定した単一根本原因には対処済みだが、指定 runner が infrastructure rc=16 で子を起動できなかったため、修正後の 22 node 緑確認だけが未完了である。