# 段 4 裁定 — T-2412

## 採る設計 (plan v2)

段 2 plan の中核をそのまま採る。

- `provenance.source_commit` の意味を「spec を含む commit」から「spec 凍結時の code state =
  spec だけを足す freeze commit の**唯一の親**」へ変える。
- loader は `parents(loaded_head) == (source_commit,)` と
  `changed_paths(source_commit, loaded_head) == (spec の relpath,)` を要求する。
  merge commit は親が複数なので拒否される。
- spec の bytes 一致検査と `expected_sha256` 検査は一切緩めない。
- 実行時 (`2175-2183`) と finalizer の期待 header (`2643-2651`) は `loaded_head` に統一する。
- `SPEC_SCHEMA` は `floor-pair-spec/v3` のまま。top-level と `provenance` の exact key 集合も変えない。

対抗案 X (field 廃止) は事前宣言を失い schema key が変わるため不採用。案 Y (祖先まで緩和) は
介在 code 変更を許すため不採用。いずれもレンズ 2 本が独立に同じ結論を出した。

## 所見の裁定

| # | 所見 | 判定 | 扱い |
|---|---|---|---|
| A-1 | blob 検査が symbolic `HEAD:` を使い、後から解決する `loaded_head` と別 commit を指しうる | real | **採用 (must-fix)** |
| A-2 | `refs/replace` を使えば現行 2 条件も成立しうる。brief の「成立不能」は過剰一般化 | real (事実として) | 記述訂正のみ採用。`--no-replace-objects` の追加は **scope 外** — 裁定パッケージへ |
| A-3 | OID 同値の喪失は tree 同値では代替されない | real | **採用 (文言のみ)** |
| A-4 | 実行中 module bytes の commit は証明しない | real (plan 認識済) | **採用 (文言のみ)** |
| B-1 | 空 `out/` は commit に残らず fresh checkout で load が落ちる | real | **採用 (must-fix、test fixture と手順)** |
| B-2 | status `source_commit_mismatch` が実際の判定と食い違う | real | **採用 (must-fix)** |
| B-3 | 模擬 git が parsed tuple を返すと raw 出力 parser を証明しない | real | **採用 (must-fix)** |
| B-4 | calibration/receipt に第二の不動点は無い | refuted | 手順の明記のみ |
| B-5 | 既存負例が恒真になる箇所は無い | refuted | 変更なし |
| B-6 | brief のアンカー表に `floor_pair_driver.py:22,86` が漏れ | real | plan が補完済み |

### A-1 の扱い

`loaded_head` を loader の先頭で **1 回だけ**解決し、spec・calibration・build receipt の全 blob
比較をその OID に対して行う。`_git_head` / `_git_show_head` の関数名は変えない (spawn 数 pin の
key であるため)。これは新しい gate の追加ではなく、いま作り直している束縛が単一の commit を
指すようにする修正である。

### A-2 の扱い

brief の「実 repository では 2 条件を同時に満たせない」は、通常の object 解決の下では正しく、
実 git で再現済みである。ただし `refs/replace` を使えば回避できるので、「不可能」ではなく
「正規の発行手順では成立しない」と書き直す。`--no-replace-objects` の付与は仮想リスク向けの
検査追加にあたり、ユーザーが明示した scope 外条件に触れるため実装しない。裁定パッケージへ返す。

## must-fix (段 5 で実装する)

1. plan の変更項目 1〜6 をそのまま。
2. A-1: `loaded_head` の単一解決と、全 HEAD blob 比較のその OID への付け替え。
3. B-2: 実行時 status を判定内容に合わせて改名する (`loaded_head_mismatch`)。
   consumer は `floor_pair_driver.py:2182` と `test_floor_pair_driver.py:2014` の 2 箇所だけで、
   成果物へ書き出される wire 値ではないことを確認済み。
4. B-3: 模擬 git の override は raw stdout (親は空白区切り + 改行、path は NUL 終端) を返す。
   加えて実 git の負例を 1 本置く (spec + 別 path を同じ commit に入れると拒否される)。
5. B-1: 実 git fixture は `out/` を commit から再構成できる形にする。
6. A-3 / A-4: proof-limit 文言 (`22`, `86`, summary の `proof_limitations`) を、
   「spec path を除く tree の同値を保証する。commit OID の同値と、実行中 module bytes の
   commit は保証しない」と書く。

## scope 外 (実装しない)

- `--no-replace-objects` の付与 (A-2) — 裁定パッケージへ。
- T-2423 (成果物名の protocol 要素)。`p3_b4_floor_artifact_issuer.py` は触らない。
- freeze receipt、working-tree clean 検査、その他の一般 hardening。

## 変異事前登録 (DW-M01、実装前)

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| M01 | 親判定 | `parents == (source,)` を `source in parents` へ緩める | KILLED (merge 親の負例) |
| M02 | 差分判定 | `changed == (spec,)` を `spec in changed` へ緩める | KILLED (実 git: spec + 別 path の負例) |
| M03 | spec blob 比較 | bytes 一致検査を除去 | KILLED (既存 mutation_03) |
| M04 | 実行時 | `runtime_head != loaded_head` の拒否を除去 | KILLED (実行時負例) |
| M05 | finalizer | 期待 `runtime_head` を `source_commit` へ戻す | KILLED (header 負例) |
| M06 | blob query の OID | 解決済み OID を symbolic `HEAD:` へ戻す | KILLED (模擬 git が `HEAD:` と `<oid>:` で別 bytes を返す負例) |
| M07 | 差分 parser | NUL 分割の末尾空要素を落とさない | KILLED (実 git の正例が落ちる = 過剰拒否) |

M06 は競合状態そのものを模擬で再現する。実 git では決定的に再現できないため、模擬でしか
書けないことを明記する。正例側 (過剰拒否の検出) は実 git の positive test と M07 が担う。

各変異は実装後に単一理由性を確認する。冗長 gate に吸われるものは登録から外し、台帳へ理由を残す。

## 分割

実装子 1 本 (driver と 2 つの test file が密結合)。Codex `role=author` = D95。
