---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: worktree-paper-story-vhash-setup
seq: 1
---

## {{D:paper-story-vhash-series}}. VHash と timestamp forwarding の論文を 3 本目の論文ストーリー系列として新設する

**決定 (ユーザー指示 2026-09-29):** `docs/paper-story-vhash/` を、MVCC の版探索・履歴保持・GC を
少数版の hot 配置 (仮称 VHash) と選択的 timestamp forwarding で減らす研究の論文ストーリー系列として置く。
契約は D1637 (1 系列 1 ディレクトリ、日付付き凍結スナップショット、腐らない入口 README、正典は decisions・worklog・
`output/insights/` の一次資料) をそのまま適用する。出発点はユーザーが提供した研究メモで、
`source-memo-2026-09-29.md` として凍結保存し、構想の記録として扱う (一次資料ではない)。
系列を前進させる並行 wave は README と版を編集せず、成果物を `output/insights/<日付>/vhash-<主題>/` と
spool fragment に置き、次の版の wave がそれらから全面再導出する。

**理由:**
- ユーザーが 2026-09-29 に「これで論文を一本書こうかと考えている」「docs/ に新しい paper-story のディレクトリを
  専用に設けてくれ」と明示した。主題は人間が設計する MVCC 機構であり、本体論文 (AI による CC 合成) とも
  backoff 系列とも違う。
- 2026-09-20 のユーザー方針「一本の論文に多くを載せる」は backoff 診断を本体論文へ畳む判断であり、
  今回はユーザー自身が別論文を明示したので、この方針の解除に当たる明示がある。
- 並行 wave が README の同じ行を奪い合わないよう、wave の書き込み先を一次資料と fragment に限る。

**却下した選択肢:**
- `docs/paper-story/` の本体論文の版に節を足す — 主題が違い、本体論文の全面再導出が必要になる (D1637 の理由と同じ)。
- wave ごとに README の stale 注記へ追記させる — 並行 wave が同じ節を編集して衝突する。
- 出典メモを要約だけにして原文を残さない — 以後の版がメモの訂正点 (メモ §30) を参照できなくなる。
