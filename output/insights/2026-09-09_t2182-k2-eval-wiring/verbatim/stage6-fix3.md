## 足した nodeid と秒数

2,083 件を追加しました。全 nodeid と実測秒数は [acceptance_duration_ledger.json の 3〜2085 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2182-fix3/orchestrator/tests/acceptance_duration_ledger.json:3) に連続して記録されています。

- 既存値の変更: 0 件
- 削除: 0 件
- `0.0` の追加: 0 件
- 台帳件数: 20,042 → 22,125

## 更新後の被覆率

- `covered=22018`
- `total=22159`
- 正確な被覆率: `99.363690%`
- producer の `--coverage-against --check`: 成功（表示値 `ratio=0.994`）

## 実走結果

指定コマンドは実行しましたが、dispatch infrastructure 障害によりテスト本体は起動されませんでした。

```text
exit code: 16
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
child_started=false
```

したがって、状態は「実装済み・未実走」です。

## 総括

`--add-only` で JUnit 実測値のみを追加し、変更ファイルは台帳だけです。既存 entry はすべて維持し、commit は作成していません。