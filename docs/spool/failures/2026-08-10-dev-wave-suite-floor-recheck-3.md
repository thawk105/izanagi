---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-suite-floor-recheck
seq: 3
---

## 新規

### {{F:acceptance-in-synthetic-checkout}}. 計測 driver が複製 checkout で受入を走らせ、本来緑のテストが 59 件赤くなった [計測汚染] [テスト代表性]

- 事象: before/after の受入 wall を同一 allocation で測るため、driver が repo の複製 checkout を
  作ってそこで受入全走を実行した。結果は **59 failed / 19 errors / 7492 passed / 1431.86 秒**
  (request `898290.nqsv`)。`orchestrator/tests/test_codex_reasoning_ab.py` が丸ごと error、
  `test_t126_pegasus_tools.py` などが failed。driver は arm を無効と判定して正しく止まったが、
  計算ノードの 1 走 (約 24 分) を空費した。
- 根本原因: 受入全走は wave の worktree という**特定の環境前提**の上でだけ緑になる。
  複製 checkout はその前提 (submodule の実体化状態、path 依存の repo root 解決、
  git 設定など) を再現しない。driver の設計時に「複製でも同じ集合が緑になる」ことを
  確かめていなかった。
- 恒久対応: **before/after を測る driver は複製 checkout を作らず、wave の worktree 上で
  `git checkout --detach <sha>` して測る**。開始時の HEAD と `git status --porcelain=v1` を保存し、
  job の最後に必ず復元して byte 一致を検証する (異常終了時も trap で復元)。
  本 wave はこの形へ作り直し、request `898551.nqsv` で完走した (`source_repo_restored: true`)。
- 再発検知: 計測 driver の arm が受入 shape を使う場合、**最初の arm の passed 件数が
  直近の受入実測と一致するか**を driver 自身が検査する。一致しなければ環境差として止める。

### {{F:spool-fold-carry-legacy-stub}}. `spool_fold` の carry 解決が序数なし旧形式 stub を実体とみなし、base 照合の保護が効かない [恒真ゲート]

- 事象: worklog fragment の `更新` に付ける `base:` digest が、[T-201] では**実本文ではなく
  `- [T-201] 変わらず (前エントリ参照)` という序数なしの旧形式 stub** の digest と一致した。
  実本文 (archive の 2 箇所) の digest はいずれも不一致で拒否された。
- 根本原因: `tools/spool_fold.py:1151` の `carry_re` は `変わらず ((N) 参照)` と `(N)` の 2 形式しか
  stub と認識しない。過去エントリに存在する `変わらず (前エントリ参照)` は carry と判定されず、
  `substantive_digest` がそこで停止して stub 自身の digest を返す。
- 恒久対応: 未実施。carry 鎖にこの形式を含む item では「他 wave が先に本文を書き換えていたら
  fold が止まる」という保護が実質的に無効になるため、`carry_re` の拡張か、旧形式 stub を
  carry として解決する経路の追加が要る。起票のみ行い、本 wave では実装しない。
- 再発検知: `carry_re` に一致しない `変わらず` 形式が worklog / archive に存在するかを
  検査する meta-test。現時点では未実装。
