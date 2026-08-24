---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-stranded-branch-audit-20260825
seq: 2
---

## 新規

### {{F:sentinel-concatenated-with-failed-command-stdout}}. 失敗時にも stdout を出す command を `$(cmd || echo SENTINEL)` で分類し、不在の枝が到達不能になった [恒真ゲート] [手順漏れ]

- 事象: 取り残し branch 6 本の着地判定で、各 path が main に在るかを
  `ms=$(git rev-parse "main:$p" 2>/dev/null || echo ABSENT_IN_MAIN)` で採り、
  `ms` を branch 側 blob と比べて SAME / MAIN_ABSENT / DIFF の 3 分類に振っていた。
  **MAIN_ABSENT が 1 件も出ず、spool fragment 7 本すべてが「main に別内容で存在」と出た。**
  実際には 7 本とも main に存在しない (fold 済みで削除されている) 側だった。
  判定表を作り直すまで、fold 済み fragment を「main と内容が食い違う未着地の成果」と
  読む一歩手前だった。実害は無い (同 wave 内で気づき、`git cat-file -e` 版へ作り直した)。
- 根本原因: `git rev-parse main:<path>` は path が解決できないとき、
  **解決前の引数文字列 `main:<path>` を stdout へ書いたうえで非 0 で終わる**。
  `$(...)` は command 置換の対象全体の stdout を捕るので、`||` の右辺が発火しても
  捕獲値は sentinel 単独にならず `main:<path>` と sentinel の連結になる。
  結果として sentinel との等値比較が恒に偽になり、**「不在」の分類枝が到達不能**になって
  全件が既定枝 (DIFF) へ落ちた。rc は握り潰していない (F37 とは別型) — rc は正しく非 0 を
  返しており、壊れたのは捕獲した値の方である。
- 恒久対応: memory `absence-check-needs-cat-file-e-not-rev-parse-fallback`
  (存在の有無は `git cat-file -e <rev>:<path>` の rc で先に決め、内容比較はその後に行う。
  `$(cmd || echo SENTINEL)` を分類に使うのは、cmd が失敗時に stdout を出さないと
  確かめた場合だけとする)。あわせて分類器を書いたら、**各分類枝が実データで 1 回以上
  発火することを数えてから結論に使う** — 本件は「MAIN_ABSENT が 0 件」という
  数え上げが最初の異常兆候だった。
- 再発検知: **機械検査は無い (prompt 規律)。** 使い捨ての shell 分類器は repo の
  lint 対象外であり、恒真な保証にしないためここに明記する。実務上の防壁は上記 memory と、
  「全分類枝の発火数を見る」作法の 2 つだけである。

## 再発

### F136

- **再発: 2026-08-25 (同日 3 例目)** — 直前の docs-only wave (同日 2 例目) と**同一の形が
  連続で再生産された**。本 wave も docs-only (差分は `docs/spool/` の 2 file) で、
  受入全走を 1 本しか投入せず走行中に repo へ何も書いていないのに、
  `test_s8b_floor_campaign.py` の `_real_output_snapshot()` 系が 11 件赤になった
  (11 failed / 15,284 passed / 60 skipped)。junit の差分は 11 件とも
  `first extra item: ('dir', 'task-runs/reports')` で、2 例目と逐語一致する。
  受入 shard は同じ作業木から request `944878` と `944879` を重ねて投入しており
  (shard-1 の junit が 03:21:47、shard-0 が 03:23:20 に確定)、既知の機序と一致する。
  帰属は 3 点で否定した — (1) wave の差分 2 file は `launch_cert` / `certificate` を
  1 箇所も参照しない (`git diff` の grep が 0 件)、(2) 同 file の焦点走は
  **451 passed / 2 skipped** で緑 (rc=0)、(3) junit 差分が実装ではなく
  `output/task-runs/` の dir 増加を指す。
- **新しい事実は決定性である。** 2 例目の焦点走も 451 passed / 2 skipped であり、
  赤の件数 (11)・assertion 本文・焦点走の緑の内訳が 3 例目と完全に一致した。
  この赤は wave 固有の事情でも散発的な flake でもなく、**docs-only wave が受入 shard 経路を
  通ると再現する構造的な赤**である。「単独再走で消える」という 1 例目の再発検知条件は、
  裏返せば「受入全走を投入するたびに一定確率で 1 回捨てる」費用を全 wave が払い続けることを
  意味する。恒久対応 (task-run 記録の書き出し先を shard session root へ逃がす seam) は
  本 wave の scope 外で、受入基盤の所有 wave の判断に委ねる点は 1・2 例目と同じ。
