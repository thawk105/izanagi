# 段 1 brief — [T-987] 8b oracle reviewed spec の設置形・contract test 改訂設計・事前登録値候補

worktree = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t987-oracle-spec-design`
(branch `worktree-dev-wave-t987-oracle-spec-design`、main 330f67d0 と同一 tree)

## scope

3 点を **設計し、承認パッケージとして裁定へ返す**。
(1) canonical path `output/s8b-oracle-spec/reviewed_spec.json` への設置形、
(2) contract test `test_schema_v1_has_no_durable_manifest_candidate_or_reviewed_spec` を
「durable 0 件」から「承認済み 1 件」形へ改訂する設計、
(3) 事前登録 7 分類 (n / master seed / block size / campaign・holdout ID /
generator versions / binding identity / run contract) の**値候補の導出**。

## 確定済みユーザー裁定 (変えない)

- 2026-08-12 第 6 束 [T-499] Q1 = (b): 承認手番は事前登録が固まるまで待つ。設計を先行する。
- 承認判断はユーザー手番。**機構の C1〜C6 を変えない。**
- 規律 2: contract test の受理集合を広げる変更は、広げる範囲と根拠を事前登録の形で明示する。
- **本 wave は実装差分ゼロで land してよい** (docs + insights のみ)。

## 不変条件 (破ったら停止)

- `output/s8b-oracle-spec/` と `output/s8b-oracle-manifest-candidates/` へ 1 byte も書かない。
- `APPROVED_SPEC_SHA256` を `None` から変えない。`SCHEMA_VERSION` を変えない。
- contract test の期待値を本 wave で変更しない (設計を返すだけ)。
- 承認済み値を「承認済み」と書かない。書けるのは「AI 草案・未承認」まで。

## 先行成果物との関係 (F35 stale 照合の結果)

**[T-499] 後継 wave (archive worklog entry 511、2026-08-13) が同じ射程の設計を既に納品済み** =
`output/insights/2026-08-12_t499-spec-producer-design/` (`package.md` に Q1〜Q4、
`producer-design.md`、`d302-schema-choice.md`、`preregistration-approval-package-draft.md`)。
`/work/SFC/tanab/dev-wave-jobs/rulings-inbox/` と worklog を走査した範囲で、
**その Q1〜Q4 はいずれも未裁定**である。よって本 wave の付加価値は次の 3 点に限る。

- A. (1) の再検証 — entry 511 の producer 設計が現 HEAD の一次資料と今も一致するか。
- B. (2) の**具体設計** — entry 511 は 3 状態 lifecycle gate の素描と「保留推奨」を出したが、
  署名・受理集合・通る正例を持つ設計は未提出。
- C. (3) の**値の導出** — entry 511 は 4 項目 (n=8 / master seed / block ID / campaign ID) を
  草案として出したが**導出過程を示していない**。残る generator versions / binding identity /
  run contract / holdout ID の候補と、各項目の「誰が決めるか」の分類も未整理。

## 親の brief 前実測 (すべて現 HEAD の一次資料。docs の記載は根拠にしない)

| # | 事実 | 出所 |
|---|---|---|
| M1 | holdout = `rr20`,`rr80`。configuration = `backoff_fixed_best`,`ident_all`,`p2_2_flag_opt`,`sort_best`,`stock_common`,`system_gate` の 6。1 replicate = 12 cell | `output/s8b-freeze/holdout_freeze.json` (confirmed_at 2026-07-16 by thawk105) |
| M2 | **単一 block 契約 (A3-3)** — manifest は block を正確に 1 件しか許さない | `orchestrator/campaign/s8b_oracle_manifest.py:302-305` |
| M3 | **spec 層は A3-3 を検査しない。** `validate_reviewed_spec` は `build_schedule` を呼ぶだけで `_validate_schedule` を通さない | `s8b_oracle_spec.py:123-137` と `s8b_oracle_manifest.py:221-271` |
| M4 | a12 stress-check は J=4〜13 の 60 cell 全て `cell_pass`、false-pass 率 U は J とともに単調増加し最大 0.00390 (α₁=1/40=0.025 の約 1/6)。判定式は `mean - q*sqrt(s/J) > 0`、B=10^6 | `output/env/pegasus/t139-a12-stress-check/full-v1/stress-check-simulation.json` |
| M5 | 同 artifact は自ら `claim_scope.value = "a11_empirical_stress_model_only"`、`pilot_ready = false`、`core_weak_null_calibration_complete = false`、未充足 pilot 前提 7 件を宣言 | 同上 |
| M6 | q(J): 4→10.9996, 5→6.6706, 6→5.2646, 7→4.5899, 8→4.1979, 9→3.9429, 10→3.7641, 11→3.6320 | 同上 `q[]` |
| M7 | pegasus 登録済み較正 2 件はいずれも `status=accepted`、records=1,000,000 (L3 の 4.9 倍で下限基準採用)、threads=48、clocks_per_us=2100、within-run CV 1.17% / 1.25% | `output/env/pegasus/calibration/registered/*.json` |
| M8 | between-run CV の実測は **linux-baremetal のみ** (rr5 0.67% / rr50 1.07% / rr95 0.11%、extime=3)。**rr20・rr80 の between-run 実測は存在しない** | `output/env/linux-baremetal/calibration/between_run_noise_*.json` |
| M9 | floor protocol が同型の先例: `env_tag=pegasus`, `contract_sha256=e576e9cd…`, `ccbench_pin=d706650c…`, `extime_s=5`, `reps=5`, `n_sessions=8`, `master_seed="2026-07-18T17:16:12+09:00"`, `allowed_excluded_reasons` = 4 件固定順, freeze pin sha256=315b1eb8… | `output/s8b-freeze/floor_protocol.json` |
| M10 | floor protocol が pin する freeze sha256 は現 `holdout_freeze.json` の実 bytes と**一致**する | 親が sha256 を実算出 |
| M11 | pegasus の env 契約は generation 1 で active、`contract_sha256=e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` | `orchestrator/campaign/env_contract_activations/00000001.json` |
| M12 | ccbench pin の 2 値: floor protocol = `d706650c…`、現 gitlink と `s8b_approved.CCBENCH_FULL_SHA` = `511c9538e4e8efa54b45cda62e72389ed3b706ec` | 上記 + `git submodule status` |
| M13 | `run_contract` の 4 値は validator が固定: `verify="legacy+s2"`, `screening="off"`, `bench_max_rounds=1`, `reps`/`extime` は `s8b_experiment_numbers` の `APPROVED_REPS=5`/`APPROVED_EXTIME_S=5` と完全一致 | `s8b_oracle_manifest.py:396-427` |
| M14 | generator_versions の 5 canonical path は code 側が固定。現 HEAD の実 sha256 は artifacts=b29f3dd6…, judge=6e90a775…, materializer=38ed8790…, outcome_stage_contract=f8a0bb22…, report=cc28c860… | `s8b_oracle_manifest.py:53-62` + 実算出 |
| M15 | `output/s8b-freeze/` に approval/active/revocation の世代 file は**存在しない** = `no-active-ratified-freeze` は今も先行 blocker | `ls output/s8b-freeze` |
| M16 | contract test の現受理集合 = 2 directory 配下の file 数が 0 件のときだけ緑 | `orchestrator/tests/test_s8b_oracle_manifest_contract.py:130-146` |

## 親の provisional 裁定 (P。攻撃対象)

- **(P1)** `n` の下限は a12 からは導けない。a12 が与えるのは「J∈[4,13] の外は
  検証済み包絡の外」という**上限側の制約**だけである。M4 の U は J とともに増えるので、
  「a12 が大きい n を要求する」という読みは誤り。
- **(P2)** `n = 8` を推す根拠は (i) 単一 block 契約下で J=n、(ii) J∈[4,13] の包絡内、
  (iii) 精度係数 q(J)/√J が 8 以降で平坦化する (5.50→2.98→2.15→1.73→**1.48**→1.31→1.19→1.10)、
  (iv) floor protocol の `n_sessions=8` と同値で先例整合、(v) 純測定時間 12×8×5×5 秒 = 40 分。
- **(P3)** `master_seed` は floor 先例に合わせ **承認時刻の ISO-8601 JST 文字列**とする。
  entry 511 草案の slug 形式より、先例整合かつ「結果を見る前に確定した」ことの検証が容易。
- **(P4)** `ccbench_pin` は「現凍結 floor と比較する本走 = `d706650c…`」「floor を再測定して
  v2 を作る本走 = `511c9538…`」の二択であり、**spec 単独では決まらない**。
  本走の目的が決まるまで承認できない項目として分類する。
- **(P5)** M3 は本 wave 発の新規所見。spec 層が A3-3 を検査しないため、複数 block の spec は
  承認を通過し manifest 生成で初めて落ちる。**検査の新設は本 wave では実装せず**、
  裁定パッケージの記録項として返す。
- **(P6)** contract test の改訂は「0 件 ⊊ {承認済み exact 1 件}」で受理集合が真に広がる。
  設計は**署名で書き、通る正例を 1 つ添える**。実装は承認後の別タスク。

## 成果物影響 (DW-G05)

本 wave を実装ゼロで畳んだ場合の影響 = **certified 選択・レポート・台帳のどの値も変わらない**。
`APPROVED_SPEC_SHA256` は `None` のままで oracle 本走は `no-approved-spec` 以前に
`no-active-ratified-freeze` で止まり続ける。変わるのは裁定材料の有無だけである。

## 成果物の形

`output/insights/2026-08-15_t987-oracle-spec-prereg/` に
`package.md` (裁定パッケージ)、`contract-test-revision.md` (B の設計)、
`preregistration-values.md` (C の導出)、`verbatim/` (子出力)。
worklog / decisions は spool fragment。実装差分ゼロ。

## 並列分割

段 2 プラン子 1 本 (read-only)、段 3 敵対 2 本 (sol / luna、read-only)。
実装面が無いため段 5 実装子は起こさない。
