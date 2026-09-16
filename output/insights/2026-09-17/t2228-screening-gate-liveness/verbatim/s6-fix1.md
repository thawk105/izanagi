## 所見ごとの対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| A-R1 / B-R1 | closed | PBS_JOBID検査を削除。`mktemp -d` でscratchを確保し、失敗時rc=2。 |
| A-R2 / A-R4 | closed | 数値UIDで比較。root名前除外を廃止し、拒否対象からPID=2・PPID=2を除外。 |
| A-R3 / identity nit | closed | hostname・uid・PID・cwd・HEAD・pin・USER・HOMEを記録。開始日時は段頭で出力。 |
| B-R2 | closed | CLI argvに`-u`を追加。 |
| B 環境順序 should-fix | closed | PATH固定・unset群をPython選定前へ移動。 |
| B tree検査 nit | closed | 3検査それぞれのrcを出力。CLI rcを保持。 |
| A-R5 / B-R3〜R5 | partial | 指定の注記・検査rcを追加。README記載、終了後の再検査・証拠照合は親の責務として残る。 |

## 変更の要約 (行対応)

編集対象は [run_screening_liveness.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/output/insights/2026-09-17/t2228-screening-gate-liveness/launcher/run_screening_liveness.sh) のみです。

| 仕様 | 修正後の対応行 |
|---|---|
| 1. 前提検査・identity | 9–30（日時出力の定義は5） |
| 2. Python選定 | 46–57 |
| 3. 単独性観測・拒否 | 59–81 |
| 4. 環境供給・cleanup | 32–44、83–100 |
| 5. CLIを1回起動 | 102–108 |
| 6. 終了後検査・CLI rc保持 | 110–121 |

## 検査

- `bash -n`：成功（rc=0）。
- 行数：変更前117行 → 変更後121行（130行以内）。
- 変更前SHA-256：
  ```text
  66f28ca8a1b75e447252ddd1db2a62d201837424f3b43a492d7ceab5ff47557c
  ```
- 変更後SHA-256：
  ```text
  009a4d8a21c5d1c8694c40343b1079f286aa1bc6101cfa28f9f0ac95a48b888f
  ```

## 総括

指定されたlauncher修正を完了しました。**実走していない**ため、実行時の成立は未確認です。他ファイルの編集、commit、branch操作、job投入は行っていません。