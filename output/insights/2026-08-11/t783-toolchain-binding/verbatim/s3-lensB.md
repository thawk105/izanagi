## Lens B レビュー

静的検査のみ。pytest は未実行です。結論は **NO-GO** です。

### [must-fix] B1 — `DW-G04` の pilot 発火経路は実在しない

`--mode pilot` 自体は CLI に存在しますが、計算ノードへ投入する既存経路は確認できません。

- CLI の pilot 分岐は直接起動時だけです。[s8b_floor_campaign.py:3514](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:3514)、[s8b_floor_campaign.py:3571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:3571)
- 実投入 shell は `--mode official` 固定です。[floor_campaign.sh:961](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/tools/pegasus/floor_campaign.sh:961)
- submit script も job script を固定投入するだけで、pilot 切替を持ちません。[submit_floor.sh:410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/tools/pegasus/submit_floor.sh:410)
- 既存の `0:873225` は `mode=official`、driver rc=2 の拒否成果物です。[job-result.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/output/env/pegasus/floor/job-staging/0:873225.nqsv/job-result.json:1)

したがって、A-2 を land しても既存の compute artifact path では到達せず、floor binary・report・certified selection の受理集合は変化しません。

brief の「pilot 床値 campaign で runnable today」という主張は refuted です。[brief.md:80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/brief.md:80)

### [must-fix] B2 — 追加する report field が downstream の exact schema で拒否される

プランは manifest/result のトップレベルへ `build_toolchain_binding` を追加しつつ、schema constants は変更しないとしています。[out-plan.md:505](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:505)、[out-plan.md:570](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:570)

しかし downstream はトップレベル key を完全一致で検査します。

- `_MANIFEST_KEYS` に新 field がない。[s8b_ratified_freeze.py:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_ratified_freeze.py:189)
- `_RESULT_KEYS` に新 field がない。[s8b_ratified_freeze.py:199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_ratified_freeze.py:199)
- exact-key 検査で余分な key を拒否する。[s8b_ratified_freeze.py:1439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_ratified_freeze.py:1439)、[s8b_ratified_freeze.py:1727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_ratified_freeze.py:1727)、[s8b_ratified_freeze.py:2157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_ratified_freeze.py:2157)

このままでは生成した floor artifact が ratified freeze を通らず、oracle が binary を certified source として受理できません。

schema validator、ratified consumer、関連テストを scope に追加するか、既存 schema が許す明示的な versioned extension に設計を変更する必要があります。FROZEN_MANIFEST の bytes 自体は変更対象にしてはいけません。

### [must-fix] B3 — S-2(a) の「手順書」側がプランに存在しない

brief は `cmake path` と `cxx version` の未束縛を手順書と成果物の双方に明記するとしています。[brief.md:23](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/brief.md:23)

プランには artifact の `known_unbound_fields` はありますが、更新対象文書の path・節・逐語がありません。[out-plan.md:142](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:142)、[out-plan.md:211](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:211)

runbook は現在も一般的な calibration/toolchain 欠落と R-4 の裁定を記すだけです。[phase3-8b-restart-runbook.md:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/docs/phase3-8b-restart-runbook.md:193)、[phase3-8b-restart-runbook.md:201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/docs/phase3-8b-restart-runbook.md:201)

この記述がないと、report では未束縛でも手順書上の受理条件が不明なため、後続の certified 判定で CXX version/cmake path を検査済みと誤認し得ます。

プランに、例えば R-4 節への次の逐語を追加する必要があります。

> 本 wave の binding は `cmake_realpath` と `cxx_version` を比較しない。これらは calibration receipt に存在しないため、certified 条件および report の受理条件に使用しない。成果物の `known_unbound_fields` は `["cmake_realpath", "cxx_version"]` とする。

### [must-fix] B4 — A-4 の official 側 loader の所有境界が欠けている

P5 は official では attempt leg 必須とします。[out-plan.md:164](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:164)

一方、プランの CLI 変更は attempt directory を pilot path で読む構成です。[out-plan.md:583](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:583)

現在の official は guard で即時拒否され、core に到達しません。[s8b_floor_campaign.py:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:207)、[s8b_floor_campaign.py:3562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:3562)

将来 W-1 が official guard を解除しても、W-1 側で official loader を配線しない限り `attempt_toolchain=None` のまま A-4 が reject します。その場合、official floor build は一件も artifact を生成できず、A-4 は将来解禁後も発火しません。

現行 wave では official 拒否を維持したまま、W-1 と「official permit 後に attempt loader を必ず実行する」契約を明記する必要があります。

### [should] B5 — helper は同一 acceptance set ではない

floor と silo の照合対象は実際には異なります。

- floor 側は CC/CXX path、CC version、cmake version を対象にする。[out-plan.md:90](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:90)
- silo 側は既存どおり CC/CXX path と GCC version 中心で、cmake version、CXX version、重複拒否は追加しない。[out-plan.md:645](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:645)、[out-plan.md:665](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:665)
- 現行 silo もその限定された predicate です。[silo_ladder_rung1.py:3574](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/silo_ladder_rung1.py:3574)

プランの `ToolchainSnapshot` は必須文字列型なので、現状の記述だけで `None` 許容による緩和が起きるとは断定できません。ただし「共通 helper」が全 field を optional にする実装を誘発しないよう、floor contract と silo contract を別 API または明示的な predicate table として固定すべきです。

そうしないと、cmake version 欠落の floor binary が matched report のまま残り、floor の受理集合が静かに広がります。

### [裁定パッケージ候補] B6 — scope 外に残る producer / consumer

| 層 | 根拠 | 本 wave の扱い |
|---|---|---|
| calibration receipt producer | [certify_calibration.sh:600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/tools/pegasus/certify_calibration.sh:600)、[make_acquisition_receipt.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/calibrator/make_acquisition_receipt.py:30)、[cli.py:581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/calibrator/cli.py:581) | calibration reissue/frozen authority のため scope 外。receipt の toolchain field 自体を変えない裁定が必要 |
| silo ladder consumer | [silo_ladder_rung1.py:3574](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/silo_ladder_rung1.py:3574) | A-3 で scope 内 |
| floor-like scoping producer | [pegasus_floor_scoping.py:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/pegasus_floor_scoping.py:82)、[pegasus_floor_scoping.py:210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/pegasus_floor_scoping.py:210) | calibration の records/threads/clocks だけを照合し、toolchain は未束縛。`ELIGIBLE_FOR_COMPARE=False` なので裁定パッケージ候補 |
| between-run noise floor | [between_run_floor.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/between_run_floor.py:163)、[screening_driver.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/screening_driver.py:98) | opt-in screening 用で、certified floor と同一視しない。将来 certified selection に入れるなら別 gate が必要 |
| trace/performance candidate producer | [pipeline.py:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/pipeline.py:748)、[loop.py:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/loop.py:193) | site resolver は使うが receipt toolchain binding はない。候補 binary が calibration toolchain と異なるまま台帳候補になり得るため、all-producer 対応は別裁定 |
| floor binary consumers | [s8b_ratified_freeze.py:1723](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_ratified_freeze.py:1723)、[s8b_oracle_driver.py:833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_oracle_driver.py:833) | toolchain report の schema 変更を受ける。B2 の scope 追加が必要 |
| certified admission | [certified_writer_admission.py:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/certified_writer_admission.py:166)、[certified_writer_admission.py:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/certified_writer_admission.py:177) | current calibration/floor admission は見るが、receipt toolchain binding は見ない。将来の certified acceptance への波及を裁定する必要がある |

### [should] B7 — brief の最も弱い実測主張は M-5

brief は全測定が Pegasus login node の観測だと明記しています。[brief.md:4](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/brief.md:4)

それにもかかわらず M-5 は、login に gcc-13 が無いことから「compute では gcc/g++」という Pegasus 一般の実測のように書かれています。[brief.md:50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/brief.md:50)

compute 側の選択は実測ではなく resolver の分岐です。[buildcache.py:454](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/buildcache.py:454) 実 compute node での realpath/version と registered receipt の一致は未確認です。

この一般化を残すと、compute 側の実 toolchain が異なる場合に floor build が全件 reject されるか、将来 helper を緩めた際に未校正 compiler の binary が受理されます。

### [should] B8 — A-4 の三者照合結果が成果物上では再検証できない

report は receipt-bound 値と `attempt_leg=provided/omitted` を記録するだけで、live 値・attempt の実測値・hash を記録しません。[out-plan.md:44](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:44)、[out-plan.md:144](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:144)

job-result も attempt file の leaf name と state のみです。[out-plan.md:632](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:632)

そのため、A-4 が実際に通ったとしても、後から certified report だけを見て「どの attempt 値が三者一致したか」を再現できません。少なくとも report への値/hash の保存、または durable な attempt artifact への一意参照が必要です。

## [T-748] W-2 確認

M-1 は official の無条件拒否で確認できます。[s8b_floor_campaign.py:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:207)

M-2 は `eligible_for_refreeze` が official のみで、pilot では false になるため確認できます。[s8b_floor_campaign.py:2453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:2453)

M-3 は投入 shell が official 固定であるため確認できます。[floor_campaign.sh:961](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/tools/pegasus/floor_campaign.sh:961)

従って、pilot の直接起動自体は可能でも、それは refreeze 可能な W-2 artifact ではありません。**権威ある W-2 を今日走らせる抜け道はありません。**

## 総括

NO-GO（blocker B1–B4）。  
A-2 は no：実在する発火 artifact path はなく、873225 は official 拒否成果物。  
A-4 は no：official は先に拒否され、pilot は attempt leg を省略するため、現時点では防御効果がない。  
refuted は brief の「pilot compute path は今日 runnable」と、M-5 の Pegasus-wide 実測一般化。  
[T-748] W-2 の停止判定は yes（権威ある W-2 に限る）。