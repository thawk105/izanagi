---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t1048-trigger-freeze-epilogue
seq: 1
title: trigger-gating の凍結領域を post-END の gated call まで広げ、END 直後の再代入窓だけを閉じた — 意味論は閉じないことを実証して 4 件起票した (コード + docs、変異 3/3 KILLED、branch worktree-dev-wave-t1048-trigger-freeze-epilogue)
---

## 本文

- ユーザー裁定は 2026-08-13 rulings 第 10 回 #5 の **(b)** (控え =
  `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-13-rulings10-15rulings.md`)。
  設計正本は `output/insights/2026-08-13_t897-trigger-admission/README.md` の RP-2。
  wave 記録は `output/insights/2026-08-13_t1048-trigger-freeze-epilogue/README.md`。
- **段 3・段 6 の敵対検証が、凍結領域の拡大では gate の意味論を固定できないことを 4 通りの
  具体差分で実証した。** prologue での `izanagi_gate_pass` 再宣言 (型差し替えで代入も真理値も無効化)、
  宣言と BEGIN の間の `return;`、epilogue 直後の dangling `else`、`FLAGS_clocks_per_us` の
  local shadowing。いずれも block と epilogue を逐語一致させたまま通る。
  **ユーザー scope が「post-END の `if` まで」と明示されているため実装せず、
  残存限界 R4〜R7 として docstring に明記して起票した。** 記録では「R2 を閉じた」と無限定に書かず
  「END 行末と gated call の間での再代入に限り閉じた」と書いている。設計判断は {{D:trigger-freeze-bytes-not-semantics}}。
- **段 2 プランが提案した「END 直後の epilogue 完全重複 (`E + E`) の拒否」を親が落とした。**
  epilogue より後を凍結しない設計では、`E + E` の「backoff 二重実行」は受理する
  `E + else { backoff(); }` と同じ結果であり、片方だけ拒否する理由を成果物の値の差として書けない
  (`DW-G05`)。段 6 の 2 レンズもともに nit と評価した。代わりに `E + E` の受理を正例テストで固定した。
- **段 1 brief の主張を 2 件、親が実測で訂正した。** (1) 「S8b oracle / floor / S-1 extime は
  quarantine 非経由」は誤りで、`prepare_cell` と `s1_verify_extime_calibration` はいずれも
  `quarantine.passed` を検査する。純増検出力を「pristine / characterization 経路と baseline 側の
  混入」の 2 つへ狭めた。(2) DW-O09 の pin 閉包探索が漏れており、
  `orchestrator/campaign/axis_trigger_gating.py` は凍結 JSON 3 本から source sha256 で間接 pin
  されていた。**pin 値 `47507d9b…` に対し着手前から実値 `72371560…` で不一致**であり、
  凍結チェーン検証の保留裁定に従って**再 pin せず**起票した。
- 段 6 レビュー B の must-fix は変異台帳側だった。MUT-2 の期待 node は「少なくとも 37」としか
  静的に言えないため、`DW-M08` の probe 経路で 1 巡目を probe と明記して回し、実測完全集合で
  再登録して本走した。**MUT-3 は 1 node しか殺さない** — 凍結定数はテスト入力の生成源でもあるため
  入力と期待が同時に動き、patch 整合テストだけが独立照合として効いていることの実証である。
- 焦点走 (9 file) の 1 回目に 1 件赤が出たが、単独走 1 passed・同一集合の再走 791 passed で
  非決定的と確定し、既知 [T-1049] (`_OPERATION_REPLAY_CACHE` の process 残留) の再発と照合した。
  新規起票はしていない。
- 工数: codex 子は plan 1 (sol/max)、consult 2 (sol/max・luna/max)、author 1 (sol/high)、
  review 2 (sol/high)、fix 1 (sol/high)。**consult sol は 1 回目が model call 上限 100 で SIGTERM し
  出力 0 bytes**だったため、探索予算の規律を prompt へ足して上限 300 で再投入した。
- **`codex_worker_launch.py` は `--artifact-dir` と `--receipt` の親ディレクトリの実在を要求するが、
  `dev_wave_codex.py` は `<root>/<wave>/` までしか作らない。** launcher を直接叩く運用では必ず空振りし、
  本 wave は 2 回失敗した。`--evidence-grace-s` の既定は今も 5 秒である。
- 変異本走で {{F:mutation-shared-tree-postcheck}} を踏み、1 走を捨てて再走した。
- 受入全走は 2 failed / 10782 passed / 65 skipped (140.16 秒、計算ノード)。赤 2 件は
  `test_dev_wave_wait.py::test_public_main_real_signal_after_success_uses_restored_handler` ([T-1066]) と
  `test_codex_worker_launch.py::test_all_repo_policy_reasoning_values_are_accepted[xhigh]` (F57 の
  `process_group_residual` / `termination_verified`) で、**単独再走 6 passed / rc=0** で再現しない。
  いずれも既知で本 wave の差分に帰属しない。
- **非帰属 checker が実運用に到達しないことを再確認した。** `tools/check_acceptance_reds.py` は
  裁定済み・未実装の [T-1053] により、赤を 1 件でも含む実 log に対して必ず rc=2
  (`probe worktree is not clean, including ignored files`) になる。受入前に親が ignored 生成物を
  撤去しても、checker 自身の子が probe worktree の中で pytest を dispatch して `__pycache__` を
  再生成するため解けない。`DW-O18` に従い rc=2 を非帰属の根拠にはせず、単独再走で確定した。
  1 回目の受入は入れ子 submodule `third_party/googletest` の未初期化で
  `preflight-submodule-ready` rc=2 になり、再帰初期化で解いた。
- 放置した場合、END 行末と gated call の間へ 1 行差し込むだけで、report が mask M を主張しながら
  実バイナリは全要因 backoff で走る状態が残り続ける。

## 次の一手差分

### 完了

- [T-1048] 凍結領域を post-END の gated call まで拡大し、END 直後の再代入窓を閉じた。
  残る意味論の穴は R4〜R7 として起票済み。
  remaining: none
  base: d27d85439499b514d78554cb2d3495a840c69ef9c068109378c7dbd5e4447699

### 新規

- {{T:trigger-skeleton-declaration-freeze}} **P2・新規**: trigger 骨格の宣言側と呼出依存を凍結するか。
  R4 (prologue での `izanagi_gate_pass` 再宣言による代入・真理値の無効化)、R5 (宣言と BEGIN の間の
  制御流変更による非到達化)、R7 (`Backoff` / `FLAGS_clocks_per_us` の local shadowing) は、
  いずれも block と epilogue を逐語一致させたまま gate を無効化できる。実証差分は
  `output/insights/2026-08-13_t1048-trigger-freeze-epilogue/verbatim/consult-b.md` 所見 1、
  同 `consult-a2.md` 所見 2、同 `review-b.md` 所見 2。
- {{T:trigger-epilogue-dangling-else}} **P2・新規**: epilogue 直後の dangling `else` (R6)。
  `#endif` は C++ の `if` を構文的に閉じないため、直後に `#if ... else { backoff(); } #endif` を
  置くと preprocess 後に `if...else` が結合し常時 backoff になる。骨格へ構文的 terminator を足す案は
  patch 不変条件と衝突するため、patch migration を伴う設計裁定が要る。
- {{T:axis-source-pin-mismatch}} **P3・新規**: `orchestrator/campaign/axis_trigger_gating.py` の
  sha256 が `known_axes_freeze.json` / `measurement_freeze.json` / `holdout_freeze.json` の
  記録値と wave 前から不一致である。凍結チェーン検証の保留裁定との関係を整理する (再 pin はしない)。
- {{T:admission-enoent-early-return}} **P3・新規**: build admission の trigger 検査が
  `FileNotFoundError` で無条件 return するため、axis 対象 source の不在が検査を素通りする。
  拒否へ倒すかは過剰拒否の危険があるため単独裁定が要る。R3 の ABA 窓と組み合わせると
  実効的な迂回になる (`verbatim/review-b.md` 所見 3)。
