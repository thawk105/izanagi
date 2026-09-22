# [T-2854] 段 6 裁定 (親) — レビュー A / B の所見と fix 1 巡目の仕様

入力: `out/s6-review-A-1.md` (正しさ境界・規律 1 / 2・検出力、NO-GO)、`out/s6-review-B-1.md` (過剰・削除、NO-GO)。どちらも C++ (単位 1・2) への攻撃は不成立。所見はすべて probe (author B の所有) に閉じる。

## 1. 所見の裁定

| 所見 | 判定 | 処置 |
|---|---|---|
| A1 M2 は自分の走で診断が発火したかを見ずに KILLED になりうる (時間切れの quit でも旧計数の不一致は起きる) | real (must-fix) | 採用。§2 の F2 |
| B1 M4 が「種別と操作群の不一致」と「宣言種別に対する表検査」の独立 2 検査で落ち、単一理由でない | real (must-fix) | 採用。§2 の F1 (表検査を署名基準にして種別検査と独立にする) |
| A2 「単独変異」と「単一理由」が区別されていない (自己試験は先頭理由だけ見る) | real (should) | 採用。§2 の F1 と §3 (kill 条件の精緻化、報告の書き分け) |
| A3 C1 / C2 の分割 (pin→C1 = header 2 file、C1→C2 = silo 1 file) を probe が照合しない | real (should) | 採用。§2 の F6 |
| B2 変異用 build 木の最初の通常 build と未変更 file の書き戻しが余計な再 compile を生む | real (should) | 採用。§2 の F3 |
| B3 OrderLine の「0 からの密連番」を合否条件にしている (裁定 C4 は記録のみ) | real (should) | 採用。§2 の F4 |
| B4 変異 spec の未知 key・schema_version を拒否しない (DW-M01) | real (should) | 採用。§2 の F5 |
| B5 witness parser を repo 関数の import でなく局所実装 | nit | 不採用 (判定差は示されない。局所実装であることを insight に記録) |
| A 内容照合は有限の特徴検査 (R の表の誤記は範囲内なら通る) | 限界の指摘 | 記録のみ (C4 の射程。拡張は裁定パッケージ候補とせず、insight の「主張しないこと」に書く) |
| 親 P1 build の並列度が `min(16, cpu数)` 固定 | should (親) | 採用。§2 の F7 |

## 2. fix 1 巡目 (Codex fix、author B の worktree、probe/ 配下だけ)

- **F1 内容照合の単一理由化:** 各 frame の署名 (表 4 への op=I があれば Payment、表 5・6・7・8 のどれかへの op=I があれば NewOrder、両方または無しは署名不定) を作る。`content-txtype` = 署名不定、または署名と宣言 tx_type の不一致 (1 = NewOrder、2 = Payment)、または両 tx_type のどちらかが 0 件。`content-table` = **署名に対して** (宣言 tx_type ではなく) 表構成が崩れていること: NewOrder 署名は表 5・6・7・8 のすべてへ op=I を持ち、表 5 と表 6 の INSERT key が同じ 8 byte で 1 対 1、表 4 への W なし。Payment 署名は表 4 への op=I がちょうど 1 本・表 0・1・2 への op=U を持ち、表 5・6・7・8 への W なし。これで M3 (表 6→5) の理由集合は `content-table` だけ、M4 (種別 1↔2) は `content-txtype` だけになる。
- **F2 M2 の発火確認:** D1 の置換に、閾値到達時の診断 marker を stderr へ 1 行出す処理を足す (例: `std::fprintf(stderr, "t2854-diag-quit\n");`、scratch 専用)。D1 と M2 の両方で、stderr の marker が 1 回以上、かつ C 行数 1000 以上の trace file が 1 つ以上、を要求する。M2 の KILLED は加えて: rc = 0、stdout の witness が一意に読める、E 数 = C 数、**C 行数 > commit_counts_**、理由集合 = `witness` だけ。
- **F3 変異の build の無駄取り:** 変異用 build 木は configure だけ行い、通常 build はしない (最初の変異の build で作られる)。復元は変異で書き換えた file だけを書き戻す (bytes が同じ file は書かない、mtime を動かさない)。
- **F4 OrderLine は記録だけ:** 注文ごとの密連番の検査と、`orderline_min != 0` による不合格を外す。記録は最小値・注文ごとの最小値が 0 の割合・見本。表 8 への INSERT があることは NewOrder 署名の表構成 (F1) が見る。
- **F5 spec の厳格化:** top-level の key 集合 (`schema_version`・`anchor_status`・`note`・`entries`) と `schema_version == "t2854-mutation-spec/v1"`、entry の key 集合 (`id`・`base`・`file`・`anchor`・`replacement`・`target`・`kind`・`expected`・`intent`) を固定し、過不足は起動前に拒否。
- **F6 分割の照合:** `sources()` で pin→C1 の raw diff が `include/trace.hh`・`include/tpcc.hh` の 2 file だけ、C1→C2 が `cc/silo/transaction.cc` の 1 file だけであることを照合。
- **F7 build 並列度:** `os.cpu_count()` (無ければ 1) を使う。
- 自己試験: F1 の単一理由を**理由集合の完全一致**で確かめる負例 (種別 1↔2 の入れ替え → `['content-txtype']`、表 6→5 → `['content-table']`、Payment frame から表 4 の INSERT を消す → 署名不定で `['content-txtype']`)、F4 の正例 (同一注文の番号 {0,2} や 1 始まりでも合格し、記録値に反映される) を足す。既存の負例の期待 `first_reason` は変えない (F1・F4 で意味が変わる負例だけを、この裁定に沿って直し、直した件を報告に列挙する)。

## 3. 変異の kill 条件の精緻化 (DW-M01、fix 前に登録)

裁定 §4 の「KILLED = 判定が fail かつ最初に落ちた理由が期待コード」を次で置き換える。

| ID | KILLED の条件 |
|---|---|
| D1 | (kill ではなく PASS 条件) 全検査合格、stderr の診断 marker ≥ 1、C 行数 ≥ 1000 の trace file ≥ 1 |
| M1 | `first_reason == "schema"`。構造破損に伴う派生理由 (witness・content) の併発は許す (先頭理由の一致として報告し、単一理由とは書かない) |
| M2 | 理由集合 == `["witness"]`、rc = 0、E 数 = C 数、C 行数 > commit_counts_、診断 marker ≥ 1、C 行数 ≥ 1000 の file ≥ 1 |
| M3 | 理由集合 == `["content-table"]` |
| M4 | 理由集合 == `["content-txtype"]` |
| M5 | 9 TPC-C consumer の全件で展開比較 (`-E -P -dD`) が不一致、include 活性比較は全件一致 |

## 4. 次の手順

fix 1 巡 → 親が回収・login で自己試験・anchor 再照合 → 焦点再レビュー 1 本 (DW-S06-C、所見ごとの closed / partial / regressed 表、DW-O16) → C1 / C2 commit → 計算 job。
