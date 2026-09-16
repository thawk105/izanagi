単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/s1-brief.md

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の
停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/s1-brief.md`
  — 親 brief (scope、不変条件、確定済み裁定、provisional 裁定 (P1)〜(P5)、変更面アンカー)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/verbatim-rulings.md`
  — 既裁定 (D2044 項 11、D1641、D1695、D1696、D1887、D1936 項 7 と末尾、D1855、D1854、D15、D1311、D1537、D1538、D1812、D1536、D1974) と事前登録 §5 / §5.1 / §11.1 / §11.2 抜粋 / §11.3、前 wave の insight README の逐語
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/probe-calibrations-summary.txt`
  — 親の実測: registered 較正 8 件の sha256 / workload / status / saturation.records
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/probe-calibrations-diff.txt`
  — 親の実測: 同 8 件の genome / acquisition_receipt / attestation / notes / noise_floor
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/probe-admission.txt`
  — 親の実測: 同 8 件を `calibration_verify.load_verified_calibration` (mode=required) へ通した結果と effective-clock method
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/probe-calibrate-argv.txt`
  — 親の実測: silo 4 job の `calibrate-argv.json` と実走ログの reps / noise floor 行
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/orchestrator/campaign/floor_pair_driver.py`
  — 凍結 spec の契約 (`FrozenPerfConfig` :193、`_parse_perf` :778、`_bind_checkout_inputs` :1122、`load_frozen_spec` :1197、`SESSION_REDUCER_ID` 等 :56-71)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/orchestrator/campaign/calibration_verify.py`
  — 較正の admission 入口 (`load_verified_calibration` :81)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/orchestrator/calibrator/cli.py`
  — calibrator CLI の既定値 (`--extime` :150、`--sweep-reps` :151、`--noise-reps` :152)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/orchestrator/calibrator/runner.py`
  — bench argv の組み立て (`base_flags` :1119-1125 付近。`-ycsb_max_ope` を渡さない)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/orchestrator/campaign/env_contract.py`
  — Pegasus 環境契約の世代 g1/g2 と較正 pin (`_build_registry` :246-285)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/orchestrator/campaign/layer3_report.py`
  — D1537 の消費側除外集合 (`SELF_INCONSISTENT_WITHIN_RUN_CALIBRATIONS` :79) と genome 不在 record の扱い (`_floor_protocol_and_basis` :477)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/docs/phase3-b4-reflux-ablation-preregistration.md`
  — 事前登録本文 (§0、§1、§5、§5.1、§11.0〜§11.3)。編集対象は §11.1 の D1812 (c) 追記段落末と §11.3 第 1 bullet の追記末だけ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/docs/spool/README.md`
  — 台帳 fragment の共通規則
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/docs/spool/decisions/README.md`
  — decisions fragment の文法
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/docs/spool/worklog/README.md`
  — worklog fragment の文法 (完了 / 更新 / base digest)

上記以外に repo 内を読んでよい。特に
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/external/ccbench/include/ycsb.hh` (:22 の `ycsb_max_ope` 既定 10)、
`orchestrator/campaign/pipeline.py` (`PerfConfig` :184、qualification shape :1697-1706、`S2_FLAGS` :159)、
`orchestrator/campaign/p3_s4_loop.py` (`default_perf` :1565)、`orchestrator/calibrator/sweep.py`、
`orchestrator/calibrator/stability.py`、`orchestrator/tests/test_floor_pair_driver.py` (spec fixture :225-330)、
`output/env/pegasus/calibration/registered/*.json`、`output/env/pegasus/calibration/job-staging/*/calibrate-argv.json`、
`docs/decisions.md` (D1640、D1699、D1779、D1266、D1383、D1453、D1694) は一次資料である。
`docs/worklog.md` / `docs/archive/` は entry 1535 (rr5 較正)・1544 (T-2288 持ち越し本文) を引くときだけ開く。

## この段の仕事

**docs-only wave の変更内容を file:line 粒度で起草する。** 実装面 (orchestrator/、tools/、hooks/、test) は 1 byte も変えない。
起草する対象は次の 5 つである。

1. **A-3 (PerfConfig の `extime` / `reps` / `ycsb_max_ope` の承認)** — 親の (P1) を検査し、採用値とその根拠を
   decisions fragment の 1 D として書ける形 (決定 / 理由 / 却下した選択肢) に起こす。根拠は一次資料の file:line と
   成果物 path で示す。**calibrator 出力から導ける値と導けない値を分け、後者をどう承認するかを明示する。**
2. **A-4 (contention セル集合の具体列)** — 親の (P2) を検査し、3 workload × セルの具体列 (各 cell の
   `records` / `threads` / `workload` 3 key の逐語 / `extime` / `reps` / `ycsb_max_ope`、束縛する較正の path と sha256) を
   decisions fragment の 1 D として起こす。「§5 に列挙する contention セル」を §5 のどこから読むかを一次資料で示し、
   読めないならそう書いた上で導出規則を書く。
3. **C 群 (同条件 accepted 較正が複数あるときの適格条件と採用順序)** — 親の (P3) を検査し、**値に依存しない**規則として
   decisions fragment の 1 D に起こす。各適格条件について「何を根拠に (どの file:line / 既裁定)」「値依存でないことの
   説明」「rr50 の 2 件 (g1 `753f535a` / g2 `94a4b79f`) と rr95 / rr5 への適用結果」を書く。**loader / binder / gate を変えない
   人手の選択規則である**ことを保つ。
4. **T-2465 (§11.3 の追記訂正)** — 親の (P4) を検査し、§11.1 と §11.3 へ足す追記の逐語案を書く。既存文は書き換えず追記のみ。
   引く D は既に採番済みのもの (D1641・D1695・D1887・D1936・D1453・D1694 等) に限る。
5. **worklog fragment** — T-2288 の `更新` 本文案 (残前提 = A-5 のみ、と何が決まったか) と T-2465 の `完了` 本文案。
   base digest は親が別途取る (T-2288 = `f0a10547…`、T-2465 = `994bb67c…`)。

あわせて次を plan に含める。

- **A-5 の裁定パッケージ案**: 窓 2 件の日時 (`not_before` / `not_after`)・`campaign_id`・`seed_hex`・出力名 3 個
  (`artifact_relpath` ×2、`summary_relpath`) について「何が要るか」「誰が決めるか (§11.1 の逐語)」「AI が候補を書いてよい範囲」を、
  値を起草せずに書く。
- **受入と検査**: 親が login node で走らせる焦点走 (事前登録 §5 を parse する consumer の test 4 本の node 名) と
  `tools/check_docs.py`、`spool_fold.py --dry-run` の順序。
- **親 brief への反証**: (P1)〜(P5) と「段 1 で判明した新事実」に誤り・過剰一般化・見落としがあれば file:line で指摘する。
  brief の実測値 (8 件 ADMITTED、g1 の method、argv に `--extime` 無し) を自分でも確かめる。

## 制約

- 書込可能 tmp が無いので pytest 緑を要求しない。静的検査でよい。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- 規律 2 (正しさゲートを緩めない) と規律 3 (結果を見る前に規則を定める) を緩める案は書かない。
- A-5 の値 (日時・識別子・seed・出力名) を起草しない。
- 出力は NFC。U+0300〜U+036F を使わない。

## 出力形式

以下の H2 見出しをこの順で書く。**全部 `#` 2 個の H2** で、`###` は使わない。最後の節は必ず `## 総括` とする (`### 総括` と書いてはならない)。

## 前提の検査
## A-3 の起草
## A-4 の起草
## C 群の起草
## T-2465 の追記案
## worklog fragment 案
## A-5 裁定パッケージ案
## 受入と検査の順序
## 親 brief への反証
## 総括
