# 段 4 裁定 — plan v2 (親)

基準 HEAD: `504ed6d` (local main を ff 取り込み済み)。

## 確定設計 (ユーザー裁定 2026-08-04、差し戻し不可)

非 UTF-8 の scoped blob は `items` から読み飛ばし、読み飛ばした件数を根に
`skipped_non_utf8` (整数) として出す。path 列は出さない。判定は strict UTF-8 decode 不能のみ。

## gate の署名 (DW-S04)

**禁止:** `build_inventory` は、`raw.decode("utf-8", "strict")` が `UnicodeDecodeError` を
送出する selected path **以外**を `items` から除外してはならない。suffix、path 名、
JSON / Python としての妥当性、NUL の有無、size を除外理由にしてはならない。
`skipped_non_utf8` は、その除外を行った path の件数と厳密に一致しなければならない
(kind filter 適用後の selected 集合の中で数える)。

**通る正例:** BOM (`EF BB BF`) 付きの `.json` は strict UTF-8 decode を通るため
`items` に残る (`artifact_format="json"`、marker は `_strict_json` の `bom-json` を
`_markers` が握るため `(None, None)`)。この item が消える実装は禁止に抵触する。

## 所見の裁定 (real/refuted、採用/不採用、scope)

### 採用 (plan v2 へ入れる)

| # | 所見 | 出所 | 対応 |
|---|---|---|---|
| 1 | counter が実 skip 数と無関係でも `5/1/4 → 6/1/5` を通過する | B | **同一 path の内容を非 UTF-8 ↔ UTF-8 へ変える差分検査**へ直す。selected の濃度を固定したまま count と membership が同時に変わることを要求 |
| 2 | zero case が未固定 | A | 全 selected が UTF-8 の repo で `skipped_non_utf8 == 0` を固定 |
| 3 | scope 外 / non-regular を数えない契約が未被覆 | A, B | scope 外の非 UTF-8 blob と in-scope symlink/gitlink を足しても count 不変を固定 |
| 4 | 全件非 UTF-8 の境界がない (`items` 空で rc=2 へ戻る変異が生存) | B | scoped file が全て非 UTF-8 の repo で rc=0 / `items == []` / `count == N` を固定 |
| 5 | NUL を binary 扱いする先例からの誤移植が生存 | A, B | strict UTF-8 として妥当な **NUL 入り** item が残ることを固定 |
| 6 | suffix 独立が 4 種でしか主張されていない | B | `.sh` (→ `artifact_format="shell"`) の非 UTF-8 insight cell を追加 |
| 7 | fixture の相関が強すぎる (全て `b"\xff\n"`、path 名が期待を露呈) | A | 不正 byte 列を cell ごとに変え、path 名から `non_utf8`/`utf8` を外す。direct test の非 UTF-8 cell は **PEP 263 の Latin-1 実行可能 source** にする |
| 8 | `docs/ruleops.md` の修正箇所が不足 | A, B | 「対象と inventory」を retained item 限定へ、lifecycle 段階 1・4 に警告、「既知限界」は全 kind の不完全性 + test kind 固有の解釈禁止 |
| 9 | D99 決定 (2) の外延と v2 の `items` が二義化する | B | decisions へ interface 追記を新規 D として記録 (段 7、spool fragment) |
| 10 | 起票予定 ID T-409/T-410 は使用済み | B | 採番しない。段 9 の land が lock 内で採番する |
| 11 | brief の母集団 1,659 件は insight 族のみ (全 scope は 1,783 件 / 44,994,296 bytes) | B | brief と worklog の記述を訂正 |

### 不採用 (scope 外の real 所見 — 実装せず起票)

| 所見 | real か | scope 外とする理由 |
|---|---|---|
| 当該 real-repo test が D63 canonical group 違反 (`real_repo` ≠ `real-repo`、decorator 使用) | real (両レンズ + 親が独立確認) | 本 wave の赤は決定的でこれに起因しない。D63 の競合閉包は同 decision が正本として管理する集合であり、変更は別裁定 |
| 収集監査 meta-test が kwargs 形の `xdist_group` を見逃す | real | 同上。族一般化は `DW-G03` の独立 2 例未達 |
| 許可 rc の Git stderr が非 UTF-8 でも検査されない | real | 本 wave の差分と無関係。受理集合の別課題 |
| direct test candidate の target 本文を `check` が decode しない (insight と非対称) | real | 同上。修正は `check` の受理集合を縮める別裁定 |
| mutation receipt の非 UTF-8 負例テストが無い | real | 差分が receipt 経路に触れない。ledger 負例が共通 `_strict_json` を既に固定している |
| `--kind test` の件数だけでは退役裁定に不十分 (対象特定ができない) | real | path 列を出さないのは確定裁定。診断経路の新設は別裁定 |

### nit (記録のみ)

- 「純粋な門番」は資源面では過言 (decode の allocation は残る)。
- 凍結 evidence の sha256 は post-hoc consumer に接続されていない。
- 歴史材料 (T-143 の insight) に旧 4-key shape が残るが、正本でないため編集しない。

## 変異事前登録 (DW-M01)

各変異は `build_inventory` の実装差分に位置し、手前に同じ入力を拒否する検査は無い
(scope・kind・regular mode・batch integrity・history は decode より前に済む)。
赤理由は各行 1 つに絞れる。受理集合を**拡大**する wave なので過剰拒否の正例
(M11 の全件非 UTF-8 で rc=0) も登録する。

| ID | 変異 | 期待 |
|---|---|---|
| M01 | decode 失敗時に `RuleOpsError("non-utf8")` を再送出 | KILLED (matrix 群が rc=2) |
| M02 | decode を見ず全 item を `continue` | KILLED (UTF-8 control 消失) |
| M03 | suffix `.raw` のときだけ skip | KILLED (非 UTF-8 の .py/.md/.json/.sh) |
| M04 | `scoped == "insight"` のときだけ skip | KILLED (direct test cell、kind test count) |
| M05 | skip するが counter を増やさない | KILLED (count 期待) |
| M06 | counter を kind filter 外まで数える | KILLED (all/test/insight の内訳) |
| M07 | counter を unique blob OID 数で数える | KILLED (同一 bytes を複数 path) |
| M08 | counter を `.raw` 件数で数える (payload を見ない) | KILLED (同一 path の内容差分検査) |
| M09 | NUL を含む valid UTF-8 も skip (先例からの誤移植) | KILLED (NUL control の保持) |
| M10 | scope 外の非 UTF-8 も counter に数える | KILLED (scope 外 control 追加で count 不変) |
| M11 | `items` が空になるとき rc=2 へ戻す | KILLED (全件非 UTF-8 repo) |
| M12 | `INVENTORY_SCHEMA` を v1 のままにする | KILLED (schema literal) |

## 実装 scope (段 5)

- `tools/ruleops.py`: `INVENTORY_SCHEMA` を v2 へ、`build_inventory` の decode 分岐を
  `counter += 1; continue` へ、根に `skipped_non_utf8` を常時出す。他は変えない。
- `orchestrator/tests/test_ruleops.py`: `_INVENTORY_ROOT_KEYS` の更新 (5 key)、
  三軸 matrix + 上記 1〜7 の境界テスト、`inspect` の非 UTF-8 fail-closed 負例。
- 親が別途書く: `docs/ruleops.md`、decisions fragment、worklog fragment。

実装子は docs を編集せず commit もしない。
