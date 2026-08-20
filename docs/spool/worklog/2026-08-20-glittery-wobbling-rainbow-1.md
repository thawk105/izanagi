---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: glittery-wobbling-rainbow
seq: 1
title: '[T-1403] mitigation leg (elapstim_req=max,warn + --warning-signal + --accept-sigterm) がwalltime打ち切りでSIGTERMを配送することを計算ノードで実測した (コード + テスト + 記録、branch worktree-glittery-wobbling-rainbow、変異matrix = baseline PASSED・5/5 KILLED・SURVIVED0・MISMATCH0)'
---

## 本文

- 段2 (codex plan)・段3 (敵対相談)・段6 の敵対レビュー2本を軽量版として省略した。設計択一が
  割れない・正しさ防壁 (verifier/gate) に非接触・受理集合不変と判断したため (DW-C00)。段5 Codex
  author 実装、段6 fix・変異matrix・受入は通常どおり実施した。この軽量版判定は段4 で自己反証を試み、
  覆らなかった (根拠: 新規probeが自己完結し、mutation harness の walltime SIGKILL 挙動そのもの以外の
  既存正しさゲートに触れない、blast radius が「既定どおりSIGKILLされる (既知・無害)」に有界)。
- 段5 実装 (Codex author) は静的レビューで3件の real 所見が出て fix 1 巡で解消した:
  (1) `.pbs` が `python3.10` でなく `python3` を呼んでいた (計算ノードで3.10未満に解決されうる、
  pegasus-runbook.md 既知の罠)。(2) evidence root の既定値が node-local 想定のパスで、login node
  から読めない可能性があった。(3) 実観測 (checkpoint + NQSV 会計) から `VerdictObservation` を
  再構成する関数が無く、`SIGTERM_CAUGHT_THEN_KILLED`/`NO_SIGNAL_OBSERVED_SIGKILLED` を実データから
  導出できなかった (`reconcile_observation` を新設して解消)。
- 実 qsub 投入は親が行った (Codex sandbox は network/qsub 不可のため)。pegasus02 login node から
  直接 `qsub -o/-e <repo外path>` で投入 (dispatch_compute.py は tests/provenance 専用の薄い
  submitter であり mitigation leg directive を持たないため使わなかった)。
- **実測の核心:** request `927684.nqsv` (max=180s, warn=120s) で、NQSV は
  `%NQSV(INFO): Batch job received signal SIGTERM.` を配送した。D139 (2026-08-04) が実測した既定
  構成 (SIGKILL 直送・grace 皆無) と異なる。probe 自身は受信から約1.6ms後に正常終了、`compute_verdict`
  による最終 verdict は `SIGTERM_CAUGHT_CLEAN_EXIT` (scheduler 会計ベースの grace は9.97秒)。
  詳細は {{D:t1403-mitigation-leg-sigterm-confirmed}} と
  `output/insights/2026-08-20_t1403-walltime-sigterm-mitigation-leg.md`。
  現行 `floor_campaign.sh` (--accept-sigterm=yes のみ) はこの実測対象と異なる構成のままであり、
  D546 決定2の「実測するまで結論しない」は現行構成について引き続き成立する。
- 変異matrix登録 (DW-M01) は段4時点では新規ファイルのため抽象的な意図 (4項目) として登録し、
  段5実装後にfile:lineへ具体化・DW-M07のfix後anchor再照合を行った。本走で1件 MISMATCH を検出:
  `verdict-clean-exit-swap` は `compute_verdict` の clean-exit 分岐が複数テストに共有されており、
  expected_nodes を机上予測の1件でなく実測の3件へ訂正して再走し、5/5 KILLED を確定させた
  (expected_nodesは机上予測でなく実測で確定する、という既存運用の実例)。
- 変異matrix本走は gen_S の混雑 (QUE 56〜78件、他の並行 dev-wave セッションと推測) により
  collection phase の dispatch-runner-timeout で orphan-hold を計8回踏んだ (うち1回は dirty file
  ありだったが単一変異のみで `git checkout --` により正しく復元)。spec の `timeout_seconds` を
  120→480→900秒へ段階的に引き上げて解消した (480秒でも `timed_out=true` を実測、混雑が実際に深い
  ことを確認した上での判断)。別途、変異走行中に自分自身が書いた untracked docs ファイル
  (本 fragment 自体を含む spool/insight) が harness の porcelain-空検査 (F174) を発火させ
  即アボートする事象を実地で踏んだ。一時退避で回避した。
- provenance 監査 (commit後 full-history) は rc=0。

## 次の一手差分

### 完了

- [T-1403] mitigation leg を実測し、D546決定2の未解決状態を新規決定
  {{D:t1403-mitigation-leg-sigterm-confirmed}} で解決した。production設定
  (floor_campaign.sh/dispatch_compute.py) は変更していない。
  remaining: none
  base: f2e69ef92019892c917044a6c9a7aa4470673d11af0224c76913b291c18522d0
