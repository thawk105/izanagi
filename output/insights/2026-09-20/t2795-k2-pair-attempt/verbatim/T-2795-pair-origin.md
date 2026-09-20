# [T-2795] pair 投入 wave の依頼 (ユーザー、dev-wave 引数の逐語、2026-09-20)

```
[T-2795] (P1、D2172 項 3 (i)、launcher は entry 1746 / D2183 で main に着地済み) K2 手動 loop の同 job pair を投入する — 3
  巡目の候補 10 + stock 対照を 1 job で。着手直前の local main から fresh worktree、投入用に detached の fresh submit-tree + fresh layout
  を別に置く。手順の正本は `docs/phase3-s4b-runbook.md` の「同 job pair (stock 対照、T-2795 / D2172 項 3)」節と
  `output/insights/2026-09-20/t2795-pair-launcher/README.md` §2・§7 (job body `IZANAGI_S4_STOCK_CONTROL=1`、driver `--stock-control`)。最初に実
  compiler での STOCK 成立 (stock の `outcome=certified-stock`、admission receipt の `src_token == STOCK`)
  を確認し、成立しなければその走を対照成立と認定せず報告して止める (再投入で救済しない、admission gate の pin
  正規化は裁定パッケージ候補のまま触らない、規律 2 を緩めない)。成立したら 3 巡目の記録 `output/insights/2026-09-19/k2-loop-round3/README.md`
  に pair 結果を追記し、認可済みの 4 巡目 (新規生成 1 回 + 同 job stock 1 本、1 job、再投入なし) を続けて投入して同系列の insight
  に置く。results 稿は K2 3 巡稿と同形の単独稿 1 本まで。B-5 試走 (β)・launcher の改修は scope 外。本題の投入だけ、仮想リスク向けの
  gate・検査・台帳の追加は scope 外。
```

注 (親、逐語ではない): 引数が指す `docs/phase3-s4b-runbook.md` の「同 job pair (stock 対照、T-2795 / D2172 項 3)」節は存在しない。同名の節は
`tools/pegasus/README.md` (job body README、`46cc32feb` で追加) にあり、本 wave はそれを手順の正本とした。
