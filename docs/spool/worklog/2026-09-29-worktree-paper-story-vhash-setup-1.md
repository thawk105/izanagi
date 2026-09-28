---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: worktree-paper-story-vhash-setup
seq: 1
title: VHash と timestamp forwarding の論文ストーリー系列を新設し、並行 wave の投げ文を用意する (docs のみ、branch worktree-paper-story-vhash-setup)
---

## 本文

- ユーザー指示 (2026-09-29): 外部の対話 AI との議論をまとめた研究メモ (VHash・選択的 timestamp forwarding・GC の協調) を
  貼り、「これで論文を一本書こうかと考えている」「docs/ に新しい paper-story のディレクトリを専用に設けてくれ」
  「図やグラフを多用してわかりやすく」「dev-wave を並列で投げまくって調査・試行錯誤・実装・実験を進めたい」
  「投げ文は /work/1/SFC/tanabe/tmp に md_1.txt のように外出しして」と依頼した。`/work/1/SFC/tanabe` は実在せず、
  実在する `/work/1/SFC/tanab/tmp` の下に置いた。
- 新設の判断は {{D:paper-story-vhash-series}}。初版 `2026-09-29.md` は Mermaid 24 枚・文字の図 1 枚・画像 0 枚。
- 確かめた事実: CCBench の `cc/silo/transaction.cc` には `#if TRACE` があり、`cc/cicada/` の全ファイルには `TRACE` の
  文字列が無い。`orchestrator/verifier/` にも `cicada` の文字列が無い。Cicada の variant は現状、正しさ検査器を通せない。
- 並行 wave の投げ文 6 本 (文献・実測・正しさ検査・小さいモデル・配置の微小計測・forwarding 試作) を repo の外に置いた。
  各 wave は下の新規 item に対応する。

## 次の一手差分

### 新規

- {{T:vhash-related-work}} **P1・新規**: VHash 論文の文献調査と新規性の位置づけ (Cicada・TicToc・MVCC の GC・timestamp 調整系の原典確認、CCBench 論文 §7 の原典照合)。入口は `docs/paper-story-vhash/README.md`。
- {{T:vhash-cicada-version-measure}} **P1・新規**: Cicada の版探索長・hot 相当の当たり率 (K 別の反実仮想)・forwarding の機会・GC 境界の遅れ・生存版数を診断計器 patch で実測する (メモ §29 段階 1)。
- {{T:vhash-cicada-verifier}} **P1・新規**: Cicada に検査用トレースを足し、izanagi の正しさ検査器で多版の履歴を検査できるようにする。壊した Cicada の positive control も用意する (forwarding 試作の正しさゲートの前提)。
- {{T:vhash-forwarding-model}} **P1・新規**: 選択的 forwarding のプロトコルを小さいモデルで書き、reader・writer・forwarding・GC の割り込みを全探索して serializability を検査する (メモ §29 段階 2)。
- {{T:vhash-hot-block-microbench}} **P1・新規**: 版選択の配置を微小計測で比べる (連結リスト・連続配置 + scalar・連続配置 + SIMD、K・版の深さ・値の大きさ)。
- {{T:vhash-forwarding-prototype}} **P1・新規**: Cicada に cold 境界 (論理的な K 版) で発火する選択的 forwarding を inert variant patch として試作し、abort して再実行する対照と比べる (GC 保護は変えない、メモ §29 段階 3)。
- {{T:vhash-story-v2}} **P2・新規**: 上の 6 件の一次資料が揃ったら、`docs/paper-story-vhash/` の 2 版目を全面再導出する (図を先に)。
