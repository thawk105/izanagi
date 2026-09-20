## 総括

**v5 への修正完了。** [probe/verify_phase_runner.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2807-author/probe/verify_phase_runner.py) だけを編集し、未コミットの差分を残しました。禁止された Git 操作は実行していません。

| 分類 | 対応・改版後の行番号 |
|---|---|
| (a) bench 失敗 | 終端・skip。bench 再生成なし。L361–362 |
| (b) verifier 完走済み／起動済み | skip。再検証は引き続き `reverify` が担当。L364–365 |
| (c) 保全済み・verifier 未開始 | 既存 `restore` で展開・SHA256／bytes 照合後、再構築 checkout の identity を確認して1800秒で初回検証。同じ attempt-1 を更新し、bench 記録は保持。`resumed_verifier`・`resumed_at` を記録。L373–375、L694–741、L990–993 |
| (d) bench 完走・保全未完了 | `trace_missing` として終端。既存の規約不適合集計で開示し、再走しない。L366–372 |

`reverify` の拒否条件は維持し、未開始の場合は `verify --resume` を案内します（L836–837）。`decide`／`summarize`、P10／P11、hard timeout の3600／1800／3600秒は変更していません。

改版後は **2103行**。SHA-256:

```text
4ff6652a365b952cba4deb23e2ae910ba863dabba4a107503c641c7a36863430
```

検証結果:

- `python3.10 -B probe/verify_phase_runner.py selftest`: **rc=0、`selftest: PASS 166/166 cases`**。指定ケースを4分類へ変更し、復元・起動の spy、bench 不変、attempt-1 判定集合への反映を確認。その他の既存期待値は変更なし。
- AST 構文確認: **PASS**。
- `prerun / calibrate / verify / reverify / summarize / selftest --help`: **6件すべて rc=0**。
- `git diff --check`: 問題なし。変更は対象1ファイルのみ。

**未実走:** build、bench、実 verifier、実 trace の圧縮・復元、計算ノードでの再開経路。今回の再開検査は合成 record と callback／spy によります。

**規則からの逸脱:** なし。