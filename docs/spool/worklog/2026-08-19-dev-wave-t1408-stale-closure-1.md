---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-t1408-stale-closure
seq: 1
title: s8c 凍結検証の履歴比例costはD551で解決済みと確認し、[T-1408] のcarryを完了で閉じた (docsのみ、branch worktree-dev-wave-t1408-stale-closure)
---

## 本文

- ユーザー依頼「履歴比例costが発生する箇所を見つけて潰す」を受けて調査した。ユーザーとの
  往復で「設計是正を新たに行うのでなく、既に不要/解決済みと裁定・修正済みのものを放置して
  いないかを優先して探す」方向へ収束した。
- fork調査で D328 保留 (`freeze_verification_hold`) の全6 consumer と `growth_test_holds.py`
  (59件登録) をサンプル検査し、いずれも「保留中は重い処理自体を実行しない」正しい早期分岐を
  確認した (見せかけの保留は無い)。新規の未対応 O(履歴) 箇所も見つからなかった。
- 唯一の当たりは carry [T-1408] (entry 689 発行、F417 に対応) だった。祖先関係の実測
  (`b7f7d934` は `4cc60864` の祖先、`4cc60864` は現行 HEAD の祖先) と、対象2テストを含む
  `test_s8c_preregistration_invariant.py` + `_core.py` (408件) の Pegasus dispatch 実走
  (request 924423.nqsv、408 passed / 0 failed、57.34s) により、commit `4cc60864`
  (`fix(s8c): 凍結世代の検証から履歴長比例のコストを取り除く`) が既に恒久対応済みと確認した。
- worktree 作成後、`tools/check_wave_startup.py` で HEAD が local main に 1 commit 遅れている
  ことを検出し ff-only で追いつかせたところ、並行して land されていた entry 690
  ([T-699] wave) が同じ根本原因の重複 finding F418 を報告していたと判明した。F418 自身は
  「本 wave の scope 外の別 wave が `4cc60864` で解消済みと事後に確認した」まで既に自己記録
  しており、本 wave の結論と独立に一致した。F418 の「再発検知: 未確認」だった回帰テストの
  有無は、本 wave の実走で `test_candidate_freeze_batch_is_bounded_by_frozen_touch_points`
  を含む全 408 件 pass を確認したことで解消できるため、F417・F418 双方へ supersede 追記した。

## 次の一手差分

### 完了

- [T-1408] `s8c_preregistration.py` の `MAX_BATCH_REQUESTS` 超過 (F417) は commit
  `4cc60864` (D551) が走査対象を凍結 namespace を触った commit + 直接親 + 境界へ絞る設計で
  履歴比例 cost を解消済みと確認した。判定4種は維持されたまま (削減なし)。現行 HEAD で対象
  2テストを含む408件の Pegasus dispatch 実走 (request 924423.nqsv、408 passed / 0 failed、
  57.34s) で裏取りした。恒久対応は完了であり残件なし。
  remaining: none
  base: 530be1a11d1ba7fd6a66dffd8b9d8c8f127400d145e7bb18e9fd61bccc991543

### 新規

- {{T:dev-wave-lightweight-stale-path-ruling}} **P3・新規**: 段1 brief 前の実測で対象 task が
  既に別ID/別waveの成果 (今回は task 実装ですらなくユーザー命令駆動の同日 fix) で解決済みと
  判明し、段2/3を省いて4→7→8→9へ進む軽量パスが entry 673 ([T-715])・687 ([T-1198])・
  690+本entry ([T-1408]/F418 重複発見) で計4回使われた。現行 `docs/dev-wave/core.md` 凍結境界節
  は「実装しない」裁定時の段5/6省略だけを明文化し、段2/3省略は明文化していない。段構成の変更
  は自己改善で実装できないため、軽量パスを正式な dispatch 規則として明文化するか現状の
  precedent 引用運用を続けるかをユーザー裁定へ送る。
