---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-t1510-sort-swo-sigabrt
seq: 3
---

## 新規

### {{F:zero-diff-worktree-does-not-isolate-environment}}. 差分ゼロの worktree で再現しても環境要因を切り分けたことにならない [計測汚染] [手順漏れ]

- 事象: 焦点走で出た赤 1 件について、親が「差分ゼロの素の main worktree を作って再現した」ことを
  根拠に repo 側の決定的な赤と判断し、並行セッションへ配った。実際は親のセッション環境の
  `FORCE_COLOR=3` / `COLORTERM=truecolor` に依存する赤で、受入経路 (計算ノード) では緑だった。
  中継側は 8 セッションへ配布し、既に修理済みの別 wave と重複作業を発生させかけた。
- 根本原因: **差分を消しても環境変数は同じセッションから継承される。** worktree を素にする操作は
  tree の状態だけを揃え、process の環境を揃えない。親は「repo 側の性質」の主張に対して
  tree だけを対照にし、環境を対照に入れなかった。
- 恒久対応: repo 側の性質を主張する再現は、**tree と環境の両方を揃えて**行う。
  疑わしい環境変数は `env -u <VAR>` で外した対照走を必ず添える。親が実測した対照は
  ambient で rc=1、`env -u FORCE_COLOR -u COLORTERM` で rc=0 だった。
  非帰属の赤を他セッションへ配る前に、この対照を根拠として添える。
- 再発検知: 「素の main で再現した」という文言を根拠にした非帰属判断が、対照走の記録を
  伴わずに現れること。

### {{F:oracle-discards-candidate-stderr-hides-root-cause}}. 候補実行の stderr を捨てると signal 番号しか残らず真因に到達できない [手順漏れ]

- 事象: sort SWO oracle が候補実行を `stderr=subprocess.DEVNULL` で起動するため、
  実行ファイルが abort しても `candidate-run-signal-6` しか残らなかった。真因は
  ccbench の `assert(data_ != nullptr)` で、stderr にはその 1 行が出ていた。
  診断が消えた結果、複数セッションが環境要因 (`RLIMIT_AS` + hugepage、masstree の config.h 不足) を
  仮説として立て、うち 1 つは裁定集約経由で他セッションへ配布された。
- 根本原因: 構造化して返すべき失敗理由を、観測経路ごと捨てていた。compile 側には
  `CompilerDiagnostic` による bounded 診断があるのに、run 側には対応する経路が無い非対称。
- 恒久対応: T-1524 が所有する。compile 側と同じ bounded 診断
  (上限 bytes + 全長 + sha256 + 切詰めフラグ) を run 側にも設ける。候補の stderr は
  未信頼入力なので、compile 側と同じ扱いで境界を保つ。
- 再発検知: 候補由来の失敗が signal 番号だけで報告され、なぜ壊れたかを構造化して返せていないこと。
