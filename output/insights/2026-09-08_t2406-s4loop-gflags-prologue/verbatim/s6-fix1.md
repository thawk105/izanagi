## 変更した行範囲

[契約テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2406-fix1/orchestrator/tests/test_p3_s4_loop_job_contract.py:54) の以下を変更しました。

- 54–56: コメント専用行の偽 heredoc opener を無視
- 359–367: コメント専用行を除いた raw source で required fragment を再照合
- 387–434: `CMAKE_PREFIX_PATH` exact 3 行と prebuild → driver 順序を検査
- 783–869: 指定された負例 6 関数を追加

差分は 114 行追加、3 行削除です。

## 各所見 (A-1a / A-2 / A-3 / B-1) の対応 (closed / partial)

- A-1a: closed
  - コメント専用行では heredoc opener を探索しません。
  - heredoc 内部の終端判定は維持しています。
- A-2: closed
  - 実行面の `CMAKE_PREFIX_PATH` 出現行を、指定された exact 3 行・出現順に限定しました。
  - `export -n`、`env -u`、追加 unset などを同一署名で拒否します。
- A-3: closed
  - prebuild 呼出しが driver 2 出現の両方より前であることを検査します。
- B-1: closed
  - `job-body-comment` を除く required fragmentを、通常コメント専用行を除いた raw sourceでも検査します。
  - PBS 指令は scheduler 上の有効行として保持しています。

## 直接呼出しによる検査結果

pytest runner は実行していません。モジュールを import し、以下を直接呼び出しました。

- 指定正例 3 件: すべて通過
- 新設負例 6 件: すべて通過
- 全 parametrize 45 ケース: すべて通過
  - registered fragment mutants: 24/24
  - shim mutants: 8/8
  - CMake environment mutants: 9/9
  - submitter forms: 4/4
- registered fragment mutants は全ケースで最初の欠落 label が指定どおり 1 件でした。
- 新規検査をメモリ上の variant から一時除去すると、対応する負例 6 件すべてが `DID NOT RAISE AssertionError` になりました。
- `git diff --check` も通過しました。

## 波及

変更は契約テスト 1 file のみです。job body、docs、registry、production caller・consumerへの変更はありません。生成された一時 bytecode も残していません。

## 総括

4 所見はすべて closed です。契約テストは実装済みですが、指定どおり pytest および job body の実走は未実施です。検証結果は直接呼出しによるものです。