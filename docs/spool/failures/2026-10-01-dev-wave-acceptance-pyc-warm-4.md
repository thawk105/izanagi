---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-10-01
wave: dev-wave-acceptance-pyc-warm
seq: 4
---

## 新規

### {{F:scoped-plan-masks-second-name-collision}}. 縮小受入の plan が不適格理由を 1 file 1 参照しか出さず、insight の汎用名 (dir と file) の衝突を 2 回に分けて踏んだ [手順漏れ]

- 事象: 2026-10-01 00:0x JST、md_7 (acceptance-pyc-warm) の記録 land 用に `tools/scoped_acceptance.py plan` を打つと、insight の下位 dir `data/`・`reviews/`・`rulings/` の全 file が `production-reference` で不適格になった。dir を固有名へ改めて打ち直すと、今度は `apw-measured/trees.json` だけが別の production file (`tools/pegasus/a5_second_boot_backoff_sweep.sh`) との一致で不適格になった。1 回目の理由には同じ file について dir 名側の参照 (`.codex/role-adapters/coder-v4-autonomous-k2.json`) しか出ておらず、file 名側の衝突が隠れていた。3 回目 (file 名も固有名へ) で eligible。実害は plan 2 回と改名 commit 2 本 (受入は投げる前)。
- 根本原因: insight の置き場に `data/`・`reviews/`・`rulings/`・`trees.json` のような汎用名を使った。plan の理由は 1 file につき最初に見つかった production 参照 1 件だけなので、1 回の plan で全部の衝突を知ることができない。先行例 (`verbatim/` の dir 名、`summary.json` の改名) は memory `scoped-acceptance-verbatim-dir-ineligible` にあったが、「汎用名全般」へ一般化して読んでいなかった。
- 恒久対応: memory `scoped-acceptance-verbatim-dir-ineligible` (dir 名の鍵) と本 F。縮小受入を狙う記録 wave は、insight の下位 dir と file の名前に wave 固有の接頭辞を付けて書き (例 `apw-measured/apw-trees.json`)、1 回目の plan の前に `git diff --name-only <tested main>..HEAD` の basename と dir 名を production 参照で一括照合する。道具側の改善候補: plan が file ごとの全 production 参照を列挙する (現状は先頭 1 件)。
- 再発検知: plan の `reasons` が `production-reference:` を返したら、1 件直して打ち直す前に、同じ file の basename と各階層の dir 名を production で grep して、残る衝突を先に全部出す。
