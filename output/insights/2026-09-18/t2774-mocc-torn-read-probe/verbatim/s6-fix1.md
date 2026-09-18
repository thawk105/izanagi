## 総括

指定の2点のみ修正しました。

| 所見 | 判定 | 修正内容 |
|---|---|---|
| policy 参照 | closed | 任意の `--policy <abs>` を追加。既定は `mocc_trace_v1_policy.json`。実際の path／SHA256 を bindings に保存し、固定エラー文言を削除。`_load_policy` の RuntimeError はそのまま既存処理で記録 |
| verifier／discriminator 起動 cwd | closed | 両方とも `args.repo_root`。PYTHONPATH 注入を削除。他の env 項目は維持 |

- 変更：`probe/t2774_probe.py`（519行）
- SHA256：`77e8d3b16e3ec3504c3fa978ab8a35e136e60608de80e2545d8d86414bd56987`
- 指定コマンド実走：`selftest: PASS 10/10 cases`（rc=0）。期待値・件数・selftest 本体は変更なし。
- 構文確認：`ast.parse: PASS`
- 診断 patch：変更なし。dry-run は今回未実施（前段報告は rc=0）。
- 未実走：`run`、build、benchmark、実 trace の verifier／discriminator。
- 所有外への変更：無し。tracked 差分なし。禁止された Git 操作・文書作成なし。
