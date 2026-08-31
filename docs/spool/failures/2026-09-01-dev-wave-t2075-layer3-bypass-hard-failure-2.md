---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t2075-layer3-bypass-hard-failure
seq: 2
---

## 再発

### F300

- **再発: 2026-09-01** — probe 走が `共有木の事後検査に失敗: source/main 共有木の観測 bytes が
  変化した` で `rc=125`。原因は 2026-08-26 項と同じ**共有 checkout の untracked 集合の変動**で、
  走行中に自分の作業木へは 1 byte も書いていない。この時刻の機体では codex 子が 8 本並行しており、
  未追跡 path は常に動く。既知の恒久対応どおり独立 clone を `--source-repo` へ渡して本走し、
  `rc=0` / 5-of-5 KILLED を得た。
  **新しい事実 1 件:** 2026-08-26 項は clone の submodule URL をローカルへ書き換える手順を必須として
  記録しているが、**変異の runner argv が submodule を必要としない焦点走 (今回は
  `orchestrator/tests/test_trial_registry.py` の 1 file) なら、submodule を一切初期化しない
  `git clone --shared` だけで probe も本走も完走する。** submodule の書き換えが要るのは、
  runner が submodule を読む走に限られる。
  なお probe 走は `rc=125` で終わったが**変異 5 件の失敗 node は全件収集できていた**ため、
  期待 node の完全集合を得るという probe の目的は達している。事後検査の赤を理由に probe をやり直す
  必要はなく、本走だけを独立 clone で取り直せばよい。
