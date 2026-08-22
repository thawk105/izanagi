---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-t1472-provider-init-indeterminate
seq: 2
title: '[T-1472] 取り残し wave を別 context が引き継ぎ、local main 取り込みの合成監査を経て受入・land まで完了させた (docs + 記録、branch worktree-dev-wave-t1472-provider-init-indeterminate)'
---

## 本文

- 本エントリは同 wave の前 entry (seq 1) の続きである。前 session は受入を 4 回投入して
  いずれも走行に至らず終了していた。引き継ぎ context が最初に実測したのは受入結果で、
  attempt3 は `classification=claim-timeout` の rc=70、attempt4 は `signal-15` の rc=143
  だった。attempt4 は `.done` が書かれておらず、launcher script ごと SIGTERM で落ちたため
  ログに終端行だけが残っていた。**待ち手の通知でも `.done` の実在でもなく、`.done` と
  producer pid の生存を併せて見ないと「走行中」と「落ちた」を区別できない。**
- claim-timeout の再発に対しては、main へ着地済みの `DW-O27`
  (「acceptance 投入は `--lease-optional` を既定で使う」、T-1458 実装) に従った。
  採用前に `tools/dev_wave_wait.py` の実装を読み、claim を 1 回だけ試して held/queued でも
  待たず `sha256(wave)[:12]` の疑似 holder で継続し `_LeaseOwnership` が NONE のままなので
  release を skip する、という挙動を確認した。私設 lease-dir は使っていない。
- wave tip は main に 40 commit 遅れていたため local main を取り込んだ。競合はなく、
  実装面で両親がともに変更した file は
  `orchestrator/tests/test_p3_autonomous_workload_trial.py` 1 件だった。
- **main 側の T-1458 が本 wave の fix の安全性根拠である
  `orchestrator/campaign/autonomous_trial_completeness.py` を 62 行変更していたため、
  競合なしの自動 merge であっても合成の意味的整合を独立に監査した** (read-only codex、
  reasoning=max)。結論は「変更不要」。`_check_terminal_projection` と
  `_check_workload_coverage` は provider-init-error / transport-admission-error terminal の
  zero-cells を依然として受理し、arm/digest consumer へ追加された formal mode は
  `matching_cells` 不在で return するため `experiment_indeterminate=True` の trial へ
  新しい拒否条件を課さない。親は独立に、`experiment_indeterminate` が `report["status"]` を
  変えず `lifecycle_terminal_status` を足すだけであることを確認した — これにより
  `_check_terminal_projection` が要求する `status == "partial"` は壊れない。
- この merge の commit で、commit 前の provenance preflight と権威である full-history 監査の
  判定が割れることを実測した。詳細と裁定パッケージは
  {{F:message-file-preflight-does-not-narrow-merge-paths}} を参照
  (F120 の派生記述の訂正を含む)。
- **段 8 裁定 1 件目 (不採用):** 前 entry の failures fragment が恒久対応として提案した
  「`docs/dev-wave/mutation.md` の `DW-M07` へ変異 harness の未文書制約 7 項目を追記する」は
  実施しない。`DW-M07` は現状 978 bytes で、`tools/check_docs.py` の L2 単節予算
  1000 bytes に対し空きが 22 bytes しかなく、7 項目は意味を保ったまま入らない。
  `docs/skill-self-improvement.md` は「予算に収まらなければ reference へ統合し、
  それでも意味等価にできなければ変更を止めてユーザー裁定へ返す」「予算値を上げる変更は
  通常の自己改善に含めず、理由付きの独立審査対象にする」と定めるため、裁定パッケージとして
  ユーザーへ返す。台帳側の記録
  ({{F:mutation-worktree-local-mode-and-resume-file-preconditions}}) は残るので、
  実測した制約自体が失われるわけではない。
- **段 8 裁定 2 件目 (採用):** 上記の preflight 非対称は failures 台帳へ新規起票し、
  F120 へ supersede 追記を行う。checker 自体の是正は実装面のため本 wave では行わない。
- 受入全走は段 8 まで終えた最終 tip に対して 1 回だけ投入した
  (`tools/dev_wave_wait.py acceptance --lease-optional`)。本 entry が台帳へ描画されている
  ということは、その受入が緑で返り `tools/dev_wave_land.py` の ff-only land が成功したことを
  意味する — land は緑の受入 receipt を要求するため、赤ならこの fragment は fold されない。

## 次の一手差分

### 完了

- [T-1472] D657 が求める C04 の crash 時の扱いへ provider-init / transport-admission 失敗を
  含める実装、変異 matrix (baseline PASSED・MUT-1〜4 4/4 KILLED・SURVIVED 0・MISMATCH 0)、
  受入全走、local main への land をすべて終えた。8c supervisor state machine 全体整合と
  `_finish_trial()` の一般 `Exception -> partial` は当初から別 T の所有であり本 T の範囲外。
  remaining: none
  base: bf90d6f868ad565beabe4359496d1d8a39c06bd1473f3fa4319d324cb3644098
