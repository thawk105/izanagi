---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-8c-formal-consumer-wiring
seq: 1
---

## {{D:formal-consumer-never-issues-non-aborted}}. formal consumer は `aborted=False` を構造的に発行しない — P6 が未実装である以上 fail-closed だけが誠実な実装であり、caller 注入は恒真化する

**決定:** 8c formal consumer の到達可能な結果を `FormalContractRejected` と `P6Unavailable` の
2 型に限り、どちらも `OriginSealed(aborted=True, constraint_class_sha256s=())` へ写す。
**`aborted=False` を構成する式を production code に置かない。**
「将来 P6 が来たら通る」分岐も置かない。本 wave の新規・変更 production 13 ファイル全体を
AST 走査し、keyword `aborted=False` と `OriginSealed(False, ...)` の positional 構築の
双方が存在しないことを機械検査する (ledger に wave 前から存在する feasibility 用の
positional 構築 1 箇所だけを文脈で allowlist する)。

**根拠となる実測:**

- **P6 契約 (`derive_p6_cut`) はコード全体に存在しない。**
  `grep -rn "derive_p6_cut\|P6Derived\|P6NotDerived" --include=*.py` が 0 件で、
  設計文書に 1 回出るだけである。D138 は「実装は発火 artifact 0 件のため行わない」、
  D156 は「境界テストを含む機械実装は **P6 実装 wave** と cap-lift receipt 設計の所有であり、
  本決定は規範の発効のみを行う」と定める。**その wave は未実施である。**
- 設計 §4.1 の条件 8 は「P6 result が `P6Derived` で marginal set が空でない」を要求する。
  実装が存在しない以上、この条件は**判定不能**である。

**却下した選択肢:**

- **P6 の判定結果を caller から注入させ、evidence 集合 digest へ束縛する** — 段 3 の敵対レンズ
  2 本が独立に**恒真化**と反証した。集合 digest は「同じ evidence を見た」ことしか示さず、
  D138 の witness 正規化・反証 test・`B \ C_exact`、D156 の認定、admission への限界効果を
  何一つ証明しない。caller は整合した synthetic evidence 集合と `P6Derived` を同時に自作できる。
  親の provisional 裁定はこれだったが、反証を受けて撤回した。
- **本 wave で `derive_p6_cut` を自前実装する** — 段 2 プランの案。D156 が機械実装を別 wave の
  所有と定め、認定に 4 要件 (end-to-end calibration / conjunct 単位の反転変異 /
  独立検査者 attestation / 認定記録と失効照合) を課している。プランはその 4 要件を 1 つも
  扱っていなかった。
- **「将来 P6 が来たら通る」分岐を置いておく** — 発火しない恒真な死にコードであり、
  読み手に実装済みの印象を与える。

**帰結:** 本結線は fixture 経路で条件 1〜7・9・10 と §4.2 双射を実際に駆動できるが、
**`OriginSealed(aborted=False)` を発行できる状態にはならない。**
これは欠陥ではなく、今日の実態に対する誠実な表現である。

## {{D:private-seam-not-a-trust-boundary}}. ledger の private seam 経由の迂回は塞がず保証限界として明記する — underscore は信頼境界ではない

**決定:** raw public 3 API (`read_origin` / `commit_event` / `read_sealed_batch`) を公開面から
除去し issued capability を必須にするが、`_production_store()` / `_fixture_store_for_test()` →
`_locked()` → `_commit_locked()` を直接呼ぶ経路は塞がない。
**保証限界として module docstring・worklog・受入報告へ明記する。**

> この結線は「ledger の private seam を直接呼ぶ caller が居ない」という**運用前提の上でのみ
> 成立する**。formal consumer を通らずに `certifiable` terminal を作る経路は Python の
> 同一 process 内では構造的に塞げない。

**根拠:** 段 6 の敵対レビューが実測した。raw 3 関数を消しても、既存の public `OriginSealed` で
整合する counters/class を構築して private seam へ渡せば、typed client・formal receipt・
条件 1〜10 を一度も通らずに `terminal_status="certifiable"` にできる。

**理由:** 塞ぐには commit 時に formal receipt を要求する = **ledger の受理集合の変更**が要り、
V-6 と同型の scope 外変更である。D198 の決定にも隣接する。
設計 §3.6 が create-only について既に採った形 (運用前提として明記する) と同じ扱いにする。

**却下した選択肢:** underscore を信頼境界と見なして「塞いだ」と名乗る — 自己申告であり、
実測が反証している。

**残余:** ledger 側で formal receipt を要求するかは V-13 としてユーザー裁定へ返す。

## {{D:receipt-resolution-out-of-scope}}. execution receipt の実体解決は `result-evidence/v1` の exact key 集合を超えるため実装しない

**決定:** provenance が claim する `execution_receipt_sha256` は**字句形式 (64 hex) しか
検査しない**。receipt bytes を解決して digest を再計算する検査は実装しない。
保証限界として明記し、V-14 としてユーザー裁定へ返す。

**根拠:** 設計 §3.2 の `evidence` は `ordered_wal_ref` と `execution_provenance_ref` の
**exact 2 参照**しか持ち、receipt への参照が無い。consumer に receipt を解決させるには
record schema へ第 3 の `{path, sha256}` を足す = 批准済み exact key 集合の改訂が要り、
producer (fixture と将来の trusted harness) が receipt bytes を deterministic path へ書く
義務も生じる。実装 wave の裁量を超える。

**経緯:** 焦点再レビューがこの残余を partial として指摘し、親は当初 fix を指示した。
**その指示が誤りで、fix 子は契約衝突を見抜いて実装せず停止し報告した。**
親は子の判断を採り、scope 外へ裁定し直した。

**却下した選択肢:** consumer が receipt bytes を推測・生成して照合する — 検査器が被検査物を
作ることになり恒真化する。
