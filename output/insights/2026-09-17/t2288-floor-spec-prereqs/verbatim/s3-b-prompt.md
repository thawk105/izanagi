単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/s1-brief.md

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の
停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/s1-brief.md` — 親 brief (検査対象)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/s2-plan-out.md` — 段 2 plan (検査対象)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/verbatim-rulings.md` — 既裁定と事前登録の逐語
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/probe-calibrations-summary.txt` — 親の実測 (registered 較正 8 件)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/probe-calibrations-diff.txt` — 親の実測 (genome / receipt / attestation)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/probe-admission.txt` — 親の実測 (admission と effective-clock method)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-spec-prereqs/probe-calibrate-argv.txt` — 親の実測 (calibrate argv と実走ログ)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/orchestrator/campaign/floor_pair_driver.py` — 凍結 spec の契約
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/orchestrator/campaign/calibration_verify.py` — 較正 admission
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/orchestrator/calibrator/runner.py` — bench argv 組み立て
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/orchestrator/calibrator/cli.py` — calibrator CLI 既定
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/external/ccbench/include/ycsb.hh` — CCBench の YCSB flag 既定
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/docs/spool/README.md` — fragment 共通規則
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/docs/spool/worklog/README.md` — worklog fragment 文法
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-spec-prereqs/docs/spool/decisions/README.md` — decisions fragment 文法

上記以外に repo 内を読んでよい (`output/env/pegasus/calibration/` 全域、`orchestrator/campaign/env_contract.py`、
`orchestrator/campaign/layer3_report.py`、`orchestrator/campaign/pipeline.py`、`orchestrator/calibrator/sweep.py`、
`orchestrator/tests/test_floor_pair_driver.py`、`orchestrator/tests/test_p3_b4_*.py`、`tools/check_docs.py`、
`docs/phase3-b4-reflux-ablation-preregistration.md`、`docs/decisions.md`)。

## レンズ B — 実物照合・閉包・実効性

plan を守らせず検査せよ。**親 brief 自身も検査対象である。** 親の実測値とその一般化を疑え。次を攻撃する。

1. **実測の再現。** 親が言う「registered 較正 8 件、silo は rr5×1 / rr50×2 / rr95×1」「8/8 ADMITTED」「g1 `753f535a` の
   effective-clock method は旧 `proc-cpuinfo`」「silo 4 job の calibrate argv に `--extime` 無し」「runner は
   `-ycsb_max_ope` を渡さない」「CCBench 既定 `ycsb_max_ope=10`」を、自分で file を開いて確かめよ。食い違いは file:line で示せ。
2. **閉包。** silo の accepted 較正が `registered/` の外 (attempts/、insights/、他の env、圧縮内) に無いか。genome 欄が無い
   2 件を silo と判定する根拠 (job-staging の `calibrate-argv.json` の `--binary`) は tracked か、その path は規則の適用者が
   機械的に辿れるか。今後の較正が `genome` 無しで registered に入る経路が残っているか (D1538 の逐語と layer3 の実装を照合)。
3. **規則の機械適用性。** (P3) の (c1)〜(c5) を、spec を書く人が現物 JSON だけから判定できるか。判定に要る field を
   1 つずつ file:line で示せ。判定できない条件 (例: 「現行 policy の method」の正本がどこにあるか) があれば指摘せよ。
   採用順序の `acquisition_receipt.qsub.submit_epoch` は全 accepted 記録に存在するか、同値衝突の可能性はあるか。
4. **A-4 の具体列の束縛可能性。** 親が書いた 3 cell (workload 3 key の逐語 `{"ycsb_zipf_skew":"0.9","ycsb_rratio":"<rr>","ycsb_rmw":"0"}`、
   records = 採用較正の `saturation.records`) が `_bind_checkout_inputs` の全照合 (env_tag / threads / clocks_per_us /
   workload dict exact / records) を通るかを、較正 JSON の実 field 値で確かめよ。`ycsb_rmw` の表記 (`"0"` と `"false"`) の
   違いが束縛を壊す箇所は無いか。
5. **A-3 の動作点論。** 「extime と max_ope は較正した動作点を変えるが reps は変えない」は runner / driver の実装上
   正しいか (`-extime` と `-ycsb_max_ope` が bench にどう渡り、reps が何を繰り返すか)。D1854 の「rratio・rmw・max_ope は
   resident peak に効く」との整合。
6. **成果物の形式。** plan が書く decisions / worklog fragment 案が `docs/spool/*/README.md` の文法 (frontmatter・H2 形・
   placeholder・base digest・`remaining: none`・引用符禁止) を満たすか。§11 への追記が `tools/check_docs.py` の
   予算・lint に掛かる可能性 (行長・placeholder 語) があるか。
7. **焦点走の対象。** 事前登録 §5 を parse する consumer とその test (`orchestrator/tests/test_p3_b4_*.py`) のうち、
   §11 の追記で影響を受けうる node があるか。無いなら無いと根拠付きで書け。

## 制約

- 書込可能 tmp が無いので pytest 緑を要求しない。静的検査でよい。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- 所見は「real / refuted / scope 外」の候補として、根拠 (file:line または成果物 path と field) を必ず添える。
- 出力は NFC。U+0300〜U+036F を使わない。

## 出力形式

以下の H2 見出しをこの順で書く。**全部 `#` 2 個の H2** で、`###` は使わない。最後の節は必ず `## 総括` とする (`### 総括` と書いてはならない)。

## 実測の再現
## 閉包
## 規則の機械適用性 (P3)
## A-4 の束縛可能性 (P2)
## A-3 の動作点論 (P1)
## 成果物の形式
## 焦点走の対象
## 親 brief の誤り
## 総括
