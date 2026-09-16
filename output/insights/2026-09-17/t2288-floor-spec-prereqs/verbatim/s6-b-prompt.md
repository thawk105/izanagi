単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/s4-ruling.md

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の
停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/s4-ruling.md` — 段 4 裁定
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/docs/spool/decisions/2026-09-17-dev-wave-t2288-floor-spec-prereqs-1.md` — decisions fragment (検査対象)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/output/insights/2026-09-17/t2288-floor-spec-prereqs/README.md` — insight README (検査対象)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/docs/spool/worklog/2026-09-17-dev-wave-t2288-floor-spec-prereqs-2.md` — worklog fragment (検査対象)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/s3-b-out.md` — 段 3 レンズ B の所見 (実物照合の元)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/orchestrator/campaign/floor_pair_driver.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/orchestrator/campaign/calibration_verify.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/orchestrator/campaign/layer3_report.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/orchestrator/campaign/env_attestation.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/orchestrator/campaign/env_contract.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/orchestrator/calibrator/cli.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/orchestrator/calibrator/runner.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/external/ccbench/include/ycsb.hh`

上記以外に repo 内を読んでよい (`output/env/pegasus/calibration/registered/*.json`、
`output/env/pegasus/calibration/job-staging/*/calibrate-argv.json`、`orchestrator/campaign/pipeline.py`、
`orchestrator/calibrator/sweep.py`、`docs/decisions.md`、`docs/archive/worklog-phase3-0916-1555.md`)。

## レンズ B — 記述の実物照合

段 5 で親が書いた decisions fragment と insight README と worklog fragment の**事実主張をすべて現物と照合**せよ。
plan・段 3 の所見を信じず、自分で file を開く。次を攻撃する。

1. **path・sha256・数値。** D と README に出る sha256 (4 較正の完全 hash と 16 桁接頭辞)、path (registered / job-staging /
   binaries)、`records` (1,000,000 / 2,000,000)、`submit_epoch` 4 値、`threads` 48、`clocks_per_us` 2100、workload 3 key の
   逐語、`ycsb.hh` の既定 10、CLI 既定 (extime 3 / sweep 3 / noise 10) を、1 つずつ現物で確かめ、誤りを file:line で示せ。
2. **識別子。** `layer3_report.SELF_INCONSISTENT_WITHIN_RUN_CALIBRATIONS`、`env_attestation.EFFECTIVE_CLOCK_METHOD`、
   `calibration_verify.load_verified_calibration`、`floor_pair_driver._bind_checkout_inputs`、`median/v1`、
   `floor-pair-spec/v3`、`b4_binary_record.place_record` / `place` (T-2697)、`output/env/<env_tag>/binaries/<sha256>` が
   現物に存在し、D の説明どおりの意味か。
3. **条件 3 の裏付け式。** `acquisition_receipt.allocation.pbs_jobid` → `job-staging/<pbs_jobid>/calibrate-argv.json` の
   `--binary` と `--binary-sha256`、receipt の `ccbench.binary_sha256` との一致を、genome 不在 2 件で実際に辿れ。
   pbs_jobid の表記 (`0:867876.nqsv`) と directory 名の対応も確認せよ。
4. **条件 5 の裏付け。** g1 の `attestation_profile.effective_clock.method` が `proc-cpuinfo` で他 7 件が現行 method であること、
   除外集合の path / sha256 が g1 と一致すること。
5. **D の「binder は protocol を照合しない」「verifier が現行 policy と照合するのは tolerance だけ」** を実装行で確認。
6. **T-2697 の着地状態。** `docs/archive/worklog-phase3-0916-1555.md` と `orchestrator/campaign/b4_binary_record.py` で、
   配置規則が README の記述 (git-ignored 複写、`place`) と一致するか。
7. **worklog fragment の事実。** 「registered 較正は 8 件」「8/8 ADMITTED」「§5 の値セル (行 154〜167) は bytes 不変」
   「codex 子 5 本」「計算ノード job は 0 本」が確認できるか (後 2 つは job dir の file 数で確認: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/` の `*-out.md` と `*.log.done`)。

## 制約

- 書込可能 tmp が無いので pytest 緑を要求しない。静的検査でよい。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- 所見は real / refuted / nit に分け、根拠 (file:line または現物 field) を必ず添える。攻撃が成立しなかった項目は正直にそう書け。
- 出力は NFC。U+0300〜U+036F を使わない。

## 出力形式

以下の H2 見出しをこの順で書く。**全部 `#` 2 個の H2** で、`###` は使わない。最後の節は必ず `## 総括` とする (`### 総括` と書いてはならない)。

## path・sha256・数値
## 識別子
## 条件 3 と条件 5 の裏付け
## 実装行の確認
## T-2697 と worklog の事実
## 総括
