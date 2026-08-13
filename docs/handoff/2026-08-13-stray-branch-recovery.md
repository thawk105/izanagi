# 取り残し branch の仕分け・回収 wave
- 目的: 指定 3 branch を内容・blob で仕分けし、必要な成果だけを安全に回収する
- 状態: 作業中
- 最終更新: 2026-08-13 11:50 JST
- 基準コミット: 004debad6467cff15ce164fab43b54934d759d8e

## 完了した中間成果
- AGENTS.md / CLAUDE.md / dev-wave dispatcher / cleanup dispatcher・overlay を読了。
- 対象外: worktree-dev-wave-t907-t908-t910-acceptance-integrity、worktree-dev-wave-t657-t660-g2-activation。branch 削除は禁止。
- branch 名の worklog/archive grep を実施。t139-addendum-b と cleanup-submodule-recurrence には既回収を示す記録があるため、commit/blob で再検証中。
- 段 4 裁定: 3 branch 全て「不要と判断して掃除対象として報告する」。根拠を worklog fragment に記録した。

## 未完の作業と次の一手
- docs 検査、spool dry-run、受入、commit、provenance、段 9 land を完了する。

## 落とし穴・気づき
- path の有無を land 判定に使わない。spool fragment の不在は fold 済みでも起こる。
- Pegasus login node。pytest/build は tools/run_tests.py 経由のみ。
- dev-wave 改善候補: 現時点なし。
- known-red は再 land 非推奨なので t1027 との merge 試行条件は不成立。
