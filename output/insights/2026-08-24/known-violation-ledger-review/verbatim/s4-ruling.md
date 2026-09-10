# 段 4 裁定 — known-violation 台帳の見直し

裁定日: 2026-08-24 (JST)。base main = `5a4cbfa8`、裁定時の local main = `d8eaa0a7` (台帳 53 件で変化なし)。
裁定 inbox 再走査済み: wave 開始 (23:36) 以降の新規 entry は無し。known-violation に言及する
inbox entry も無し。

## 結論: 案 D を採る。実装差分ゼロで終える。

段 5・6 を飛ばし `4→7→8→9` とする。

## 所見の裁定

| # | レンズ | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| sol-1 | 正しさ | `git merge-file` は実 merge の忠実な代理でない | **real** | 採用。親の主張を「素の 3-way merge では競合した。解決過程は未確定」へ弱めた |
| sol-2 | 正しさ | `_commit_paths()` は finding 対象 path 集合でない | **real** | 採用。実装面 path のみで再測定 → 値は 12 件で不変 |
| sol-3 | 正しさ | 4 件は plan v1 の bytes 述語で測られていない | **real** | 採用。ただし sol-4 で案 A が倒れたため論点消滅 |
| sol-4 | 正しさ | 案 A はデコレータ順序・同一行重複で実装著作を免除する | **real** | 採用。**案 A 却下** |
| sol-5 | 正しさ | 案 B の docs-only 化は author gate の抜け道 | **real** | 採用。データ置き場は実装面必須 |
| sol-6 | 正しさ | 案 B は schema 同値性・入力面を定義できていない | **real** | 採用。先送りタスクの必須条件へ |
| sol-7 | 正しさ | 逐語ミラーは全史監査が見ない値を守る唯一の検出器 | **real** | 採用。**案 C 単独却下** |
| sol-8 | 正しさ | 生成器分類に誤分類 1 件 (`3f2c43d758`) | **real** | 採用。G4b を新設し訂正 |
| luna-1 | 実効 | 案 A の述語は「著作なし」を保証しない | **real** | 採用 (sol-4 と同型、独立に到達) |
| luna-3 | 実効 | `<sha>.json` は 53 finding / 52 commit を表現できない | **real** | 採用。複合 key が必須条件 |
| luna-5 | 実効 | loader を import 時に動かすと `--message-file` 契約を壊す | **real** | 採用。先送りタスクの必須条件へ |
| luna-7 | 実効 | 1 件 1 file でも同一 entry の並行登録は競合する | **real** | 採用。**「生成器を止める」は過大。減らすだけ** |
| luna-8 | 実効 | 14/21 は過大、上限は 12/21。`prevented.py` に脱落あり | **real** | 採用。抑止見積りを最大 12 へ訂正 |
| luna-9 | 実効 | G5/G6 は独立検証された原因分類でない | **real** | 採用。finding 内訳は使うが原因分類は暫定と明記 |
| luna-10 | 実効 | 投影外の opaque pin は未検証。閉包主張は未成立 | **real** | 採用。先送りタスクの必須 scope へ |
| luna-11 | 実効 | plan v1 の file:line は正しいが最新案の実装プランでない | **real** | 採用。案 A が却下されたためプラン v2 は作らない |
| luna-2/4/6 | 実効 | sol-3/6/7 と同型 | **real** | 上記に同じ |

**refuted と裁定した所見はゼロ。** 両レンズの所見はすべて real であり、親の裁定 (P1)(P2)(P3) は
いずれも覆された。

## 案ごとの裁定

- **案 A (merge の実装面判定を著作述語へ狭める): 却下。**
  署名: `_commit_paths(merge)` から実装面 path を除外する一般則は入れない。
  理由: 全行が親由来かつ全親が subsequence かつ出現回数上限内でも、
  `@audit` / `@authorize` の相対順序を決めること、同一行を 2 回置くことは実装著作である。
  最終 blob からは救えない。D721 を維持する。**撤去可能件数は 0。台帳は 53 件のまま。**
  通る正例: 実装面 path を一切変更しない merge (現行どおり finding なし)。
- **案 C (逐語ミラーを畳む) 単独: 却下。**
  署名: `test_known_violation_ledger_matches_literal_entries` を削除・縮約しない。
  理由: `ruling` / `note` は受理判定に使われないため全史監査が改変を検出しない。
  逐語ミラーは 53 件全部の 5 field・順序・一意性を独立に pin する唯一の検出器であり、
  実 commit 照合テストの被覆は 31 件にとどまる。
  通る正例: 台帳へ entry を追加し、ミラーの `expected` も同じ内容で更新した commit。
- **案 B (台帳を entry 単位のデータへ) 単独: 不成立。** 逐語ミラーが Python literal のまま残るため
  競合面が消えない。案 C を伴う必要がある。
- **案 B+C 併用: 本 wave では実装しない。ユーザー裁定へ送る。**
  理由: 両レンズが独立に「独立 literal pin の廃止自体をユーザー裁定にすること」を条件とした。
  既存の正しさ防壁を撤去する判断は親の裁量ではない (絶対規律 2、自己改善契約の
  「正しさ防壁の変更は実装せず裁定パッケージへ送る」)。加えて luna-10 の未検証 opaque pin が
  残っており、閉包を確認しないまま着手すれば land 不可になる。

## 変異事前登録 (DW-M01 / B-057)

**実装差分ゼロのため変異 matrix は免除される** (`DW-S04` の逐語: 「実装しない」と裁定済みで
実装差分ゼロの wave だけ変異 matrix を免除する)。B-057 の変異は登録しない。
**受入全走は免除されない。** 段 7 の記録 commit を作った tip に対して実走する。

## この wave の成果物 (docs のみ)

1. 53 件の全数分類 (訂正済み) と、生成器別の内訳。
2. 増加の実測 — `ast` 構文解析による厳密値。増加 20 回・減少 2 回、53→34→53、44.7 時間、約 10 件/日。
3. 0 件化の到達可能性の判定 — **現行契約では不可能**。49 件は不可逆、4 件も案 A 却下で撤去不可。
4. ユーザー裁定パッケージ (裁定 3 点)。
5. 先送りタスクの切り出し。
6. 親の測定方法の欠陥 4 件を failures 台帳へ。

## 先送りタスク (scope 外の real 所見。段 7 で fragment 化する)

- **[新規] 台帳の entry 単位格納への移行 (案 B+C)。** 着手条件はユーザー裁定 3。必須条件:
  複合 file key (`<sha>--<kind>`)、index を持たない `sorted` directory 列挙、
  現行 `_known_violation_registry()` の全検証の同値保存、duplicate/unknown key の厳格拒否、
  filename と本文の一致検査、tracked regular file のみ (symlink・untracked 拒否)、
  HEAD tree からの読み出しまたは worktree と HEAD の一致検証、lazy load
  (`--message-file` 契約を壊さない)、データ directory を実装面として分類、
  53 件全部の実 commit 照合検査と公開 stdout の逐語検査、
  投影外 consumer (`check_docs.py` / `test_check_docs.py` / `test_hooks.py` /
  `test_dev_wave_land.py`) の opaque pin の read-only 閉包確認。
  同一 entry の並行登録は fail-closed とする (競合ゼロにはならない)。
- **[新規] `--no-edit` merge / revert が trailer ゼロの commit を作るのを止める機械防壁。** G3 の 8 件の生成器。
- **[新規] 受入前 local main 取り込み merge を mid-merge でも Codex author へ委任できるようにする。**
  現在は authority-snapshot 検査が conflict マーカーのある working tree を拒否するため
  親が直接解決するしかなく、G5 の 11 件の直接原因になっている。
- **[新規] `output/insights/**/*.py` が実装面判定に当たる件。** 解析 script を insight へ置く運用と
  Codex author 契約の関係を整理する。G6 の 3 件の生成器。
- **[既存 T-1462/T-1464 等と別] D661 の `_message_file_paths()` 同型偽陽性。**
