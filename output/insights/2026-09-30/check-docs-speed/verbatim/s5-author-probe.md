## 作成した file

[wave-probe/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed-probe/wave-probe/README.md) に使用方法を記載し、[equiv_real.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed-probe/wave-probe/equiv_real.py)、[equiv_fixtures.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed-probe/wave-probe/equiv_fixtures.py)、[equiv_plugin.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed-probe/wave-probe/equiv_plugin.py)、[bench_abab.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed-probe/wave-probe/bench_abab.py) を作成しました。`wave-probe/_scratch/` は削除済みです。

## 各 script の引数と出力 JSON の形

3 つの実行 script は共通で `--src-repo`、`--old-commit`、`--new-checker`、`--scratch`、`--out` を取ります。既存の出力先は rc=2 で拒否します。

| script | 追加引数 | JSON の主な項目 |
|---|---|---|
| `equiv_real.py` | なし | 7 状態の `states[]`、旧・新の rc と stdout/stderr の hex、所見集合、`fault_reached`、一致判定 |
| `equiv_fixtures.py` | `--test-file`、`-k` | node outcome、checker 呼出し列、呼出し件数、先頭 20 件の差分 |
| `bench_abab.py` | `--rounds`、`--profile-new` | warmup・計測の `runs[]`、wall と peak RSS の集計、新旧中央値比、安定性判定 |

全体一致は rc=0、不一致は rc=1、実行不能は rc=2 です。

## 正規化規則

fixture 比較では clone の絶対 path を `<TREE>`、合成 repo と pytest の一時 root を `<ROOT>` に置換します。argv と stdout/stderr に適用し、文字列と bytes の型は区別して記録します。詳細な対象パターンは README に記載しました。

## smoke の実走結果

各 script の `--help` は rc=0、必須引数を欠く `--bogus` 呼出しは rc=2 でした。fixture の少数 node smoke は次の条件で実走しました。

```text
python3 wave-probe/equiv_fixtures.py --src-repo <現 worktree の絶対 path> --old-commit 4f412c67bcd7ff9cca1e78ce9bd1dd7a15d46037 --new-checker <現 worktree>/tools/check_docs.py --scratch <現 worktree>/wave-probe/_scratch --out <現 worktree>/wave-probe/_scratch/smoke.json --smoke-tree <現 worktree> -k 'test_synthetic_repo_baseline_clean or test_spool_guard_empty_layout_is_clean'
```

結果は **rc=0、2 node passed、checker 呼出し 2 件、差分 0 件**でした。

## 既知の限界

`Popen` の stdout/stderr を手動で読み、`communicate()` を使わず `wait()` だけを呼ぶケースでは、既に消費された出力を記録できません。7 状態比較、全 fixture、ABAB 計測は**実装済み・未実走**です。

## 総括

指定された 5 file を作成し、少数 node で記録と比較の動作を確認しました。本番の一致判定と速度・RSS の結果は、親による計算ノード実走で確定します。