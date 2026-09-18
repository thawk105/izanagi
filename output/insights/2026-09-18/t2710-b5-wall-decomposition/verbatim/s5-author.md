## 総括

作成したファイルは以下の3本です。すべて untracked、tracked file の差分はありません。

| ファイル | 行数 |
|---|---:|
| [t2710_probe_plugin.py](probe-t2710/t2710_probe_plugin.py) | 457 |
| [t2710_probe_runner.py](probe-t2710/t2710_probe_runner.py) | 453 |
| [t2710_probe_analyze.py](probe-t2710/t2710_probe_analyze.py) | 470 |

- **selftest：45/45 件 PASS、rc=0。** held module の import、pytest session の生成、M の実行はしていません。
- **構文確認：3本とも `ast.parse` 成功。**
- env 定数の実在確認：`IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1`。
- conftest の実在確認：台帳 attr **1005行**、初期配布数 **1014行**、scope 関数 **1704行**、duration 関数 **1732行**。

実物への plugin 設置、xdist の B/C 動作、計算ノード runner、実測成果物の集計は **実装済み・未実走** です。合成 callable・item・controller／spans／JUnit による検証は通過しました。

親が compute で最初に確認する点：

- 実行対象 M の各 node に `helper` があり、`verify` が対象の呼出し回数に対応すること。single-defects は **5/2/2/1回**を確認してください。
- B の `controller.json` で全 worker の `intended_matches=true`。初期相方の予測・実行列・3個目以降を集計結果で確認してください。
- `record-error`、未完走、B の実現不能がないこと。検出した走は集計から除外します。

**設計上の補足・差分：** `close` は既に atexit に bound method として登録されるため、class 属性の wrapper 設置に加えて、その callback を一度だけ再登録しています。元 callable は一度だけ呼びますが、他の終了 callback との相対順は変わります。また観測範囲は M を実行した worker です。分割 model の変異処理とその他残差は未分離、overhead の H は単価からの近似値として明記しています。