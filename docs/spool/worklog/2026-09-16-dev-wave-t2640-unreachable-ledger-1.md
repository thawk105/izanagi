---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2640-unreachable-ledger
seq: 1
title: [T-2640] 未記帳の到達不能 commit 30 件を記帳し全件を救出した — 通知は止まり監査は 0 件を返す (docs + 記録、branch worktree-dev-wave-t2640-unreachable-ledger、共有 Git へ救出 ref 30 本、実装面差分ゼロのため変異 matrix 免除)
---

## 本文

- 一次資料は `output/insights/2026-09-16_t2640-unreachable-ledger/`。監査 stdout 2 種、記帳前後の
  台帳照合 JSON、53 path の内容照合、規律 6 の内容監査、30 本の ref 作成と再検査の rc、
  子の逐語 5 本を置いた。
- **親の段 1 brief の provisional 裁定 (P1) は撤回した。3 者が独立に blocker と判定したため。**
  brief は「内容が main に完全一致で残る 16 件を `accepted-loss` にする」としていたが、
  段 2 plan・段 3 レンズ A・段 3 レンズ B が揃って「D2044 項 7 は当該 16 OID についての
  人間の喪失受容文ではない」と指摘した。台帳の逐語は `accepted-loss` を
  「人間が喪失を明示的に受容した場合」と定めており、AI の内容照合をこれへ読み替えることは
  裁定の拡大解釈である。**全 30 件を `rescued` にすれば既存の授権内で閉じられる。**
  設計判断は {{D:no-ai-loss-acceptance}}。
- **親 brief の実測の一般化 3 件も子が訂正した。** (a) 「判定器は必ず indeterminate」は 4 件からの
  一般化だった → 30 件すべて実走し直した (30/30 が `indeterminate` / `assessment-timeout`)。
  (b) 「loose 4 件は期限超過」は誤り → mtime+2 週は 2026-09-23 で、評価時点では超過していない
  (`urgent` の窓には入る)。(c) 「26 packed」は `evidence.json` に pack membership が無いまま
  書いていた → `git verify-pack -v` を 18 本の `.idx` 全部に掛けて確定した。
- **30 件という集合は 3 経路で一致した。** `audit_dangling_commits.py` 単独 (85.194 秒、rc=1)、
  `check_branch_rescue.py --ledger-check` の `unledgered_commits`、
  `--offrepo-root` 付き監査 (**3708.671 秒**、repo 外 15 万 dir / 85 万 file を走査、抑止 0 件)。
  3 本目は同 tool の所要上限 300 秒を 12 倍超えた。`/cleanup-branches` はこの形を毎回要求する。
- **原因は main 側 insight 配置の 2 度の変更だった。** `output/insights/<日付>_<task>/` →
  `output/insights/<日付>/<task>/` の再編と、`114c5c4dfc8e` ([T-201]) の gzip 圧縮。
  53 組のうち 37 組は内容が main に残っているが、**直接一致は 0 組で 37 組すべてが
  gzip 展開後の blob OID 一致**である。
- **救出の代償は小さい。** `git rev-list --objects <30 OID> --not --all` の実測で、恒久的に
  延命する object は **322 個 (commit 40 本)** だけ (repo は in-pack 171,779 + loose 4,616)。
- **成果物は tracked 実装差分ゼロだが、共有 Git common directory へ ref を 30 本足している。**
  台帳 commit だけでは再現されない状態変更であり、別 clone で台帳を見ても救出済みにはならない。
  `refs/heads/` ではないので `git branch -a` と `git worktree list` の項目は増えない。
- 判断材料の収集と entry 生成に使った一回限りのコードは job dir に置き repo へ入れていない
  (段 2・段 3 とも支持)。出力はすべて insight の `evidence/` に保存した。
- **本 wave で判定器は直していない (scope 外)。** `tools/check_branch_landed.py` の
  `COMMAND_TIMEOUT_SECONDS = 5.0` は CLI から変えられず、本 repo では `git log` が 5 秒を超えるため
  30/30 が `assessment-timeout` で倒れる。`--timeout-seconds 300` を渡しても 9.7 秒で倒れる。
  `assessment_verdict` には実測どおり `indeterminate` を書き、内容照合を `landed` の代用にしていない。

## 次の一手差分

### 完了

- [T-2640] 30 件を既存 schema で記帳し、救出 ref を作って全件 `rescued` にした。救出後の
  `--ledger-check` は rc=0、`ledger_notification_due=false`、通知 0 件、issues 0 件、監査報告 0 件。
  remaining: none
  base: e750027b95188d60f9e1315c98036d2118beeedb62204c5700b63912ed48625f

### 新規

- {{T:branch-landed-per-command-timeout}} **P2・新規**: `tools/check_branch_landed.py` の
  per-command 上限 `COMMAND_TIMEOUT_SECONDS = 5.0` が本 repo 規模に合っていない。到達不能
  commit 30 件を実走して 30/30 が `assessment-timeout` で `indeterminate` になった。
  `--timeout-seconds` は全体予算で per-command ではないため CLI から変えられない。判定器は
  着地の有無をこの repo で 1 件も判定できていない。定数を上げると verdict の受理集合が変わるので、
  上げる前に何を受理するかを決める必要がある。
