---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-t1647-a2-cert-fanout
seq: 1
---

## {{D:a2-outer-certification-is-a-conjunction}}. A-2 の外側 certification は workload 単位 campaign の論理積とし、規則を protocol hash へ入れる

**決定:** A-2 の 4 cell を 1 本の job で直列に取る形をやめ、**workload ごとの独立 job へ分割する**。
これに伴い受理集合が「単一 request の 4 cell」から「2 request・2 host・2 時刻の workload 対」へ
広がるため、**「各 workload は独立に環境契約された campaign であり、外側の certification は
その論理積である」規則を policy へ明記する**。ただし文言を policy に足すだけでは足りない。
**規則は `_protocol_preimage` の対象に入れ、`protocol_sha256` が規則の変更に追随することを
負例で示す。**

**理由:**
- 分割そのものは既定の規範である。`docs/pegasus-runbook.md` の 2026-08-11 ユーザー裁定が
  「独立なら既定で並行投入する。同じ protocol を別 workload で回すのは fan-out してよい典型」と
  定めており、A-2 の単一 job 直列がその逸脱だった。
- 受理集合を広げる以上、それを許す規則が protocol 側に無ければ「気づかないうちに広がった」形になる。
- `_protocol_preimage` は `scheduler` を含まない。policy に書き足すだけでは `protocol_sha256` が
  動かず、**書いただけで発火しない飾り**になる。過去に繰り返し警戒してきた型である。

**却下した選択肢:**
- **cell 単位へ分割する** — `run_workload` が要求する stock → adopted の対照条件を壊す。
- **反復 5 回を別 job へ割る** — 各反復を別 campaign・別 lock へ束縛し直すことになり proof chain を
  変える。実行時間のために正しさ検証の構造を変えることになり、D1059 の向きにも反する。
- **規則を policy へ書くだけで hash 対象に入れない** — 恒真な保証を 1 つ増やす。

## {{D:job-local-closure-is-not-a-shared-parent-scan}}. 共有親の走査禁止は、1 job だけが所有する directory の closure 検査を禁じない

**決定:** 並行投入の独立条件 1 が禁じる「親 directory を検査する consumer の共有」は、
**2 つ以上の job が共有する親**の走査を指す。**1 つの job だけが所有する
`jobs/<workload>/raw/` の closure 検査 (regular file ちょうど 2 件、余分な entry と symlink を
拒否) は、この禁止に当たらない。** 分割にあたって旧版の closure 検査を落とさず、job-local で
同じ厳密さを保つ。

**理由:**
- 禁止の目的は「job どうしが互いの成果物を観測して独立でなくなること」を防ぐことであって、
  自分の成果物の完全性検査を捨てることではない。
- 旧版は `raw/` の regular file 集合がちょうど 4 cell であることを検査していた。exact path を
  直接開く形に変えただけでは、`jobs/rr5/raw/decoy.json` のような余分 file が受理される。
  これは論理積以外の受理集合拡大にあたる。
- 段 6 のレビューはこれを「受理集合を広げない」と「親を走査しない」の衝突として裁定へ返したが、
  所有単位を見れば衝突ではない。

**却下した選択肢:**
- **exact path を開くだけで closure を見ない** — 余分 file を受理し、受理集合が広がる。
- **共有親 `jobs/` を走査して全体を検査する** — 独立条件 1 を壊す。
