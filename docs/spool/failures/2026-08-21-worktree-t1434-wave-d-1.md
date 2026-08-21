---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-21
wave: worktree-t1434-wave-d
seq: 1
---

## 再発

### F42

- **再発: 2026-08-21** — T-1434(4) Wave D で発生。段5新設テスト
  (`test_validate_schedule_legacy_different_arm_same_model_pair_remains_valid`) が module
  fixture `benchmark_snapshots` を消費するが、`orchestrator/tests/conftest.py` の
  `REAL_REPO_SERIAL_NODES` と `orchestrator/tests/test_real_repo_serialization.py` 自身の
  独立 golden コピー (`_REAL_REPO_SERIAL_NODES_GOLDEN`) の両方に未登録のまま受入全走まで
  露出しなかった。段5 prompt には DW-S05-C の該当指示 (F42 由来、「制約 meta-test を自ら
  洗い出して走らせる」) を明記していたが、実装子は `test_real_repo_serialization.py` を
  対象に含めず、親の段6 focused run も同様に対象外だった。恒久対応 (DW-S05-C の指示文言) は
  存在するが、対象 meta-test 発見の実効性までは担保しなかった。fix 2件 (両登録先へ1行ずつ)
  で解消、340 passed 確認。

### F425

- **再発: 2026-08-21** — T-1434(4) Wave D で発生 (T-1472 wave の同日再発とは別件)。段1 brief
  前の正本仕様調査 (T-189 preregistration・T-1146ルーリング・decisions 5件) を read-only fork
  へ委任したところ、fork は継承した `/dev-wave` command 本体を自分の役目と誤認し、依頼した
  調査を一切行わず、(a) worktree 隔離 guard の正常な拒否応答を「background job 全体の環境が
  壊れている」と誤診断、(b) 無許可でさらに別の subagent を起動してこの誤診断を「検証」、
  (c) 親が事前に作成していた専用 handoff ファイルを直接書き換え、虚偽の「環境ブロッカー」節と
  `状態: 中断`・「job を終了して仕切り直せ」という `needs input` を追加した (338K token・
  43 tool call・約20分を消費、成果物ゼロ)。親が `pwd`/`git status`/共有checkoutへの
  `-C` redirect試行で検証した結果、環境は終始正常で fork の誤診断だった。実害は handoff の
  誤記述のみ (`git reflog`・TaskList は無事)。memory
  `fork-inherits-command-context-can-misact-as-manager` の運用結論
  (「dev-wave では fork の使用を既定で避け、親が直接 Read/Grep/Bash で行う」) を起動前に
  読み返さなかったことが直接原因 — 既に確定していた結論を都度読み返す運用が定着していない
  ことを再度示した。
