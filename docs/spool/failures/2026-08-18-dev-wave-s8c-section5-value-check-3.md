---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-18
wave: dev-wave-s8c-section5-value-check
seq: 3
---

## 新規

### {{F:codex-consult-stall-zero-output}}. 段 3 の敵対レンズが 2 回とも成果物ゼロで落ち、6600 秒を失った [コンテキスト浪費]

- 事象: 段 3 の敵対相談レンズ 1 本を投入したところ、1 回目は wall-clock 3600 秒で SIGTERM
  (`stop_reason=max_wall_clock_s`、`codex_exit_code=-15`、model call 26、`output_bytes=0`)。
  読みすぎと判断して読む範囲を行範囲で限定し 40 分の締め切りを本文へ書いて再投入したところ、
  2 回目は **model call 4 件で 3000 秒**を使い切り、やはり出力ゼロで落ちた。合計 6600 秒を失い、
  段 3 の敵対はもう 1 本のレンズと親の一次資料確認だけで成立させることになった。
- 根本原因: 2 回目の受領証が示すのは読みすぎではなく**外部応答の停滞**である
  (1 回目は 2.3 分/call、2 回目は 12 分/call、同時刻に走った別レンズは 27 call を 502 秒で完了)。
  子側の prompt を直しても解消しない要因に対して、同じ待ちへ 2 度目の全予算を投じたのが浪費である。
- 恒久対応: memory `waiter-failure-modes` に「出力ゼロで壁時計上限に達した子は、受領証の
  `model_calls / wall_clock_s` を見て**読みすぎ (call 数が多い) と停滞 (call 数が少ない) を区別**し、
  停滞なら同一レンズを再投入せず担当を後段のレビューへ移す」を追記する。判定に使う値は
  `receipt.json` の `actuals` にあり、親が 1 コマンドで読める。
- 再発検知: 受領証の `outcome=not_accepted` かつ `output_bytes=0` の子について、
  `actuals.model_calls / actuals.wall_clock_s` を worklog へ書くこと。停滞側 (1 call あたり
  10 分超) が同一 wave で 2 回出たら再投入せず段構成で吸収する。

## 再発

### F43

- **再発: 2026-08-18** — 段 6 の敵対レビュー子が `## 総括` を fenced code block の**内側**へ
  書いたため `check_codex_output.py` が rc=1 で不受理にした (`output_bytes=3141`、
  `codex_exit_code=0`)。中身は有効で real 所見を 1 件当てていたため、親が未完了と明記して保全し
  fix の入力に使った。加えて同日、極小作業 (2 行の取り込み) の実装子が正常終了 (exit 0、84 秒) しつつ
  報告 327 bytes で 500 bytes 下限に届かず不受理になった。後者は「2〜5 行で書け」と書いた親の
  prompt 側の誤りであり、作業自体は差分を親が逐語照合して採った。**出力形式の指示は
  「fence の外に `## 総括` を置く」と「下限 500 bytes」を両方明示する**。
