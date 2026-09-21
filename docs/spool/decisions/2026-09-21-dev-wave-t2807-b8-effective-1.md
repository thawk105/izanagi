---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-21
wave: dev-wave-t2807-b8-effective
seq: 1
---

## {{D:b8-effective-and-longrun-verify}}. B-8 事前登録 v1 の発効の形と、校正 → 本走 → 3 値判定の実施手順

**決定:** D2194 項 1 の承認に従い、事前登録 v1 (raw sha256 `6ccb18c7…`) を案 A の発効束で発効し、校正 3 job → 本走 6 job →
3 値判定まで実施した。発効と実施の形は次のとおりとする。

1. **発効束 JSON の作り方。** 前 wave の draft の**実験構成の値は 1 つも変えず**、`status` だけを `effective` へ置換し、
   `effective` 節 (決定・承認日・承認の対象・承認を記録した commit・D 番号を振った fold・draft の出所と sha256・校正 walltime・
   verifier hard timeout の 3 値) を足す。**発効 commit 自身の hash は bundle に書かない** (事前登録 §0 の自己参照禁止)。
   承認情報は役割別の field に分ける — 承認の対象 (提示 snapshot 内の資料とその実値) と、承認を記録した commit と、
   D 番号を振った fold は別物である。
2. **束縛の掛け方。** 校正・本走・再検証は発効 commit の detached submit-tree (1 job 1 木) を `--repo-root` とし、
   `--bundle` はその木の tracked path を指す。runner (repo 外、D95) は投入直前に sha256 を照合し、不一致なら投入しない。
   集計は `--accept-ruling-sha` / `--accept-bundle-sha` を各 1 値で明示する。
3. **本走の未完走の扱いは 2 分岐。** 保全済みで verifier 未開始の枠は元の `verify` に `--resume` を足して初回 verifier を
   走らせ、verifier が起動済みで未完走の枠だけ同一 trace の `reverify` を 1 回許す。一律に `reverify` へ送ると前者を回復できない。
4. **費用の判定基準は dispatch の Elapse の和**とし、runner の内部 monotonic 集計は暫定値として別記する。
5. **論文ストーリーの限定の置き場。** 日付版は凍結物なので編集せず、腐らない入口 (`docs/paper-story/README.md`) の
   stale 注記へ積む。新しい日付の版は作らない (D1858)。

**理由:**
- 発効束は「承認された実験構成」であり、値を変えれば承認の対象が変わる。`status` は発効という事実の記録であって構成値ではない。
- 固定 checkout への束縛は D2186 項 1 の要求そのもので、木を分けるのは同一 worktree の dispatch が直列になるためである。
- runner の bundle 検査は `status` を見ないので、draft のまま走らせる事故は手順 (tracked path の固定と投入直前の照合) で防ぐ。
  新しい機械 gate は足さない (要求外)。
- 未完走の 2 分岐は runner の実装 (`reverify` は verifier 起動済みの枠だけを受理し、保全済み・未開始は `verify --resume` を要求する)
  と事前登録 §6.4 の両方に従う。
- 費用の上限は「job 実消費 (dispatch Elapse の和)」と事前登録 §7 が定めており、runner の内部計時はこれを代行しない。

**却下した選択肢:**
- 発効束の `status` を検査する機械 gate の新設 — 要求外の追加防壁であり、手順と tracked path の固定で足りる。
- 本走の未完走を一律 `reverify` に送る — 保全済み・verifier 未開始の枠を回復できず、未確定を増やす。
- 論文ストーリーの日付版 §8 を書き換える / 新しい日付の版を作る — 前者は凍結規則違反、後者は一項目の決着のために版を作ることになる。
- 発効 commit を先に main へ land してから校正を始める — D2186 項 1 は固定 checkout を要求するだけで main 着地を条件にしていない。
