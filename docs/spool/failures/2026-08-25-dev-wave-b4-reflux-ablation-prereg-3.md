---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-b4-reflux-ablation-prereg
seq: 3
---

## 再発

### F24

- **再発: 2026-08-25** — 偽完了が 5 回、うち 1 回は**走行中の変異 harness のツリーへ干渉**した。
  親は完了通知を信じて `git checkout -- orchestrator/campaign/p3_s4_loop.py` を実行し、
  注入中の変異を消して probe 走行を汚染した (結果は破棄し clean な本走をやり直した)。
  原因は 2 系統。(1) **Monitor tool の実行環境から detach した計算ノード job のプロセスが
  `pgrep` で見えない** — 生存判定を主条件にした待ち手は、そこでは構造的に常に「不在」を返す。
  (2) 自作判定器のバグで、`pgrep` が**自分のシェルラッパーを数え**、プロセス不在を即異常として
  早期終了した。F24 の恒久対応は既に「`.done` の存在 + exit code だけを見る」「pgrep の
  自己マッチに注意する」と書いており、**書いてある対策を実施しなかったことによる再発**である。
  実施していれば (1) も無害だった (`.done` は producer だけが書くため環境から見える)。
  再発検知は F24 既存のとおりで足りる — 追加の機構は作らない。
