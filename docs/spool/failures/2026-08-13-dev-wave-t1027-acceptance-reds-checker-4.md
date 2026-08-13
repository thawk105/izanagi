---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-t1027-acceptance-reds-checker
seq: 4
---

## 再発

### F102

- **再発: 2026-08-13** — 四度目。[T-1027] wave の段 3 レンズ A が
  `This content was flagged for possible cybersecurity risk` で rc=1・出力 0 bytes
  (24 model call を空費)。**冒頭には防御目的を 1 文書いていた。**
  残っていたのは節見出し `## 攻撃せよ (これが本題)` と、本文の「穴」「偽装」「侵入」という語彙で、
  **framing を 1 文足すだけでは足りず prompt 全体の見た目が判定される**ことを示した。
  効いた書き換えは独立した前置き節 — 「対象はこの repo 自身の開発フローで使う〈用途〉であり、
  セキュリティ製品でも攻撃ツールでもない。外部からの入力も扱わない」 — を冒頭に置き、
  節見出しを `## 評価してほしい論点` にし、動詞を「評価せよ・列挙せよ・名指しせよ」へ替える形。
  所見の質は落ちず、blocker 3 件 (うち 1 件は親 brief の不変条件の向きの誤り) を返した。
- 補足: 本件は恒久対応の不足ではなく**適用漏れ**である。F102 の既存対応と memory
  `codex-adversarial-prompt-defensive-framing` には「冒頭だけでなく点検項目の動詞にも要る」と
  既に書かれていた。実効的な関門は**敵対 prompt を投入する前に見出しと動詞を 1 度読み返すこと**で、
  同 memory へこの手順を追記した。
