---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2124-s1-epoch-historical
seq: 2
---

## 再発

### F606

- **再発: 2026-09-02 (near miss)** — [T-2124] の段 1 で 32 worktree を exact path 集合 x (committed 三点 diff + staged + untracked) で走査し、重なるのは `orchestrator/campaign/artifact_admission.py` の 2 本 (T-733) だけ、本 wave は同 file を編集しないので無害、と正しく判定した。走査自体に穴は無かった。にもかかわらず衝突は起きかけた — 段 2 のプランが、その触らない file が定義する定数 `CAMPAIGN_VERIFIER_EPOCH_SCOPE` の**現在値を test へ literal で焼き込む**ことを提案しており、T-733 はまさにその文言を exact 24 path から curated exact 62 path へ変えていた。採用していれば、正しい S-1 実装のまま T-733 の着地と同時に本 node が落ちた。段 3 のレンズ B が稼働 worktree の現物を読んで検出し、段 4 で当該提案を不採用にした (既存 node が同じ変異を既に殺しており検出力も増えないため二重に不採用)。型は F606 と同じ「走査の網が実際の編集予約より狭い」だが、本件が足す軸は **危険が編集面に無い**ことである。自分が触る path の集合ではなく、**自分のテストが値として固定する対象を誰が所有しているか**が問われた。恒久対応は F606 既存の「落ちた面は『無い』と書かず、走査面を明示して限定した結論を書く」で変わらない。運用としては、test へ他 module の定数値を literal で固定する提案が出た時点で、その定数の定義 file を稼働 wave の走査対象に含めて所有者を確かめる。既存の作法で足りる — 定数を production から参照する形 (本 wave が維持した既存 assert の形) なら、この危険は原理的に生じない。
