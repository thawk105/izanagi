# [T-2860] 段 6 裁定 (親、2026-09-23)

レビュー = `s6-review.md` (codex read-only 1 本、NO-GO)。**可逆最小正規化 (DW-S07):** markdown 改行用の行末空白 9 行を除去した。
原文 sha256 `d9cbdf7998e2e4a31b22e933dcab7d09a5a3f144823a3cbd7f89bbec840ff95a` (5,117 B) → `bb03060d33a88b9f67392cc804b9ac2a924ce28651a5afdf36790b66154296c1` (5,099 B)、
job root の原文 `review.md` と `diff -w -B` で一致 (rc=0)。

| 所見 | 裁定 | 親の検算 | 処置 |
|---|---|---|---|
| must-fix: critic の WAL 読取範囲を「全 10 行」と過大に記録 | real・採用 | 写しの WAL を `jq -c .` した各行の文字数は 1,844 / 1,934 / 446 / 1,605 / 1,231 / 2,578 / 1,935 / 444 / 1,615 / 1,229。1,800 超は候補・stock の `build_start` / `build_done` の 4 行。critic の python 読取りは guard hook が拒否していた (transcript の tool_result) | insight §2・稿 §2.5・fragment を「10 record の先頭 1,800 字ずつ、4 record は末尾未表示」「Bash 8 本のうち 1 本は拒否、実行 7 本は読取り」へ |
| should: critic の時刻を「07:5x・保存なし」と書いた | real・採用 | transcript の最初と最後の timestamp は 2026-09-22T22:49:53.481Z / 22:53:19.164Z (= 07:49:53 / 07:53:19 JST) | 稿 §2.7 と §4、insight §2 の工数行に記録時刻を書き、process の起動時刻ではないと限定 |
| nit: 「bytes のまま取り出した」は末尾 LF の追加を省いている | real・採用 | 保存物から末尾 1 byte (LF) を除くと 11,114 B、sha256 `25745b5f14b7fb51f3da16901eef55df35a8069d7f503e844ee88f273a383c18` | insight §2・稿 §2.5・fragment を「取り出し末尾 LF を補った」へ |

主要数値・識別子・AO 取込み・原本保全・層 3 の差分・主張限定・stale 注記・fragment 形式はレビューが照合し一致 (refuted 4 件)。

焦点再レビュー 1 巡目 (`s6-focus-1.md`、無変更の複製、sha256 `4b12cf4ca31a7aa94fafa09755f3a21c4d3d5eb534e938e3b31463331bc9a280`): **GO**。3 所見とも closed、親の派生値 (1,800 字超の 4 record、拒否 1 本・実行 7 本、07:49:53〜07:53:19 JST と 205.7 秒、11,114 B と `25745b5f…`、正規化前後の sha と byte 数) を再計算で一致。新規所見なし。
