## 総括

`probe-t2700/t2700_ab_analyze.py` のみ修正しました。

- 両 request の shard 引数の存在・一意性・一致検査を維持。
- `repo_root` の必須・一致検査を request.json 側だけに限定。
- request.json の bytes の SHA256 と receipt／result のハッシュを照合。不一致は `artifact`、理由は `request binding hash mismatch`。
- 合成 request を実物の key 構成に更新。

`python3 probe-t2700/t2700_ab_analyze.py --selftest` を実走し、**PASS、rc=0**。内部の `--check-run` で実物形の受理、request.json の `repo_root` 欠落・不一致、receipt／result のハッシュ不一致の拒否を確認しました。既存の統計反例・系列検査も PASS です。

実 run は未実走。所有外編集・docs 編集・commit・git 操作は行っていません。