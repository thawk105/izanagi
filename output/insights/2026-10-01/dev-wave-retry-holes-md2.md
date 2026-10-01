# 同原因の再試行を生んだ手順の穴を dev-wave 手順書へ 1 行ずつ入れた (md_2、2026-10-01)

authority: none / default_effect: no-state-change — 収容先と見送り理由の記録。手順の正本は `docs/dev-wave/` の各節。

## 依頼と一次資料

- 依頼: land 調整役の `md_2.txt` (2026-10-01 SELF-REVIEW 集約の型 2〜4・単発の型を手順書へ 1 行ずつ)。
- 一次資料: 同 dir の `summary.md` (repo 外、land 調整役が作成)。下の「元の型」はその節名。

## 収容先 (6 項目を収容、1 項目を見送り)

| 項目 | 元の型 | 収容先 (層) | 入れた文の要旨 |
|---|---|---|---|
| 隔離 session の Bash | 型 2 (5 wave で 8〜10 回) | `DW-O03` (L2) | 絶対 path 直書き・git 単独 (`-C`・`cd &&` 不可)、複数手順は Write した `.sh` を `bash <絶対path>` 単独起動 |
| submodule 初期化の再実行 | 型 3 (F810 再発) | `DW-O08` (L2) | 既存文 (2026-10-01 10:00 に 7c864b383 が追加) へ `rc=1` の `update-no-fetch` を例示し、確認 command を `git submodule status --recursive` と明記 |
| 子への必読資料の渡し方 | 型 4 (F819 再発) | `DW-O02` (L1.5) | 必読資料は原名で job dir へ出し、1 行 1 file の絶対 path で列挙 |
| 子が試験を走らせられない | 型 4 (md_20) | `DW-S05-C` (L1.5) | 実走不能 (`run_tests.py`・pytest 不可) で止まらず「実装済み・未実走」と書く |
| fix 裁定の部分許可 | md_42 (3 回) | `DW-S04` (L1) | 期待値変更を許す裁定 (段 6 fix も) は対象 test 関数の全 assert を逐語で並べ可否を付ける |
| 撤去前の ExitWorktree | 単発 (md_44) | `DW-S09` (L1) | 撤去前に `ExitWorktree`(keep) で session を木の外へ出す |

- fix 裁定の項目は依頼文の「段 6 の fix 裁定」を、親の裁定の正本 `DW-S04` に「段 6 fix も」と明記して置いた。
  段 6 だけで読む `DW-S06-B` は L1.5 で、原資が足りなかった。
- ExitWorktree の項目は依頼文の「DW-S09 か撤去の入口」のうち `DW-S09` に置いた。撤去手順 `DW-O28` は md_1 の所有。

## 見送り (1 件)

- 文献・外部索引の生死確認は本走と同じ request 形で打つ (md_43、arXiv `max_results=0` で同じ 500 を 5 回) —
  見送り。dev-wave 手順書の段・条件のどれにも発火点が無い (文献検索は dev-wave の段でなく研究作業の道具の作法)。
  依頼文の条件「置き場所が dev-wave docs でなければ見送り」に当たる。md_43 が記憶
  `index-liveness-probe-uses-production-request-shape` を作成済み。

## 予算の収め方 (D730/D782 の第 1 段 = 既存記述の削減、上限は据え置き)

着手時と完了時の `tools/check_docs.py` 実測 (予算を 0 に差し替えて findings から読む使い捨て script、repo 外):

| 層 | 着手時 | 6 行を足した直後 | 完了時 | 上限 |
|---|---|---|---|---|
| L1 | 10,624 | 10,801 | 10,620 | 10,625 |
| L1.5 | 9,692 | 9,711 | 9,694 | 9,696 |
| `DW-O03` | 971 | 1,085 | 998 | 1,000 |
| `DW-O08` | 658 | — | 709 | 1,000 |

- 原資: (1) code span の外で CJK と隣り合う半角空白の除去 (L1 の `DW-S01`・`DW-G05`・`DW-S04`・`DW-S07`・
  `DW-S09`・`DW-CTX`・`DW-M01`、L2 の `DW-O03`)。Python 側 literal に pin された行と数字直後の空白は残した
  (`D95 決定` のような D/F 番号の語境界を保つため)。(2) L1.5 行の全角括弧の半角化 (1 対 4 bytes)。
  (3) `DW-O03` 内の理由の重複句 (「射程が違うので」「同じ理由で」「同型に」) の削除。(4) 自分の追記文の短縮。
- L1.5 は空白除去の原資が実質 0 だった。残る空白はほぼ全部 `reasoning=` 行など check_docs の literal に pin された行の中にある。
- pin の確認: 編集前 (3489f7322) の docs に逐語で現れる Python 文字列 literal 588 件のうち、編集後に消えたのは
  5 件 (「絶対 path」「scope 外」「repo 外」「fragment 」「非 0 終了」)。どれも dev-wave 文書を読まない試験の一般語との偶然一致で、
  check_docs・test_check_docs 由来は 0 件。
- 次に L1・L1.5 へ足す wave の空きは L1 5 bytes、L1.5 2 bytes。空白の原資は L1 の `DW-C00`・`DW-STOP`・`DW-S08` に十数 bytes 残るだけ。
