---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-27
wave: worktree-dev-wave-t2797-b5-v2-prep
seq: 2
title: [T-2797] B-5 v2 は発効せず見送り (ユーザー裁定) — backoff の値 1 個での LLM 対照は査読の決め手になりにくく、「なぜ LLM か」は関数単位の軸で取り直す (docs、branch worktree-dev-wave-t2797-b5-v2-prep)
---

## 本文

- ユーザー裁定 (2026-09-27): 発効確認の提示に対し「トップ会議に論文を通すのに重要な図になりそう？そうでないなら時間の無駄だと思う」→ 親の見送り推奨に「見送りで良い」。記録は {{D:b5-v2-shelved}}。
- 本走・計算の投入はしていない。D2258 の実装は main に残す。

## 次の一手差分

### 新規

- {{T:function-axis-llm-contrast}} **P2・新規 (段階 E の後)**: 関数単位の軸 (silo-function-policy) で「LLM 対 非 LLM 生成器」の対照を設計する ({{D:b5-v2-shelved}})。段階 E ([T-2865]) が形になった時点で、同じ評価数の予算で LLM と random 等を比べる事前登録を起草する。D2258 の実行契約 (1 評価 1 job、429 の保留、LLM 親の起動器) を流用できるか先に確かめる。計算の投入前に node 時間をユーザーへ示す (D2212 項 4)。

### 見送り

#### 研究・計測系

- [T-2797] B-5 生成器対照 (backoff の値 1 個での LLM 対 random / sweep) — 理由: ユーザー裁定で v2 を発効しない ({{D:b5-v2-shelved}})。査読の「なぜ LLM か」には列挙できない空間での対照が効くので、関数単位の軸で取り直す。v1 cohort は閉鎖済み (v1 §15)、v2 の実装は main に残る。
  base: 90f537c2612ad35d7a043dd4e992b06331d9d72e3e11f80be68fad30a707b24e
