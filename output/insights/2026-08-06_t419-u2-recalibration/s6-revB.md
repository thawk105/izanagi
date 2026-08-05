結論は **NO-GO**。親の実測 `4 failed / 307 passed` は所与として扱い、こちらでは pytest・build・実機実走を行っていない。緑は主張しない。

## 所見

### RC-01 / caller は直接 4 production 経路、test 6 file。さらに receipt consumer へ推移波及する

1 行要約: schema-valid な有限値では同値だが、抽出後の例外挙動は所有外 campaign まで波及する。

根拠:

| 種別 | caller |
|---|---|
| receipt の独立再計算 | [_independent_comparison_passes:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:176)。入口は [receipt_matches_contract:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:152) |
| calibrator self-check | [_effective_clock_self_comparison_passes:405](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:405)。early caller は [:483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:483)、late caller は [:683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:683) |
| silo live attestation | [silo_ladder_rung1.py:1974](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/silo_ladder_rung1.py:1974) |
| silo raw receipt 再導出 | [silo_ladder_rung1.py:3427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/silo_ladder_rung1.py:3427) |

test の全直接参照は次の 6 file に閉じる。

- [test_execution_guard.py:227,544,548,594,601,646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_execution_guard.py:227)
- [test_calibrator_certify.py:272,760,894,948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:272)
- [test_env_attestation.py:300,1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_env_attestation.py:300)
- [test_env_contract.py:837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_env_contract.py:837)
- [test_silo_ladder_rung1_evidence.py:960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_silo_ladder_rung1_evidence.py:960)
- [test_silo_ladder_rung1_driver.py:903,913,1990,1999](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_silo_ladder_rung1_driver.py:903)

`_effective_clock_band_math_passes` の production caller はなく、test caller は [test_execution_guard.py:544,594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_execution_guard.py:544) のみ。

`env_attestation.py` はこの関数を呼ばず、issuer 側の別実装を保持している（[env_attestation.py:982-1009](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/env_attestation.py:982)）。したがって抽出の直接影響は consumer 側だけである。

未実走の推移波及候補は、`receipt_matches_contract()` を通る [loop.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/loop.py:88)、[s8b_floor_campaign.py:885](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/s8b_floor_campaign.py:885)、[s8b_oracle_driver.py:794,937](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/s8b_oracle_driver.py:794)、[s8b_oracle_report.py:1371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/s8b_oracle_report.py:1371)、[s8b_ratified_freeze.py:1869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/s8b_ratified_freeze.py:1869) と各対応 test。赤になるのは後述 REG-01 の malformed/non-policy 例外 edge を fixture が踏む場合であり、現時点では speculative。

判定: caller 列挙は **real**、未実走 file の赤予測は **speculative**。  
成果物影響: receipt 再検算例外が campaign/freeze/report の生成を構造化拒否ではなく中断させうる。  
区分: **must-fix**。  
推奨対応: 6 file に加え上記 downstream test と `test_pegasus_tools.py` を受入対象へ追加する。

---

### PC-01 / early rejection は「実際に判定した α profile」を proof chain に残していない

1 行要約: `rejection.json` は導出値だけで、全 samples・tolerance・method・governor・profile hash がない。

根拠:

- 判定対象は wrapper の `attestation-pre.json` ではなく、CLI が cooldown 後に再取得する `dynamic_pre` である（[certify_calibration.sh:548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:548)、[cli.py:588-629](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:588)）。
- 診断 projection は入力の tolerance と全 samples を捨て、median・上下限・違反 sample だけを返す（[cli.py:411-424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:411)、[execution_guard.py:214-275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:214)）。
- `rejection.json` にも raw profile/hash は書かれない（[cli.py:520-530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:520)）。
- 親が更新条件にした `tolerance_pct == 2.0` は artifact 内に存在せず、`policy_matches: true` からしか推論できない（[s4-adjudication.md:161-167](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:161)）。

判定: **real**。  
成果物影響: final receipt が `rejection.json` を hash 束縛しても、第三者は失敗した α profile を再構成・再計算できず、「決定的事実」にならない。  
区分: **must-fix**。  
推奨対応: schema-versioned rejection receipt に exact effective-clock input（全 samples、tolerance、method、governor）と profile SHA-256 を保存する。

---

### PC-02 / 「独立 published-bytes self-comparison」は test helper にしか存在しない

1 行要約: 実際の certify job と final receipt は着手条件 (iii) を実行・記録しない。

根拠:

- bytes 再読は test-local helper のみ（[test_calibrator_certify.py:268-278](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:268)）。呼ぶのも tmp artifact 用 test だけ（[:709-736](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:709)）。
- production publish は rename 後に target bytes を再読しない（[cli.py:704-740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:704)）。
- job wrapper は calibrator rc を記録して終了するだけ（[certify_calibration.sh:742-770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:742)）。
- collector は bytes を hash するだけで canonical predicate を評価しない（[collect_receipt.py:153-179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/collect_receipt.py:153)）。
- したがって「accepted publish → (ii)(iii) 到達」は実装と不一致（[s4-adjudication.md:135](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:135)）。

判定: **real**。  
成果物影響: accepted artifact と final receipt に独立 self-pass の証拠がなく、proof chain が未閉鎖。  
区分: **must-fix**。  
推奨対応: CLI から独立した verifier で publish target bytes を再読し、入力 SHA・判定・policy identity を専用 receipt に記録して final receipt へ束縛する。

---

### REG-01 / public predicate の「1 bit も変わらない」は例外意味論で破れている

1 行要約: 新 evaluator は shape/policy 不一致でも band math を評価するため、旧 `False` が例外へ変わる。

根拠:

- 新 public 関数は常に evaluator を呼ぶ（[execution_guard.py:183-190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:183)）。
- evaluator は `input_valid` / `policy_matches` が偽でも `float(statistics.median(...))` まで進む（[:224-275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:224)）。
- 捕捉集合に `OverflowError` がない（[:276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:276)）。
- 静的反例は `expected={"samples_mhz":[10**400],"tolerance_pct":0.0}`。旧 HEAD は policy 不一致で band math 前に `False`、新版は巨大整数の `float()` で `OverflowError`。
- 新 vector 群にも overflow/custom Mapping はない（[test_execution_guard.py:558-603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_execution_guard.py:558)）。

判定: API 回帰は **real**、現行の正規 profile での発火は **speculative**。  
成果物影響: malformed/non-policy receipt が structured reject でなく campaign 例外となり、成果物生成を中断する。  
区分: **must-fix**。  
推奨対応: public path は shape/policy 不一致を先に short-circuit し、診断 path だけ eager evaluation する。併せて `OverflowError` negative vector を追加する。

---

### NE-01 / `not_evaluated` の 8 項目は過剰申告ではないが、列挙漏れがある

1 行要約: final artifact の assemble/schema validation が未実行なのに列挙されていない。

根拠:

- 8 項目は [cli.py:64-73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:64)。
- early 分岐後に未実行となる dynamic isolation、benchmark、post probe、quality、late gate、publish は [cli.py:644-741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:644) と対応し、実行済み項目を「未評価」とする反例は得られなかった。
- ただし実 result に対する `_assemble_v2()` は schema validation を 2 回行う（[cli.py:490-509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:490)）が、early 時には実行されない（[:686-687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:686)）。
- `"dynamic-pre-isolation"` は visibility 検査が既に済んでいるため、実際には未実行の `composite_competing_probe("dynamic-pre")` を指すと明記しないと曖昧（[:603-610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:603)、[:657](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:657)）。

判定: 列挙漏れは **real**、名称の曖昧さは nit。  
成果物影響: proof が「未評価検査の完全列挙」を名乗ると、final schema 未検証を隠す。  
区分: **must-fix**。  
推奨対応: `final-artifact-assembly-and-schema-validation` を追加し、dynamic 項目を具体名へ変更する。PC-02 を実装するなら published-bytes check も列挙する。

---

### OPS-01 / collector 自体は rejection-only を扱えるが、runbook の attempt path が実装と違う

1 行要約: collector の必須ファイル判定は安全だが、手順どおりの raw `$PBS_JOBID` path では collection が失敗する。

根拠:

- collector は calibrator attempt に特定 filename を要求せず、非空 manifest だけを要求する（[collect_receipt.py:76-91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/collect_receipt.py:76)）。
- 必須なのは job-staging の submit/acquisition/job-result で、`calibrate_rc` は整数なら非 0 でも受理する（[:116-141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/collect_receipt.py:116)）。
- CLI attempt path は `:` を `_` へ sanitize する（[cli.py:274-280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:274)）。
- runbook は raw `<PBS_JOBID>` を両 namespace に使うよう記載する（[tools/pegasus/README.md:118-126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/README.md:118)）。実際は attempts が `0_...`、job-staging が `0:...`。
- collector test も `calibration.json` を置く成功 fixture しかなく、rejection-only/nonzero rc は固定していない（[test_pegasus_tools.py:873-915](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_pegasus_tools.py:873)）。

判定: collector 互換性は反証できなかった。runbook 不一致は **real**。  
成果物影響: 手順を逐語実行すると `final-receipt.json` が作れず、rejection proof chain が未収集になる。  
区分: **must-fix**。  
推奨対応: wrapper が raw/sanitized path を出力するか、runbook を二 namespace 明記へ直し、rejection-only collector test を追加する。

---

### OPS-02 / clean commit は投入時点しか束縛せず、live worktree は job 中に drift できる

1 行要約: source commit と clean 検査は job 冒頭だけで、後段 helper は共有 worktree の可変 bytes を直接実行する。

根拠:

- submitter は HEAD と clean を qsub 前に確認する（[submit_certify.sh:71-81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/submit_certify.sh:71)）。
- job も冒頭で commit・script SHA・clean を再照合する（[certify_calibration.sh:172-206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:172)）。
- その後は live `$TOOLS/run_probe.py`、live `runner.py`、live `orchestrator/calibrate.py` を読む（[:341-343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:341)、[:648-665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:648)、[:720-731](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:720)）。immutable snapshot を作るのは CCBench だけ（[:486-507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:486)）。
- submitter は `REPO_ROOT` を script 位置から求める一方、qsub 前に `cd "$REPO_ROOT"` せず（[submit_certify.sh:12-15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/submit_certify.sh:12)、[:166-180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/submit_certify.sh:166)）、job は `$PBS_O_WORKDIR` を repo とみなす（[certify_calibration.sh:33-36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:33)）。
- CCBench HEAD=gitlink と tracked-clean は検査するが、recursive submodule 状態は検査しない（[certify_calibration.sh:486-491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:486)）。現 worktree は CCBench 自体は一致・clean、nested Shirakami は未初期化だった。後者が silo target を壊す証拠はなく speculative。
- policy files の存在・calibration policy の非 symlink は submit/job 両側で確認される（[submit_certify.sh:39-48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/submit_certify.sh:39)、[certify_calibration.sh:106-113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:106)）。

判定: mid-job source drift と CWD coupling は **real**。nested submodule の実害は **speculative**。  
成果物影響: receipt の `source_commit` と実際に判定・生成した Python bytes が異なりうる。  
区分: **must-fix**。  
推奨対応: superproject helper も detached snapshot から実行して全 source SHA を receipt に束縛する。暫定でも、worktree root から投入し job 終了まで編集禁止を明文化・機械化する。

---

### OPS-03 / early gate は benchmark 前だが全 build 後で、約 1/3 の費用根拠は壊れている

1 行要約: nominal build cap 1080 秒は実際の逐次 timeout 合計 2340 秒と一致しない。

根拠:

- header は `CCBench=900 + gflags=60 + glog=120 = 1080` とする（[certify_calibration.sh:7-11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:7)）。
- 実際は gflags が 60 秒×3（[:395-415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:395)）、glog が 120 秒×3（[:459-480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:459)）、CCBench が 900 秒×2（[:497-507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:497)）。合計 cap は 2340 秒。
- receipt はなお 1080/6610 を記録する（[:591-623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:591)）。未実走の `test_pegasus_tools.py` もこの誤った literal を固定する（[test_pegasus_tools.py:200-214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_pegasus_tools.py:200)）。
- build 後は残りが正であることしか確認せず、calibrator の必要 envelope を満たすか確認しない（[certify_calibration.sh:639-644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:639)）。

certify 実挙動の予測:

1. gflags/glog/CCBench build、binary hash、wrapper pre-profile、acquisition receipt、perf smoke まで実行。
2. CLI の static probe → cooldown → dynamic probe → TSC → schema preflight 後、[cli.py:628-642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:628) で拒否。
3. CLI rc=1。attempt には collection 前は `rejection.json` のみ。`calibration.json`、`calibration.md`、`window-probes.json`、`candidate.json`、`publish.json` は出ない。
4. wrapper は `job-result.json(calibrate_rc=1)` と `failure.json(stage=calibrate,rc=1)` を残し、post-attestation を実行せず job rc=1 で終了（[certify_calibration.sh:742-770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/tools/pegasus/certify_calibration.sh:742)）。
5. 後続 collector が成功すれば sanitized attempt に `final-receipt.json` が加わる。

判定: build 実行と cap 不一致は **real**。「約 1/3」という実費比率は **根拠不足/speculative**。  
成果物影響: reservation receipt が実行可能 envelope を過大主張し、full attempt が途中 timeout しても「予約済み」に見える。  
区分: **must-fix**。  
推奨対応: 逐次 timeout の和で reservation を再計算し、CLI 起動前に `remaining >= calibrator_required_s` を検査する。費用表現は実測まで「benchmark 部分を省く」に限定する。

---

### TEST-01 / 現差分は親が許可した 4 node の期待値更新前で、受入可能状態ではない

1 行要約: 既知赤は裁定済みでも、現在の test bytes はまだ late-artifact を要求している。

根拠:

- 旧 test は probe 3 回、`calibration.json/md/window-probes` 存在、`rejection.json` 不在を要求する（[test_calibrator_certify.py:739-784](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:739)）。
- metamorphic test の policy=2 側も probe 3 回と v2 calibration rejection を要求する（[:914-931](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:914)）。
- 親の更新許可と維持条件は [s4-adjudication.md:146-168](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:146)。

判定: **real**。  
成果物影響: 現時点の acceptance proof は 4 failed を含み、commit/submit の根拠にならない。  
区分: **must-fix**。  
推奨対応: 許可された 4 node だけを更新。ただし PC-01 のため、先に rejection artifact に full clock input/tolerance を記録しないと「旧性質を落とさない」条件を満たせない。

---

### REC-01 / 段 4 裁定には実装・運用と食い違う記述が複数ある

1 行要約: bit 同値、proof 到達、bytes 不変、費用、α 一般化が現在の証拠を越えている。

根拠:

- 「public は 1 bit も変わらない」[:56-59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:56) は REG-01 の例外反例で不成立。
- 「early では rejection.json だけ」[:94-97](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:94) は job 終了時だけなら正しいが、所定の collection 後は `final-receipt.json` も残る。
- 「どの bytes 生成規則も変えない」[:104-105](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:104) は `rejection.json` に新 field を追加する実装（[cli.py:520-527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:520)）と矛盾。
- 1 job の拒否を「α は計算ノードで帯内にならない決定的事実」と一般化する [:133-134](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:133) のは、同裁定が採用した LIVE-01 と矛盾する。証明できるのは exact job/profile の failure のみ。
- accepted publish で (iii) 到達する [:135](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:135) は PC-02 により誤り。
- 「registry へ入らない」[:136](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:136) は曖昧。artifact は filesystem の `registered/` へ入る（[cli.py:704-724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:704）が、`env_contract.REGISTRY/current` へは活性化されない、が正確。
- 「約 1/3」は OPS-03 のとおり未立証。

判定: **real**。  
成果物影響: 裁定記録が未取得 proof と単発環境観測を完了事実として後続 wave に渡す。  
区分: **must-fix**。  
推奨対応: commit 前に上記を exact-job、filesystem registered、activation registry、job-exit/after-collection の各語へ修正する。

## 反証できなかった点

- `collect_receipt.py` が `calibration.json/md/window-probes` を必須扱いする、という破壊仮説は**反証できなかったのではなく、コード上反証できた**。rejection-only でも非空なら収集可能。
- `diagnostics` / `not_evaluated` の追加で repo 内 exact-shape reader が壊れる反例は**得られなかった**。既存 test は部分 field 参照で、collector は opaque bytes として扱う。ただし `rejection.json` に `schema_version` がない点は nit。
- 新診断に時刻・path・hash はない。浮動値は実測ごとに変わるが、test は固定 fixture と `pytest.approx` を用いており、実機値の焼き込みは**反証できなかった**。
- schema-valid・有限・plain-dict 入力について、canonical boolean が旧版から変わる反例は**得られなかった**。REG-01 は malformed/overflow 例外面。
- late gate の保持、publish policy identity gate、early 時の benchmark 非開始は実装どおりであり、ここは**反証できなかった**。
- worktree root を CWD とし、job 中に一切変更せず、外部 preflight が成功する条件なら、linked worktree 自体が qsub を阻む反例は**得られなかった**。

## 総括

- 最重要 1: early rejection は判定した α profile の raw input/tolerance/method を保存せず、「決定的事実」を再計算できない。
- 最重要 2: 独立 published-bytes self-comparison は test-only で、actual job/final receipt は着手条件 (iii) に未到達。
- 最重要 3: live worktree helper と誤った build cap により、source proof と reservation proof の双方が閉じていない。
- public predicate には旧 `False` が `OverflowError` へ変わる所有外 consumer 回帰がある。
- collector 自体は rejection-only を扱えるが、runbook の raw/sanitized attempt path が誤っている。
- 親実測の 4 failed は現在も未解消であり、こちらでは pytest を実走していない。
- 以上から、commit・production certify 投入の双方を許可できない。

**NO-GO — raw failing profile の束縛、actual published-bytes 独立検査、predicate 例外同値、reservation/source proof、4 node 更新が完了するまで投入不可。**