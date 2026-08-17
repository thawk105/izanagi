---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-18
wave: t1312-evidence-grace-origin
seq: 2
---

## 新規

### {{F:argparse-help-rewrap-breaks-literals}}. help 文字列への 1 語追加が、行折り返しの移動だけで無関係な逐語 assertion を壊した [恒真ゲート] [手順漏れ]

- 事象: `tools/dev_wave_codex.py` の `--evidence-grace-s` の help 先頭へ
  「子の起動完了時を起点とする」を足したところ、`--help` の意味は正しいまま
  `test_dev_wave_codex.py::test_help_marks_resource_defaults_non_authoritative` が落ちた。
  既存 assertion が要求する literal `--max-wall-clock-s` が、出力では
  `--max-wall- clock-s` に割れていた。
- 根本原因: argparse は `textwrap` で help を折り返し、空白とハイフンで改行しうる。
  テスト側の `_help_option_block` は行を空白 1 個へ連結して正規化するため、
  ハイフン位置で入った改行は空白として残り、元の option 名へ復元できない。
  文頭へ挿入すると後続すべての折返し位置が動くので、**編集した箇所とは無関係な行の
  literal が壊れる。**
- 影響: 計算ノードの焦点走 1 本を消費した (181 item 中この 1 件だけが赤)。
  受入全走の前に見つかったため lease は消費していない。
- 恒久対応: memory `argparse-help-edits-must-append-as-separate-chunk` に
  次の手順を置いた。**(1) 旧文面を byte 同一の前方 prefix として保つ。
  (2) 新語句は末尾に、直前と空白で区切った独立 chunk として足す。**
  末尾へ連ねるだけでは足りない — `textwrap` は `break_long_words=True` のため、
  空白もハイフンも含まない長い chunk を任意位置で割りうる。
- 再発検知: 当該テスト自身が fails-closed で検出する (本事象はそれが発火して判明した)。
  新しい検査は作らない。

## 再発

### F57

- **再発: 2026-08-17** ([T-1312] wave の焦点走)。**D498 の修正を適用した木でも、login ノードの
  32 worker 走行で 68 件が赤になった。** 3 file 633 item
  (`test_codex_worker_launch.py` / `test_dev_wave_codex.py` / `test_check_docs.py`) を
  追加 flag なしで走らせた結果で、署名は本 F と同じ
  (`evidence_status='missing'`、`limit_trigger=None`、`codex_exit_code=-15`、
  `wall_clock_s` は 3.0 秒予算に対し 2.66 秒)。同じ 2 file を `--force-dispatch` で計算ノードへ
  回すと 181 item が 180 passed / 1 failed になり、唯一の赤は本 wave が作った help 折返しの
  決定的な赤だった。**launcher 系の赤は 68 件すべて環境要因で、`DW-O18` により帰属しない。**

  **新しい情報は 2 つある。**
  - **D498 は本 F を消さない。** 猶予の起点を子の起動完了時へ移すと「preflight が猶予を
    食い切る」機序は消えるが、login ノードの過負荷下では spawn 後の evidence 出力が
    猶予 1.0 秒に間に合わず、同じ署名の赤が残る。段 3 の敵対レンズ B がこの限界を
    実装前に指摘しており (「preflight 機序を除くだけで非帰属赤が消えることまでは保証しない」)、
    実測がそれを裏付けた。**本 F の恒久対応に「D498 で閉じる」と書いてはならない。**
  - **この赤は infrastructure error の形では出ない。** 既存の `--force-dispatch` recipe が
    対処してきた login ノードの `rc=16` (bounded scope attest 失敗) と違い、
    走行は完走してもっともらしいテスト失敗を 68 件並べる。**rc と件数だけを見ると
    実装差分の回帰に見える。**

  **恒久対応は本 F 既載の既定 recipe** (login ノードから投げる短時間の targeted 走行には
  `--force-dispatch` を付けて計算ノードへ回す) **のままとし、追加の機構は作らない。**
  本再発が足すのは適用理由であって手順ではない — これまでは `rc=16` を避けるためだったが、
  launcher 系では**偽の赤を判定に使わないため**にも必要である。

- **再発: 2026-08-18** ([T-1312] wave の変異 matrix 本走)。**変異 harness の baseline が
  計算ノードでも同族のフレークで赤になり、production write を開始せずに中止した。**
  署名は F285 側の sub-mode (`limit_trigger='max_wall_clock_s'`、`codex_exit_code=-9`、34 件)。
  直前の probe 走行は同一 commit・同一 runner で baseline PASSED だったので一過性である。

  **新しい情報は、`--resume` が baseline を再走しないことである。** 中止時に harness が印字する
  resume command をそのまま流すと `baseline=0 run(s)` となり、記録済みの FAILED baseline を
  再利用して同じ地点で再び中止する。**baseline のフレークからは resume で復帰できない。**
  新しい `--scratch-root` / `--out` / `--attempt-out` で最初から走らせ直す必要がある。
  やり直した走行は baseline PASSED で完走した。
