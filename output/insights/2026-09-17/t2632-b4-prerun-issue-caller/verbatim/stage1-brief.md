## 段 1 brief

- **研究前進:** 論文主張 B-4 (reflux ablation) の実走前提 §6 条件 9「§5.1.1 の分析契約を実行する経路が実在する」のうち、
  registry / manifest 生成器 (発行器) の **production 呼び手** が tests 以外に 0 件である穴を埋める。
  完了判定: 呼び手が repo に入り、現物 (3 campaign の whiteboard) を入力に 1 回実行され、封印 receipt または
  発行器の typed rejection と「足りない入力」の一覧が job dir と insight に残る。実発行の成功は完了条件でない (依頼の逐語)。
- **scope:** 呼び手 module 1 本 + その test。§5 の 2 欄記入 (項 2)・base campaign 起動 (項 3) は scope 外。
  発行器・台帳・事前登録・`p3_s4_loop` は no-touch。仮想リスク向けの gate・検査・台帳・一般化は足さない (DW-G05)。
- **確定済み裁定:** D95 (実装面は Codex author)、D1880 (母集合 = manifest 201 行、n 切り下げ不可)、D1881 (root は事前登録が名指し、呼び手は選べない)、
  D1846 (束縛は bootstrap のみ、checkpoint は whiteboard 5 field だけ = D39 決定 3)、D1936 項 8 / D1986 項 4 (成功例置換・追加基盤・n 切り下げ不採用、少数は記述報告まで)、D2016。
- **brief 前の実測で判明した、一次資料の前提を覆す新事実 (段 4 で再裁定):**
  - (N1) 発行器は適格行 < 201 で `design_not_feasible` を返し publication root を作らない
    (`p3_b4_prerun_issuer.py:835-843`、`p3_b4_analysis_ledgers.py:1071-1083`、test `test_fewer_than_201_eligible_is_typed_before_root_creation`)。
    したがって T-2632 README「次の一手」の「1 (封印発行) は 2 と独立に閉じられる」は **封印 receipt の取得については refuted** —
    receipt には 201 の適格行が要り、それは 3 (自然赤) と 2 (真偽値の根拠) を前提とする。独立に閉じられるのは **production 経路の実在** だけ。
  - (N2) `initial_proposal_sha256` (全行で有効 sha256 必須、`_validate_attempt`) は既存 campaign の現物から導けない —
    `loop_state.json` の whiteboard 行は `iteration/direction/magnitude/result/delta_pct` の 5 field だけ (D39 決定 3 のリーク遮断、D1846 が確認)、
    `runs/wal.jsonl` は genome と src_token を持つが proposal document を持たない。
  - (N3) 在庫: 3 campaign・whiteboard 7 行・全て `success`、`rejected` 0 (T-2632 README の再計数と一致、本 wave で再確認)。
  - (N4) `output/b4-prerun-publication` は gitignore されない (`git check-ignore` rc=1)。発行器の root は module file の checkout
    (`_REPOSITORY_ROOT = parents[2]`) から解決するので、wave worktree で走らせれば `<worktree>/output/b4-prerun-publication`。
  - (N5) registry の理由語彙 (`scheduled/generation_failed/red_not_reproduced/duplicate/corrupt/screening_only_red`) に「赤でない成功例」は無い。
    registry は「予定した attempt」の台帳 (§5.1.1) なので、成功 precursor は行にならない → 現物からの候補集合は空。
  - (N6) planned result path は呼び手が選ぶ (producer 側の規約なし)。発行器の固定名 5 種と root 直下の予約を避ければ root 配下でも可
    (`test_other_future_result_path_below_publication_root_is_allowed`)。
- **不変条件:** 規律 2 を緩めない。真偽値 (`calibrated_workload_member` / `bootstrap_member` / `reference_is_unique`) を hard-code で真にしない。
  値を捏造して行を作らない — 出所の無い field は typed に止める。発行器・台帳の bytes を変えない
  (producer-auth experiment の錨 3 本 `p3_b4_producer_auth_experiment.py:457-478` が無傷であること)。
- **成果物の形:** `orchestrator/campaign/p3_b4_prerun_issue.py` (名前は (P2) 暫定) — CLI。campaign root を argv で明示、
  `loop_state.json` の whiteboard から `result == "rejected"` の行だけ候補にし、各 field を名指しの現物から組む。
  出所の無い field があれば発行器を呼ばず typed に報告して非 0。候補 0 件なら空 batch で発行器を呼び、typed rejection を JSON で出す。
  成功時のみ rc=0 で receipt path / sha256 / commitment を出す。test は fixture campaign dir で「候補 0 → 発行器 typed rejection」と
  「候補 1 (rejected) で出所欠落 → 発行器を呼ばず typed stop」の 2 本を最小に。
- **割れうる前提 (親の provisional 裁定・攻撃対象):**
  - (P1) `bootstrap_member` は発行そのものが集合を固定するので、発行 batch に含めた行では真とみなせる (T-2632 README は「publication 不在だから真にできない」と読んだ — 循環)。
  - (P2) module 名・置き場・argv 形 (campaign root を明示、走査 framework を作らない)。
  - (P3) 候補 0 件のとき発行器を呼ぶ (空 batch は `_normalize_attempts` を通り `design_not_feasible` に落ちる、と親は読んだ — 未実測)。
  - (P4) planned result path は `<publication_root>/results/<attempt_id>.json` の形 (発行器の予約と衝突しない)。
- **DW-O13 (gate 入力の実在):** 入力 field は `loop_state.json.whiteboard[].result`。実測値域は `{success}` のみ。`rejected` は
  `p3_s4_loop.py:1877/1899/1911` (`record_diff_reject`) で到達可能だが現物では未観測。
- **模擬 / 実:** 実発行の試行は wave worktree の発行器と実 campaign artifact で行う (模擬なし)。fixture の 201 行は使わない。
- **並列分割:** 実装子 1 本 (module + test)。段 2 plan 1 本、段 3 consult 2 本 (設計択一 (P1)〜(P4) が割れるので軽量版にしない)。
- **受入・実測環境:** login node (pegasus02) の焦点走 + 受入全走 (`tools/dev_wave_wait.py acceptance`)。計算ノード不要。
