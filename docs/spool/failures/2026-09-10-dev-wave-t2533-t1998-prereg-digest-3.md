---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-10
wave: dev-wave-t2533-t1998-prereg-digest
seq: 3
---

## 再発

### F42

- **再発: 2026-09-10** — 事前登録の束縛のために consumer へ `subprocess.run` を 2 箇所足したが、親の焦点走の集合を「変更した 2 file + 直接の path/basename pin 2 file」から組んだため、repo 全体を AST 走査する `test_ccbench_spawn_sites.py` の reviewed inventory を落とした。2026-08-28 の再発と同じ機構である。今回は最終受入まで行かず段 6 の敵対レビュー B が静的に指摘し、親が当該 file を単独走して 2 failed を現物で確認してから fix へ回したため、費用は焦点走 1 回 + fix 子 1 本に収まった。**新しい process 起動 site を足す wave では、親の焦点走の集合に `test_ccbench_spawn_sites.py` を必ず入れる。** module 名の grep では出ない層である。
