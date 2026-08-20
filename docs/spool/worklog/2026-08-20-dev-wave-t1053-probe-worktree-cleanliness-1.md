---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1053-probe-worktree-cleanliness
seq: 1
title: check_acceptance_reds.pyのprobe worktree清浄性検査失敗時の診断へ汚染pathを追加した (コード+テスト、branch worktree-dev-wave-t1053-probe-worktree-cleanliness、変異matrix=baseline PASSED(86 passed)・4/4 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼の発端: `tools/check_acceptance_reds.py` の非帰属checkerがprobe worktree清浄性検査
  (`probe worktree is not clean, including ignored files`) でrc=2になり実運用に到達しない
  問題 (T-1053/T-1117)。別セッションのT-183 (branch worktree-dev-wave-t183-codex-failure-recovery)
  が受入6/6でこのバグに阻まれてland未達のままブロック中と、cross-session messageで
  引き継ぎを受けた (本waveの依頼自体はcommand引数として独立に発行されていた)。
- 調査の結果、現行main HEAD上ではPYTHONDONTWRITEBYTECODE伝播の欠陥を発見できなかった
  (3独立方法が一致、詳細は{{D:probe-cleanliness-bytecode-propagation-confirmed}})。T-183の
  6回の受入試行はいずれも先行修正 (env allowlist追加・dispatch子環境のsetdefault追加) の
  main着地後だったため、「tested-mainが古い」という説明も実測で棄却した。証拠のないまま
  追加のロジック変更を行うのは過剰実装と判断し、T-1117 (診断が汚染pathを示さない問題) の
  修正だけを実装した。
- 段3敵対相談の一方のレンズが、`tools/pegasus/dispatch_compute.py` のorphan-hold機構に
  未防御raceを発見した: (i) 外部timeout/killでdispatcher自身の例外処理に到達しない場合は
  holdが作られない、(ii) hold書込み失敗時もholdなしとして処理が続行する
  (fail-openであり規律のfail-closed原則に反する)、(iii) qdel後にqstatでの終端確認をしない。
  今回のwaveのscope (probe worktree清浄性検査の診断改善) の外であり、実際の incident として
  観測されたものではなく段3の静的検査で見つかった論理的gapのため、failures台帳への新規記録は
  見送り、次の一手へ新規taskとして登録するに留めた。
- 子の工数はCodex 7本 (plan 1、consult 2、author 1、review 2、fix 1、focus 1)、いずれも
  gpt-5.6-luna・reasoning=max。段6の変異matrixはbaseline PASSED (86 passed)・
  4件すべてKILLED (期待どおり)・SURVIVED 0・MISMATCH 0。うち3件 (M1〜M3、診断メッセージの
  内容・件数上限・byte上限に関する変異) はD398 (受理集合を変えない) の性質上、通常の
  正しさ保護kill ではなく診断検出力のpin (`DW-M08`) として扱う。M4 (受理/拒否判定そのものを
  無効化する変異) だけが正しさ防壁の直接的な保護に相当し、期待した4テストのうち
  `test_ignored_artifact_diagnostic_record_limit[64]` だけは別経路 (fingerprint変化検知の
  fallback) が同じrc=2を返すため生存すると事前予測し、実測もその通りだった
  (残り4テストでKILLED)。
- 段2の待ち手で `dev_wave_wait.py producer --receipt-file` にcodex自身の `--receipt` と
  同一pathを誤って指定し、waiterのreceipt (schema `status`) がcodexのreceipt.json
  (schema v3) を上書きした。実害はなかった (出力mdは無事)。

## 次の一手差分

### 完了

- [T-1117] `_probe_fingerprint()` を `(hash, porcelain_text)` のtuple返却へ拡張し、
  `_assert_probe_identity()` が失敗時だけ最大64件/8192bytesの上限付きで汚染pathを
  例外メッセージへ含めるようにした。受理/拒否判定 (hash比較)・cleanup経路・rc=2は不変
  (D398固定)。新規4テスト (単一path・複数path・件数境界64/65・byte境界) を追加し、
  変異4件すべてKILLED (baseline PASSED 86 passed、SURVIVED 0、MISMATCH 0)。
  remaining: none
  base: d130b3b49f95835b2f31dada5df8c0b6b6b6766e6457ebfd14cafc394a368a98

### 新規

- {{T:acceptance-reds-orphan-hold-timeout-race}} **P2・新規**:
  `tools/pegasus/dispatch_compute.py` のorphan-hold機構 (probe worktreeへの遅延書き込みを
  防ぐfail-closedのはずの防壁) に、段3敵対レビューが3つの未防御raceを発見した — 外部
  timeout/killでdispatcher自身の例外処理に到達しない場合はholdが作られない、hold書込み
  失敗時もholdなしとして処理が続行する (fail-open)、qdel後にqstatでの終端確認をしない。
  実際のincidentとしては未確認 (段3の静的検査による論理的gap)。成果物影響: 現状は
  probe worktree清浄性検査の受理集合を直接は変えないが、Pegasusのキュー混雑時
  (親が本wave中に同時34job走行を実測) にdispatchのtimeoutが発生しやすい状況では、
  この経路が別の未解明なprobe汚染要因になっている可能性がある。詳細な指摘は
  一次資料 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1053-probe-worktree-cleanliness/
  outputs/stage3-lens-b.md` を参照。
