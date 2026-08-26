## 変更

- [acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-prereg-attainment/orchestrator/tests/acceptance_duration_ledger.json) に JUnit 由来の 1,786 entry を追加。
- `nodeid_count`: `15944` → `17730`
- JUnit の失敗 1 件は canonical 生成器の規則に従い除外。
- commit、`git add` は未実施。

## 実走結果

1. 指定テストは Pegasus の infrastructure failure で起動できませんでした。

   ```text
   Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
   IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
   ```

   rc=16、実走 nodeid 0 件です。通常実行、再試行、`--force-dispatch`、G5 単独実行のすべてで同じ結果でした。したがって全件緑とは報告しません。

   JUnit 集合との静的 join 結果は次のとおりです。

   ```text
   acceptance duration ledger coverage: 17698/17700 = 99.988701%
   ```

   これは `test_g5_...` の実走出力ではありません。

2. `--check` は想定どおり rc=1 でした。

   ```text
   acceptance duration ledger differs: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-prereg-attainment/orchestrator/tests/acceptance_duration_ledger.json
   excluded_failure_or_error=1
   ```

3. `git diff --stat`:

   ```text
    orchestrator/tests/acceptance_duration_ledger.json | 1790 +++++++++++++++++++-
    1 file changed, 1788 insertions(+), 2 deletions(-)
   ```

## 不変条件の確認

- 編集前の `HEAD` 辞書と比較:
  - 既存 entry: 15,944 件
  - 削除: 0 件
  - 既存値変更: 0 件
  - 追加: 1,786 件
- 既存 mapping の SHA-256 は前後とも `f39710ef7a4b5c1ccbefa57c3bc1a10a89644a119ee1f06a13358a49b4f7b6e0`。
- 素の writer nodeid は辞書 membership で不存在を確認。
- `@real-repo` 付き writer key は存在し、値は `0.19`。
- 追加キーと丸め値は JUnit から算出した期待集合と完全一致。
- top-level 順、内側キー昇順、2-space canonical JSON、末尾 newline を確認。
- `git diff --check` 成功。tracked 変更は台帳 1 ファイルだけです。

## 波及

- 所有外 caller: `orchestrator/tests/conftest.py` の台帳ロード、collection 並べ替え、controller-to-worker snapshot。
- 共有 fixture: acceptance collection 全体が conftest hook を共有するため、追加 nodeid が unknown cost から実測 cost に変わり、実行順が変わる可能性があります。
- consumer test: G5 の被覆 gate、G6 の writer pin・suffix fallback、G1/G7/G8 の loader・snapshot・ordering 契約。
- 受理集合、fixture 実装、consumer test、閾値、期待値には変更なし。

## 総括

台帳更新と静的不変条件検査は完了しています。ただし Pegasus の `qstat` preflight 障害により、指定テスト全件の緑だけは未確認です。親側で第 1 コマンドを再実走する必要があります。