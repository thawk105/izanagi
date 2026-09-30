---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: worktree-dev-wave-vhash-workload-space
seq: 2
---

## 再発

### F1079

- **再発: 2026-09-30** — VHash md_29 wave の land 前の前方 merge で、変種が出た。main 側 (vhash-interval-gc) が `orchestrator/tests/test_condition_meaning_gate.py` に site 数の総和 pin `sum(_CONDITIONAL_BRANCH_SITE_COUNTS.values()) == 277` を新しく足し、wave 側は同じ辞書の `IZANAGI_CICADA_VLIFE` を 37 → 44 にしていた。文字の競合は 0 件で、合成結果の総和 pin は wave の +7 を含まず、合成後の login 自走で赤になった (受入 1 回目の後、land の PREP で検出)。手で直さず abort し、同じ file を変えた lock-order-axis の着地後に main を 1 回取り込み、Codex が辞書を数え直して 298 に書いた merge で受入を取り直した。「同じ行を同値へ」でなく「一方が足した派生値の pin が、他方の変える要素を数える」形で、F1079 の再発検知 (両側で対になった数値 literal の比較) には掛からない。恒久対応は F1079 のまま (合成後のコードから派生値を導出する) に加え、condition gate など件数 pin を持つ登録簿を両側が変えた取り込みでは、合成後に該当 test を自走してから commit する。

### F139

- **再発: 2026-09-30** — VHash md_29 wave で、Cicada 計器 patch の拡張 (走行末の熱いキー走査) が実機の制約を机上で外し、計算ノードの smoke を 2 回空振りさせた。(1) Codex author が走査を `ycsb_cicada.cc` の `#if IZANAGI_CICADA_VLIFE` に置き companion 登録した (condition gate は owner TU `transaction.cc` の前処理しか観測しない。smoke 前に親の静的確認で見つけて owner TU へ移した)、(2) 移した fix で owner TU の分岐宣言を 49 のまま残し、gate が実数 44 と照合して拒否 (37898.nqsv、61 s)、(3) 走査が `include/ycsb.hh` にだけある `YCSB`・`Storage::YCSB` を使い、workload ごとに compile される `transaction.cc` で compile error (37937.nqsv、99 s)。(2) は login の自走でも `test_condition_meaning_gate.py` の在庫 test が赤だったが、Codex の sandbox は pytest・dispatch を使えず、親も smoke 前に走らせていなかった。3 回目で成立 (37961.nqsv)。恒久対応は F139 のまま (実機の書式は先例の実装か最安の生死確認で確かめてから書く) に加え、gate 登録を触る wave は統合直後・smoke 前に condition gate test を login 自走する (記憶 condition-gate-meaning-sees-owner-tu-only)。
