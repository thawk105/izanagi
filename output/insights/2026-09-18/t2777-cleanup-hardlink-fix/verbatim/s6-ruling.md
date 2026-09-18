# 段 6 裁定 (レビュー A / B の所見) — [T-2777] (2026-09-18 11:40 JST、親)

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A1 | ref 名 `objects/ab/<38hex>` (合法、`check-ref-format` rc=0) の loose ref `modules/sub/refs/.../objects/ab/<38hex>` とその reflog `logs/refs/.../objects/ab/<38hex>` が object 名前形に一致し、registry file の hardlink を受理する | **real / must-fix** | 採用。段 4 で親が「害は無い」と見送った点を、不変条件 (i) (`refs`/`logs` は registry) との衝突として是正する |
| A2 | `objects/info/*`、`multi-pack-index` 等は False のまま rc=20 (nit、裁定どおり) | real / nit | 変更なし。限界として insight に書く |
| A3 | 入口真理値表・stable の保証 (既裁定) | refuted / nit | — |
| A4 | 6 呼出し・semantic・marker・撤去範囲は維持 | refuted | — |
| A5 | 負例 4 case は単一理由、`GIT_OPTIONAL_LOCKS=0` は拒否を迂回しない (index を比較対象に残す点で代替より強い) | refuted | 維持 |
| A6 | synthetic 正例の限界 (live 未確認、nit)、既存 assertion 削除 0 行、pin 維持 | real / nit・refuted | 段 9 で live 実測 |
| B (全項) | prefix / race / recovery / M0〜M4 完全集合 / M1 到達性 / 所要 | refuted (GO) | — |
| B nit | 旧 M1 (`return parts[0] == "modules"`) を登録に持ち込まない | real / nit | M1 = `return True` |

## fix 1 の仕様 (A1)

- `_is_shared_object_path`: ref 名は任意階層 (`refs/heads/objects/ab/<hex>` = branch 名 `objects/ab/<hex>`) なので、**`modules` と末尾 3 component (`objects/<fanout>/<name>` または `objects/pack/<name>`) の間の component に `refs` または `logs` が 1 つでもあれば False**。実装は `not ({"refs", "logs"} & set(parts[1:-3]))` 相当の 1 節を既存の and 連鎖に足す (M5 の anchor になるので、独立した式として書く)。
- 帰結: submodule の path 自体が `refs` / `logs` を component に持つ場合 (例: path `refs/x`) の真の store も False → rc=20 (拒否側 = 安全方向)。git が作る `refs/**`、`logs/refs/**`、`worktrees/<wt>/refs/**`、`worktrees/<wt>/logs/refs/**`、入れ子 submodule の `refs`/`logs` はすべて除外される。
- 負例 2 case 追加 (`test_admin_nonobject_hardlink_is_rejected` の parametrize に足す、各 1 理由): `ref-shaped-object` = `modules/sub/refs/heads/objects/ab/<38hex>` (内容 40hex + 改行)、`reflog-shaped-object` = `modules/sub/logs/refs/heads/objects/ab/<38hex>` (内容は reflog 行 1 本)。既存 `ref-named-objects` (`refs/objects/topic`) は残す。全 6 case で CLI rc=20・無変異・alias 不変。
- 変異 M5 (negative / KILLED): 上記の除外節を恒真化 (例: `not ({"refs", "logs"} & set(parts[1:-3]))` → `True`) → 2 新規 case が KILL。M1 (`return True`) は 6 case を KILL。M0/M2/M3/M4 は不変 (anchor は fix 後に再検証、DW-M07)。
- 既存テストの期待値変更・反転・緩和・skip・削除は禁止。赤なら実装側が誤り。
