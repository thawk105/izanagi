# 段 4 裁定 — [T-2662] 真偽表の候補集合 (probe 契約) と wave の形

段 2・3 は省いた (既定の軽量版。設計択一は D2104 項 25 が「暫定は本番側・抑止を広げない」で
束縛済み)。裁定 inbox の再走査で D2104 が main b4631a92e に fold 済みと分かり、brief の参照を更新した。

## 裁定

- **実装しない (実装差分ゼロ)。** 段 5 は probe 1 本を Codex `role=author` が worktree 内へ書き、
  親が job dir へ退避して login node で実走する。probe は repo へ commit しない (insight は
  SHA-256 と byte 数で同定し、出力の逐語を `s5-truth-table.md` へ貼る)。
- **変異 matrix は免除** (`DW-S04`: 実装面の差分ゼロ)。**受入全走は免除しない。**
- **段 6 は敵対レビュー 2 本** (read-only codex consult) を真偽表と結論の下書きに当てる。
  レンズ A = 候補集合の完全性と実在 path 対照の妥当性 (割れる型を見落としていないか、対照が
  本番の入力領域を代表しているか)。レンズ B = D248 の意味の解釈と向きの結論 (抑止を広げない
  不変条件に反していないか、fail-safe の向きを取り違えていないか)。
- **向きの結論は真偽表を見てから README に書く。** brief の (P2) は provisional であり、真偽表が
  (P1) を否定する行 (本番 True かつ helper False) を 1 行でも出したら (P2) を書き直す。

## probe 契約 (候補集合の事前登録)

probe は `tools/audit_dangling_commits.py` を `importlib.util.spec_from_file_location` で読み
(既存テストと同じ経路)、次の各行について helper `_has_bounded_path_reference(content, pattern)` と
本番 `_bounded_path_reference_matches(content, patterns, roots)` の `pattern in found` を並べる。
行 ID・pattern (repr)・content (repr)・helper・本番・一致・向き (H>P = helper だけ True、
P>H = 本番だけ True) を表にし、末尾に集計 (行数・一致数・H>P 数・P>H 数) を出す。

### 候補 pattern (path) の型 — 探索根は `/offrepo` を既定とし、根自身に境界 byte を含む型を別に持つ

| 型 | 例 | 意図 |
|---|---|---|
| P0 | `/offrepo/w/a.py` | 境界 byte なし (対照) |
| P1 | `/offrepo/w/my file.py` | 末尾要素に空白 |
| P2 | `/offrepo/my dir/a.py` と祖先 `/offrepo/my dir` | 中間 dir に空白 (祖先 pattern も候補に入る) |
| P3 | `/offrepo/w/a\nb.py` | 改行 |
| P4 | `/offrepo/w/a(1).py` | 括弧 |
| P5 | `/offrepo/w/it's.py` | 引用符 |
| P6 | `/offrepo/w/a\tb.py` | tab |
| P7 | `/offrepo/w/a[1]{2}<3>.py` | 角括弧・波括弧・山括弧 |
| P8 | `/offrepo/w/日本語/a.py` | 非 ASCII (境界 byte ではない) |
| P9 | `/off repo/w/a.py` (根 `/off repo`) | 探索根自身に空白 |
| P10 | `/offrepo/x/offrepo/y.py` | pattern 内部に根が再出現 |
| P11 | `/elsewhere/a.py` (根 `/offrepo`) | 根の外の pattern (本番の入力領域外、helper との構造差の露出) |
| P12 | `/offrepo/w/receipt[?]*.json`、`/offrepo/w/:(glob)does-not-match` | 実在 path 2 件と同じ形 |
| P13 | 実在: `/work/1/SFC/tanab/dev-wave-jobs/.../g2 clean scan Ω/<配下 file 1 つ>` | 実在の空白入り dir 配下 (根 `/work/1/SFC/tanab/dev-wave-jobs`、pattern は `_reference_patterns` で生成) |
| P14 | 実在: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2397-a1-attempt4/acceptance1.log` | 陽性対照 (境界 byte なし、landed 参照が main に実在) |

### 候補 content (landed 内容の書き方) の型

| 型 | 形 | 意図 |
|---|---|---|
| C0 | `<p>\n` | 裸 + LF |
| C1 | `'<p>'`、`"<p>"`、`` `<p>` `` | 引用 |
| C2 | `(<p>)`、`[<p>]` | 括り |
| C3 | `<p>.backup\n`、`<p>+backup\n` | 右側衝突 (両方 False の対照) |
| C4 | `/other<p>\n` | 左側衝突 (両方 False の対照) |
| C5 | `<p>。\n` | 非 ASCII 接尾 (両方 False の対照、D248 の明示例) |
| C6 | `<p>` (content == pattern) | 先頭・末尾に接する |
| C7 | `<p>+backup\n<p>\n` | 無効の後に有効 |
| C8 | `prefix <p-file> and '<p-ancestor>'` | 同一 content に file と祖先 |
| C9 | `<p>\0` | NUL 接尾 (境界 byte ではない → 両方 False) |
| C10 | `<p>\r\n` | CRLF |
| C11 | 1 MiB + α の content で `<p>` を chunk 境界 (`READ_CHUNK_SIZE`) の前後 ±(len(root)+2) の各 offset に置く | chunk 跨ぎ (P4 の (P4) 前提) |
| C12 | 実在: main blob `orchestrator/manual_probes/test_t2397_a1_source.py` の bytes (`git cat-file -p main:<path>`) | P14 の陽性対照 (祖先 dir を `Path("...")` で参照) |
| C13 | P13 の実在 path を `"`、`'`、裸 + LF で書いた合成 content | 実在の空白入り path での差の発火 |
| C14 | 空 content、空 pattern | 端 (helper は False、本番は空集合) |

pattern 型 × content 型の直積のうち、意味を持つ組を全部取る (P11 は C0/C1、P13/P14 は C12/C13 に限る)。
本番の `patterns` 引数には、その行の pattern に加えて `_reference_patterns` が生成する祖先を全部入れる
(本番と同じ入力形)。

### probe の fail-closed

`--selftest` で既存テスト `test_bounded_path_reference_single_scan_matches_legacy_boundary_semantics`
の 6 行を再現し、期待どおり (全行一致) でなければ rc≠0 で止まる。実在 path (P13/P14/C12) は
存在しなければ rc≠0 で止まり、代役に落とさない。

## 段 5 への射影

- probe の置き場: worktree 内 `output/insights/2026-09-17/t2662-bounded-reference-truth-table/probe_truth_table.py`
  に書かせ、親が実行前に `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2662-bounded-reference-truth-table/`
  へ `mv` する (repo には残さない)。
- 出力: Markdown の表 (stdout) と JSON (`--json <path>`)。
- 子は docs を編集しない・commit しない。
