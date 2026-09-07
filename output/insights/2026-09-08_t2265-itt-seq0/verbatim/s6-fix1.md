## 再導出した行番号

- `<module>._certify_main._build_trace_binary`: 3019
- `<module>.main`: 3387

`nl -ba` と `rg -n 'buildcache\.build'` で現物を確認しました。AST visitor は `buildcache.build(...)` の Call 行を採用します。該当呼出しは上記 2 箇所のみです。

## 直した箇所

`orchestrator/tests/test_ccbench_spawn_sites.py` の数値 4 箇所だけを変更しました。

- line 922: `3013 → 3019`
- line 934: `3382 → 3387`
- line 2679: `3013 → 3019`
- line 2683: `3382 → 3387`

ledger 本体と exact-set assertion は同じ 2 site を指しています。

## 変えていないもの

- ledger は 8 entry のまま。追加・削除なし
- `relative_path`、`owner`、`sink_kind`、`sink_scope`、`reason` は不変
- assertion、比較方向、許容範囲は不変
- 他ファイルの pin は不変:
  - `b10_backoff_shape_sweep.py`: 3294、4051
  - `paper_story_a1_paired.py`: 7146
  - `s8b_floor_campaign.py`: 4705、8632
  - `s8b_oracle_n_pilot.py`: 944
- 指定されたテストファイル以外のソースは編集していません。

## 実走

第一実走:

```text
python3 tools/run_tests.py orchestrator/tests/test_ccbench_spawn_sites.py
```

- rc: 16
- dispatch infrastructure failure: `qstat -Q preflight rc=1`
- child 未起動、テスト件数 0

fallback 実走:

```text
PYTHONPATH=. python3 /work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/orchestrator/tests/test_ccbench_spawn_sites.py
```

- rc: 0
- 実走 nodeid: `orchestrator/tests/test_ccbench_spawn_sites.py`
- 44 passed、0 failed
- 101.68 秒、serial
- 親が観測した赤 3 nodeid も全件に含まれ、赤は残っていません。

## 総括

- must-fix: 4 個の行番号 pin を現物に同期済み
- 未解決点: なし