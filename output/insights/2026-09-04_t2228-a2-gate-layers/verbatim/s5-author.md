## 総括

- `test_condition_gate_family_real_records_positive_then_issued_red_negative` を追加しました。
- 実装済み・未実走です。指定 runner は dispatch 前に `rc=16` で停止しました。
- `git diff --stat`: test 1 file、365 行追加。production 差分はゼロです。

## 変更内容

- [test_paper_story_a2_certification.py:565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-a2-gate-layers/orchestrator/tests/test_paper_story_a2_certification.py:565)
  - 実 fixture と実 compiler で record を monkeypatch 前に生成。
  - 正例 2 genome の request、declaration、全 leaf 引数、呼出し順・回数、canonical receipts を検査。
  - 実 family による admission を独立計算。
  - issued-red 負例で family 拒否と driver の exact detail 伝搬を検査。

## 実走結果

実行コマンド:

```text
python3 tools/run_tests.py orchestrator/tests/test_paper_story_a2_certification.py -q -rf -k condition_gate
```

`qstat -Q` preflight が失敗し、`child_started=false`、`rc=16` でした。実走 nodeid はありません。

静的検査:

- AST parse: 成功
- `git diff --check`: 成功
- 結合文字 U+0300 から U+036F: 追加なし

## 波及の静的列挙

- production の driver、gate、受理・拒否挙動は変更していません。
- 共有 `_SUPPLIED` fixture と `condition_gate_test_support.py` は参照のみです。
- `test_condition_meaning_gate.py` と既存 consumer test への変更はありません。
- `backoff_sweep.py`、`backoff_repro.py`、`s1_direct_comparison.py` は同じ evaluator の静的 consumer ですが、各 driver 固有経路は未実測です。
- 既存 A-2 test、fixture、duration ledger、過去 4-cell 成果物への差分はありません。

## 未了・懸念

Pegasus dispatch 復旧後に指定 node 範囲の実走確認が必要です。現時点では緑または closed と申告しません。