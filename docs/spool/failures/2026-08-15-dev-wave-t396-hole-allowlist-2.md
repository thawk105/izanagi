---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-15
wave: dev-wave-t396-hole-allowlist
seq: 2
---

## 再発

### F256

- **再発: 2026-08-15** — 段 3 レンズ A の初回投入が上流分類器に遮断され、model call 16 回・
  出力 0 bytes を空費した (`turn.failed` の message = `This content was flagged for possible
  cybersecurity risk`、`evidence_status=complete`、`codex_exit_code=1`)。
  親は F256 の恒久対応を知っており、**prompt 冒頭には防御目的を明記していた**。
  遮断したのは、段 2 の結果を受けて**後から追記した「最優先の争点」節**が
  「回避する C++ 文字列を構成できるなら具体的に示せ」と攻撃成果物の作成を求めていたことである。
  防御的枠組みは prompt 冒頭に 1 度書けば足りるものではなく、**追記した節を含む個々の指示文が
  それぞれ攻撃成果物を要求していないことを、投入前に確認する**必要がある。
  再投入は被覆監査の枠組み (契約項目と機械執行の差分表・既存境界テストの被覆評価) へ
  書き直して成功した。
