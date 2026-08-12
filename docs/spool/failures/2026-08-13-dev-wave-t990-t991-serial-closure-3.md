---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-t990-t991-serial-closure
seq: 3
---

## 新規

### {{F:one-sided-interference-check}}. 干渉の検査を片側からしか行わず、refuted とした所見が受入で real に戻った [テスト代表性]

- 事象: 段 6 の敵対レビューが「新設した item 印と既存 growth-test hold の `user_properties` は
  干渉しない」を `refuted / nit` と判定した。根拠は「hold 側は `growth_hold_*` という別 key
  だけを追加する」。しかし受入全走で `test_growth_test_holds_contract.py` が赤になった。
  同 test は `dict(item.user_properties)` の**完全一致**を要求しており、対象 node は
  保留対象と実 repo 直列の両方に属していたため、新設した印が増分として現れた。
- 根本原因: 干渉は対称ではないのに、**片側 (新規側が既存側の値を壊すか) だけを検査して
  refuted と結論した。** 逆側 (既存側が当該チャネルの完全一致を要求するか) を見ていない。
  共有チャネルへの追記は「既存の値を壊さない」だけでは安全と言えない。
- 恒久対応: {{D:internal-stamp-not-public-channel}} — 内部印は公開チャネルへ載せず非公開属性へ置く。
  これにより結合自体が生じない。実体は `orchestrator/tests/conftest.py` の
  `_REAL_REPO_SERIAL_NODE_ATTR` 経路と、`orchestrator/tests/test_real_repo_serialization.py` の
  stamp 監査 (正本 node はちょうど 1 個、正本外は 0 個)。
- 再発検知: 受入全走。加えて、共有チャネルへ追記する変更では **consumer 側が完全一致を
  要求していないか**を検査項目に含める (レビュー prompt の攻撃面)。

### {{F:prose-boundary-drifts-from-implementation}}. 正本の境界を散文の除外註記で書き、論法が要件からずれて閉包漏れが 2 系統残った [ドリフト]

- 事象: `orchestrator/tests/conftest.py` の実 repo 直列正本には「意図的な除外」を散文で書いた
  註記があり、「slow oracle canary は patchharness の隔離 worktree を使い、共有 submodule
  worktree を patch しない」と主張していた。しかし当該 canary は `git worktree add --detach` で
  **共有 submodule の管理領域を登録・破棄する**。註記の主張 (patch しない) と必要な性質
  (共有資源を変えない) がずれており、註記を信じた読み手が漏れを見落とす構造だった。
  同じ註記の別項「実 external/ccbench に patch を apply/revert する writer」も、現行 test が
  `patchharness.applied` を `nullcontext` へ差し替えているため実装と食い違っていた。
- 根本原因: 正本リストの**境界条件を機械検査でなく散文で表現した**。散文は実装が変わっても
  追随せず、しかも「理由が書いてある」ことで正しさの錯覚を与える。
- 恒久対応: {{D:closure-detector-design}} の 2 本立て。共有 fixture 閉包の完全性検査は
  正本自身を seed にして機械で閉包を要求し、実接触の runtime guard は実行時の接触を
  fail-closed で拒否する。散文の註記は「機械検査が扱わない範囲」だけに縮めた。
- 再発検知: 変異 M1〜M5 (正本から node を削る 3 件と detector 自身への 2 件) が
  すべて KILLED であることを事前登録して実測した。
