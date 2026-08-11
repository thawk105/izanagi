---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t756-fn2-trace-v2
seq: 3
---

## 新規

### {{F:mutation-digest-truncation-hides-expected-nodes}}. 失敗 node が多い変異は期待 node の完全集合を記録できない [手順漏れ] [テスト代表性]

- 事象: 変異事前登録のため `git diff-tree --raw` から `-r` を落とす変異の期待 node を実測で
  導出したところ、26 件が失敗したのに失敗 digest は 12 件しか出力しなかった
  (`IZANAGI_FAILURE_DIGEST_ACCOUNT failures=26 failed=26 selected=12 omitted_failures=14`、
  `budget_bytes=49152`)。harness は失敗 node 集合の完全一致でしか KILLED を数えないため、
  この変異はどう登録しても MISMATCH にしかならない。
- 根本原因: 失敗 digest の byte 予算による切り詰めと、harness の「期待 node 完全一致」判定が
  噛み合っていない。切り詰めが起きたことは digest 自身が申告するが、変異の登録側はそれを
  見る義務を負っていなかった。
- 恒久対応: `docs/dev-wave/mutation.md` `DW-M08` の「期待 node と記録 node を突き合わせ前に
  同じ形式へ正規化する」義務に、切り詰め時の扱いを含める運用とする。**本 wave では
  `docs/dev-wave/**` の L1.5 byte 予算に空きが無く追記できなかった** (`check_docs` が
  `9791 > 9566` で拒否)。予算を空けるには L2 節の削除が要り、それはユーザー裁定に限られるため、
  記述の追加は裁定待ちとして本エントリをポインタにする。実務上の回避は
  「失敗 node が多い変異は narrow な gate へ再照準し、広い変異は実測値だけを証拠として残す」。
- 再発検知: 変異台帳の `failed_nodes` 件数と、job stdout の
  `IZANAGI_FAILURE_DIGEST_ACCOUNT` の `omitted_failures` が非 0 でないかの照合。

### {{F:plan-child-asserts-absent-toolchain}}. 段 2 プランが存在しない toolchain を実走条件に据えた [手順漏れ]

- 事象: 段 2 の codex プランが「実走は admission build と同じ `g++-13` を要求し、無ければ
  成功扱いしない」と書いたが、この環境に `g++-13` は login / compute とも存在しない
  (`docs/pegasus-runbook.md` §7 が明記、既存 real-build control もそのため skip する)。
  そのまま実装していれば規律 1 の実走証拠が 0 件になっていた。
- 根本原因: `docs/dev-wave/core.md` `DW-S01` は「別 program を起動する成果物では build・
  環境変数・外部 command と注入 seam の実在を棚卸しする」義務を**親にだけ**課しており、
  段 2 のプラン子には課していない。子は runbook を読めば分かる事実を確認しないまま条件に据えた。
- 恒久対応: `docs/dev-wave/workers.md` `DW-S02` へ「実走条件に据える外部 command・toolchain は
  実在を確認させる」を追記する。**本 wave では docs 予算不足で追記できず** (上記と同じ理由)、
  裁定待ち。実務上は親が段 1 brief で実測した toolchain 一覧をプラン子の prompt へ渡す。
- 再発検知: 段 3 の敵対レンズが実在しない前提を blocker として拾う (本件は sol / luna の
  2 レンズが独立に検出した。段 3 を省く軽量版では検出されない)。
