## 総括

- 恒真だった repetition 検査を境界値と対応関係の検査へ強化しました。
- 編集は所有対象のテストファイル 1 件のみです。
- production、docs、git index、commit は変更していません。

## 直した assertion

[test_s8b_floor_campaign.py:14985](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix4/orchestrator/tests/test_s8b_floor_campaign.py:14985)

- 最初の round と最後の round を明示的に選択。
- 15013 行で repetition `0` の存在を検査。
- 15014 行で repetition `n_sessions` の不存在を検査。
- 15019 行の `assert repetition == row["round"] - 1` により、両端の round を 0 始まりへ対応づけています。

## 強化後に変異が赤になることの実測

一時変異:

```python
repetition=round_no - 1,
```

を次へ変更:

```python
repetition=round_no,
```

実行 command:

```bash
PYTHONPATH=. PYTEST_ADDOPTS='-k test_registry_plan_maps_round_to_zero_based_repetition' python3 orchestrator/tests/test_s8b_floor_campaign.py
```

結果: `0 passed, 1 failed, 510 deselected`、終了 code 1。`assert 0 in planned_repetitions` で発火しました。

変異を復元後、同 command は `1 passed, 0 failed, 510 deselected`。production の `git diff` は `0` 行です。

## 実走結果

```bash
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_campaign.py
```

結果: `508 passed, 0 failed, 3 skipped`、終了 code 0。

`git diff --check` も終了 code 0 です。

## 残った懸念

なし。最終差分は `orchestrator/tests/test_s8b_floor_campaign.py` のみです。