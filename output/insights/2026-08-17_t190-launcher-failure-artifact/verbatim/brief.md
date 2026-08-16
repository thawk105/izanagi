# 親 brief — dev-wave [T-190] launcher 失敗 artifact 保存による原因分離

- wave: `worktree-dev-wave-t190-failure-artifact`
- worktree (repo root): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t190-failure-artifact`
- 起点 main: `5a19b8ab`
- 日時: 2026-08-17 01:00 JST

## 1. scope

**[T-190] のみ。** F57 族 (launcher / git の wall-clock 縁張り付きフレーク) の恒久対応のうち、
**失敗 artifact 保存による原因分離だけ**を実装する。fixture harden 本体 (予算値の是正) は
本 wave の scope 外で、本 wave の診断結果を見てから別 wave で起票する。

**依頼文の「[T-553] も対象」は stale であることを親が実測した。** [T-553] は 2026-08-09 に
実装済みで完了している (`docs/archive/worklog-phase3-0809-352.md`、branch
`worktree-dev-wave-t553-git-budget`)。[T-692] R1〜R3 は s8c 事前登録の `git cat-file` 15 秒固定
timeout を作業量比例予算へ変える裁定であって、launcher の失敗 artifact 保存の裁定ではない。
現行 `docs/worklog.md` の次の一手に [T-553] は無い (grep 0 件)。**生きているのは [T-190] のみ。**

## 2. 確定済みユーザー裁定 (逐語要約)

- 実装は Codex author (D95)。
- **禁止 1:** production の wall-clock gate を緩める方向の変更は採らない (規律 2)。
- **禁止 2:** テストを再試行で緑にする対応も採らない。台帳が既に根拠を記録している。
- 3 秒超過そのものを根本原因と断定しない。負荷との相関も成立していない
  (loadavg 12〜15 での発火と 1 未満での連続 2 回発火の両方が記録されている)。
- 本 wave が保存すべきは、**pytest tmp が終了時に失う失敗時 receipt と stop reason**。
- 診断成果を必ず台帳へ残して終わること。

## 3. 不変条件 (破ってはならない)

1. production の `--max-wall-clock-s` / `--evidence-grace-s` / `--termination-grace-s` /
   `--poll-interval-s` の **値も判定条件も変えない**。launcher parser の既定
   (evidence `5` / termination `2`、`tools/codex_worker_launch.py` の parser 既定) を触らない。
2. `accepted` の受理述語を変えない。`limit_trigger` が取りうる値の集合
   (`_LIMIT_REASONS`) と、それが受理判定へ効く経路を変えない。
3. test fixture の予算値 (`_base_command` の wall=`3` / evidence=`1.0` / termination=`0.05` /
   poll=`0.01`) を本 wave では変えない (harden は別 wave)。
4. 既存テストの期待値を反転・緩和・skip・削除しない。赤なら実装側が誤り。
5. 診断のために本番の制御フロー (どこで break するか、どの順で terminate するか) を変えない。
   観測量の記録は制御フローに副作用を持たせない形で足す。

## 4. 純増検出力 (既存被覆を性質で検索した結果)

既存機構: `grep -rn "FAILURE_ARTIFACT|failure_artifact|artifact_dir"` で失敗時退避の機構は **0 件**。
テスト側には診断メッセージ生成器が既にある —
`_launcher_failure_message` (`orchestrator/tests/test_codex_worker_launch.py:408`) が
`_runtime_context_lines` (`:375`) 経由で `receipt['limits']` と `receipt['actuals']` を印字し、
`_bounded_failure_message` (`:478`) が **16 KiB (`_DIAGNOSTIC_MAX_BYTES`、`:42`) で切り詰める**。

**したがって現状で失われているのは次の 5 点であり、これが本 wave の純増である。**

| # | 失われている観測量 | 実アンカー |
|---|---|---|
| ① | `evidence_forced_stop` | `tools/codex_worker_launch.py:353` で宣言、`:1505` で代入されるが receipt にも診断にも出ない |
| ② | `residual=None` の出所 (4 経路以上) | `_group_member_count` (`:1140`-`:1166`) が `identity is None` / `scandir` 失敗 / 個別 `stat` 読取失敗 / parse 失敗 をすべて同じ `None` に潰す |
| ③ | phase 別時刻 | 不在。job clock 起点 (`:35`) と attempt clock 起点 (`:1347`) の 2 つしかなく、preflight / spawn / drain / terminate の区切りが無い |
| ④ | latch の全成立集合 | `:1456`-`:1490` の `if/elif` が wall → model → token を単一 `pending_limit` へ縮約し、複数同時成立を区別しない |
| ⑤ | 失敗時の artifact ファイル本体 | receipt.json / `attempt-NNNN.events.jsonl` / `.stderr.log` / `.output.md` / rollout はすべて pytest `tmp_path` 配下 (`_base_command`、test:`983`-`997`) で teardown 時に消える。診断メッセージに出るのは receipt の `limits`/`actuals` の 2 dict だけで、`attempts[]` 個別は出ない |

## 5. 割れうる前提 (親の provisional 裁定であり攻撃対象)

- **(P1) 計装 ①〜④ の出力先。** 親 provisional = **attempt record ではなく別 artifact file**
  (例: `<artifact_dir>/attempt-NNNN.diagnostics.json`)。
  理由: `_ATTEMPT_FIELDS` (`:93`-`:123`) と `_RECEIPT_FIELDS_V2` (`:127`-) は frozenset で、
  field 追加は schema 変更であり `check_receipt` の外部期待・受理判定へ波及する (不変条件 2)。
  **攻撃してよい**: 別 file だと「receipt と別 file が食い違う」新しい失敗様式が生まれないか、
  失敗時に別 file 自体が書かれない経路が残らないか。
- **(P2) ⑤ の退避先と発火条件。** 親 provisional = **環境変数 opt-in**
  (未設定なら現状どおり退避しない)。受入全走では runner が設定する。
  **攻撃してよい**: opt-in だと肝心の受入全走で設定漏れが起き恒真化しないか。
  常時退避にした場合の disk / 並列 48 worker への影響はどちらが大きいか。
- **(P3) ④ の扱い。** 親 provisional = **`limit_trigger` の値と決め方は現状のまま維持**し、
  全成立集合は診断 artifact 側にだけ出す。
  **攻撃してよい**: 診断側だけに出すと「診断は複数、受理は 1 つ」の乖離が新たな混乱源にならないか。

## 6. 成果物の形

- **A (launcher 側):** ①〜④ を失敗時に落とせる観測量として出す。制御フローは変えない。
- **B (test 側):** launcher テストが rc 不一致で落ちたとき、`tmp_path` 配下の artifact 一式を
  teardown 前に耐久 dir へ退避する。既存の 16 KiB 診断メッセージは残す (置き換えない)。

## 7. DW-G04 発火 gate の実在

発火条件 = launcher テストの rc 不一致。実 artifact path と計測 ID =
F285 走 A (`/work/1/SFC/tanab/dev-wave-jobs/cleanup-cherry-3stage/acceptance.log`、
bnode130、request `908484`、失敗 21 件、全件 `limit_trigger=max_wall_clock_s`)。
`receipt_actuals.wall_clock_s` の実測 3.0099〜3.2650 秒 (予算 3.0 秒ちょうど) が同 log に残っている。

## 8. DW-G05 成果物影響

実装しない場合: F57 の再発は今後も「非帰属・原因未確定」として `docs/failures.md` へ積まれ続け、
受入全走の緑 1 回分の窓が再発のたびに失われる。**certified 選択・材料レポートの値と受理集合は
変わらない** — 本 wave は診断計装であり、受理集合を動かさないことが不変条件 2 だからである。

## 9. 環境

実測・受入とも Pegasus 計算ノード。focus 走は
`python3 tools/run_tests.py --force-dispatch <file> -q -k <expr>`、
受入全走は `python3 tools/run_tests.py` ちょうど。
login ノードの bounded local は本 wave の起動時に
`memory.max / memory.oom.group を走行中に attest できない` で infra failure になったため使わない。

## 10. 分割方針

段 5 は所有素集合で 2 単位:
- **単位 A** = `tools/codex_worker_launch.py` (+ 同 file 向けの production 側テスト)
- **単位 B** = `orchestrator/tests/test_codex_worker_launch.py` の退避 harness

依存: B は A が出す artifact を退避対象に含めるため、A のファイル名契約だけ先に確定させる。
