---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: worktree-dev-wave-vhash-workload-space
seq: 2
---

## 再発

### F139

- **再発: 2026-09-30** — VHash md_29 wave で、Cicada 計器 patch の拡張 (走行末の熱いキー走査) が実機の制約を机上で外し、計算ノードの smoke を 2 回空振りさせた。(1) Codex author が走査を `ycsb_cicada.cc` の `#if IZANAGI_CICADA_VLIFE` に置き companion 登録した (condition gate は owner TU `transaction.cc` の前処理しか観測しない。smoke 前に親の静的確認で見つけて owner TU へ移した)、(2) 移した fix で owner TU の分岐宣言を 49 のまま残し、gate が実数 44 と照合して拒否 (37898.nqsv、61 s)、(3) 走査が `include/ycsb.hh` にだけある `YCSB`・`Storage::YCSB` を使い、workload ごとに compile される `transaction.cc` で compile error (37937.nqsv、99 s)。(2) は login の自走でも `test_condition_meaning_gate.py` の在庫 test が赤だったが、Codex の sandbox は pytest・dispatch を使えず、親も smoke 前に走らせていなかった。3 回目で成立 (37961.nqsv)。恒久対応は F139 のまま (実機の書式は先例の実装か最安の生死確認で確かめてから書く) に加え、gate 登録を触る wave は統合直後・smoke 前に condition gate test を login 自走する (記憶 condition-gate-meaning-sees-owner-tu-only)。
