# 段 1 brief — 変異本走を計算ノード 1 ジョブへ束ねる

## scope

`tools/mutation_harness.py` の**実行場所だけ**を login node から gen_S 計算ノードへ移す。
ジョブ内の runner は `--runner-mode local`。逐次性・`flock` 単一走行・復元検査・全走 (test_command)・
検出力 (DW-M08 の失敗 node 記録) の**意味は一切変えない**。変異 1 件ごとの qsub を廃す。

## 確定済みユーザー裁定

- DW-G01 に従い、恒久実装の**前に** 2〜3 変異の小 spec で「個別 dispatch と束ね実行で verdict が
  完全一致する」生死確認を取る。不一致なら恒久実装へ進まない。

## 段 1 前提実測 (すべて本セッションで実測)

- **削減量 = 実測で裏付いた。** `output/insights/2026-08-02_t243-parallel-docs-spool/mutation-ledger.json`
  (runner_mode=dispatch、41 変異、test_command = 全走) の median per-mutation `duration_s` = **467.0 s**、
  同 record の pytest 自身の所要 (test_output_tail の `in Xs`、対応が取れた n=12) の median = 237 s。
  **差 = median 229.9 s / 変異** (min 219.8、max 237.0)。合計 `duration_s` = 19,037 s (5.29 h)。
  baseline (277.8 s) と collection (226.7 s) も同じ overhead を払う。
  → 43 回 × 約 230 s ≈ **2.7 h/matrix** が pytest 以外の待ちに消えている。ユーザーの「約 220 秒」は妥当。
- **gen_S の上限は足りる。** `qstat -Qf gen_S` の Per-Req Elapse Time Limit = **86400 s (24 h)**。
  41 変異 × 237 s ≈ 2.7 h。`dispatch_compute.py` は `--walltime HH:MM:SS` を既に持つ (既定 00:30:00)。
- **計算ノードでは内側が自動で local になる。** `site_policy.classify_site` は `bnode*` を
  `PEGASUS_COMPUTE` と判定し、`run_tests.py:939` の再 dispatch は login のときだけ発火する。
- **task enum の拡張は却下済み案ではない。** `dispatch_compute.TASKS` は `{tests, provenance}` の閉集合。
  D103 決定 5 が拒むのは「任意 command 化 / `tools/pegasus/*` の glob 許可」であり、
  provenance wave の決定 (3) は**閉じた enum に task を足して親子二層 fail-closed にする**形を
  採用済みである。`mutation` task の追加はこの採用済みパターンに乗る。
- `output/pegasus-dispatch/` は `.gitignore:25` で無視される → harness の clean-tree assert に影響しない。
- 他 worktree 12 本が並走中 (t342-u1..u5、t189、t313、t328、t342-344、fold-rotation)。本 wave は
  `worktree-dev-wave-t357-mutation-batch` のみを所有する。

## 不変条件 (破ったら停止)

1. verdict (status / failed_nodes / matches_expectation) が dispatch 経路と完全一致すること。
2. `flock` による「同一 repo で同時に 1 本」の保証を**弱めない**。
3. 復元検査 (`_verify_originals` / `_assert_head` / signal handler) を弱めない。
4. `test_command` を縮めない (全走のまま)。DW-M08 の `-rf` と node 記録を弱めない。
5. 証拠 (receipt / job stdout / stdout_sha256) を捨てない。

## 攻撃対象の provisional 裁定

- **(P1) `flock` の有効範囲。** `_lock_path_for` は `tempfile.gettempdir()` = `/tmp` を使い、`/tmp` は
  node-local (`/dev/md0`)。一方 `/work`・`/home` は Lustre を **`flock` mount option 付き**で
  マウントしている (`/proc/mounts` 実測)。harness を計算ノードへ移すと lock が bnode の `/tmp` へ移り、
  単一走行保証が「login host ごと」から**実質ゼロ**へ落ちる。
  → provisional: lock を repo と同じ共有 FS 上 (repo dir の兄弟、`_assert_runtime_artifacts_outside_repo`
  を満たす repo 外) へ移す。現行より狭くならない方向にしか動かない。**これは正しさ防壁に触るため
  軽量版を使わず、段 2/3 と段 6 レビュー 2 本を回す。**
- **(P2) walltime kill と復元。** 現行の harness に外側時間上限はない。ジョブ内では walltime が
  hard kill になり、SIGKILL なら**変異が当たったままの tree が残る**。
  → provisional: signal 復元経路は維持、walltime は `estimated_run_seconds × runs` に余裕を掛けて要求、
  途中切断は `--resume` で回収。NQSV が SIGTERM を先に送るかは段 2 で確認する。
- **(P3) `--detached` の意味。** 「外側の実行時間上限に掛からない経路」の自己申告。ジョブ内には
  walltime という上限がある。→ provisional: フラグの意味 (Claude Bash 面の上限外) は変えず、
  walltime 見積りを親の義務として DW-M05 側へ書く。検査は弱めない。
- **(P4) 証拠 field。** 束ね実行では変異ごとの receipt / job stdout が存在せず、`_artifact()` の
  local 契約は該当 field を null 必須にする。→ provisional: 束ね 1 本分の receipt を run 単位で
  台帳へ残し、変異単位は local 契約のままとする。証拠を黙って落とさない。

## 成果物

1. **生死確認**: 2〜3 変異の小 spec 1 本 + 使い捨て qsub script (100 行以内、DW-G01) +
   dispatch 経路 ledger と束ね経路 ledger の 2 本 + verdict 完全一致の突き合わせ。
2. GO のときだけ恒久実装: `dispatch_compute.TASKS` へ `mutation` を追加 (親子二層 fail-closed)、
   P1 の lock 再配置、両者のテスト。
3. docs: `docs/dev-wave/mutation.md` DW-M05 の起動形、`docs/pegasus-runbook.md` の該当節、
   新 D (spool fragment)。
4. 変異 matrix + 受入全走。

## DW-G05 成果物影響

実装しない場合: 変異本走 1 matrix あたり約 2.7 h の待ちが残り続ける。値そのものは変わらないが、
コストが wave に変異数の削減を強い、**受理集合を守る証拠 (変異台帳の検出力) が実質的に劣化する**。
誤って実装した場合: P1 で二重走行が起きれば変異台帳の verdict と復元後 bytes が壊れ、P4 で証拠が
落ちれば台帳の provenance 参照が切れる。ゆえに生死確認で verdict 完全一致を先に取る。

## 並列分割方針

段 2 プラン起草 codex 1 本 (read-only)。段 3 敵対 2 レンズ (レンズ A = 正しさ防壁 = P1/P2/P3、
レンズ B = 証拠と受理集合 = P4 + 変異事前登録の妥当性)。段 5 は所有分離で
実装子 A = `tools/pegasus/dispatch_compute.py` 系、実装子 B = `tools/mutation_harness.py` 系。
