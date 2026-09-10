---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-11
wave: dev-wave-t2551-evidence-root
seq: 1
title: [T-2551] 段4jobのcanonical証拠保存先をPythonへ渡し直した
---

## 本文

- D1936項5の局所修正。相対path指定時にshellとPythonの保存先が分かれる不整合を閉じ、
  絶対path正常系とD1773/D1801のCMAKE_PREFIX_PATH契約を維持した。新規実験は行っていない。
- 独立レビュー2本のreal/must-fixは0。export削除のM1はrelativeだけKILLED、absoluteと実consumerは成功。
  job契約file全体82 passed、変異baseline5 passed。証拠と逐語は
  `output/insights/2026-09-11/t2551-evidence-root/README.md`。
- authorのテストはqstat preflight失敗で子未起動、親が計算ノードで実走した。
  起動時のsubmodule部分checkoutは専用worktree内で復元し、startup再検査を通した。
- 段4関連の稼働CC precheckはdocs-onlyで実装所有重複なし。受入前のphase追記競合は両方を保持して解消。
- 工数はCodex author1本・独立review2本。全てaccepted、gpt-6-astra/medium。
- 記録前受入は23,070 passed / 68 skipped、child-green、red node 0。tested tipは
  `df3bd8ce5e2f8e270d1a2e736ec48bdf959c224d`、前後fingerprint一致。新規除外は0。
  check_docs/check_codex_agentsは成功、統合後の全史provenanceは9637件・新規違反0・既知56。
- dev-wave改善候補は初期化中断後の再試行成功と実checkout不整合の扱い。専用handoffへ記録し、
  ユーザー指定に従い改善実装・新規仕組み・次wave起動・pushは行わない。

## 次の一手差分

### 完了

- [T-2551] D1936項5のcanonical evidence root再exportと既存job契約整合を完了した。
  remaining: none
  base: c77159b5f1eac230afae2ddc38568c1a5fb9885d6373f0b3556ac755770188c9
