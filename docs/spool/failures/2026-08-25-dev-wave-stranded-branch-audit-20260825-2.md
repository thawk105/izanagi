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
