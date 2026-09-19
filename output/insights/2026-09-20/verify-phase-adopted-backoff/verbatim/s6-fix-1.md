## 総括

`probe/verify_phase_runner.py` のみ変更しました。

| 関数・変更後行範囲 | 差分の要旨 |
|---|---|
| `decide` 849–883 | SHA 検査に明示許可集合を追加。無指定時は従来の検査を維持 |
| `summarize` 935–1071 | 許可集合の適用、フェーズ別件数、top-level・候補別の3項目を追加 |
| `render_markdown` 1074–1088 | 同じ3項目を空集合も含め表示 |
| `selftest` 1091–1315 | 合成ケース7件追加。既存42件の期待値は変更無し |
| `ruling_sha` 1325–1328 | 小文字16進64桁の argparse 検証を追加 |
| `main` 1341–1379 | repeatable な `--accept-ruling-sha` を追加 |

変更後ファイルは **1384行**、SHA-256 は以下です。

```text
c960093de4206d8947b03097bb146ba9e4ee7b43ec6b974cee9d60a4b7609cd5
```

検証結果：

- `python3.10 -B probe/verify_phase_runner.py selftest`：**PASS 49/49**
- 指定の `ast.parse`：成功
- `summarize --help`：新オプションの表示を確認
- 不正SHAの argparse 拒否：6/6成功
- `git diff --check`：成功

変更関数は上表の6関数だけです。`decide` は SHA 検査のみ変更し、§4.1 の判定集合・anomaly・pass・indeterminate の条件は維持しました。走行経路、既存の会計・24枠・未完走集計も変更していません。

所有外への波及：**無し**。禁止された Git 操作は未実行。実走記録への `summarize` と job dir への書込みも未実行です。

親が実行するコマンド（修正版の絶対パスを使用、出力は新しいファイル名）：

```bash
python3.10 -B /work/1/SFC/tanab/izanagi/.codex/worktrees/vpab-author/probe/verify_phase_runner.py summarize \
  --input /work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/run \
  --output /work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/run/summary-B-fix1.json \
  --markdown /work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/run/summary-B-fix1.md \
  --accept-ruling-sha 2f9d8eb1e6520bb45cbb2eff76ede4286a23b39c29463cc50b18019ae97610cd \
  --accept-ruling-sha 1ddd2386ef1f4558077fffbef4bcab882205f955a5e4c8f9375d01b64cfd9201
```