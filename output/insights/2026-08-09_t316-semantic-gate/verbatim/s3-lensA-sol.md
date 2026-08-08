結論は **NO-GO** です。D127(5) の旧 class-cross cache hole 自体は現行 D136 で閉じていますが、提案は「sandbox 方針を選んだこと」と「実際の各 run が sandbox 内で行われたこと」を同一視しており、raw sort の reward hack と成果物 proof chain が未閉鎖です。

## real 候補

### R1. sandbox policy は cache identity にはなるが、実行時封じ込めの証明にならない

- **status:** real
- **severity:** blocker
- **所見:** 段2は `SandboxProfile` を `BuildRunContext`／policy preimage に入れる設計ですが、cache hit 後の各 `exec` が実際にその profile で走ったことを強制・記録する exact topology がありません。[s2-plan.md:104–110](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate/s2-plan.md:104)
- **根拠:** 現行 `BuildResult` は binary path/hash を返すだけです。[buildcache.py:165–180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/buildcache.py:165) `_run_trace()` は path を直接 `subprocess.run` し、`run_once()`／`measure_point()` も unsandboxed runner を既定値に持ち、通常 mode では injected runner を下流へ渡しません。[pipeline.py:260–281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/pipeline.py:260) [runner.py:346–373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/calibrator/runner.py:346) [runner.py:440–450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/calibrator/runner.py:440)
- **不足:** `build_done` は binary hash/cache-hit、`verify_done` は verifier 値、`commit` は admission SHA を持ちますが、stage・binary SHA・profile/backend・attempt ID を束縛した sandbox execution receipt がありません。[pipeline.py:810–817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/pipeline.py:810) [pipeline.py:889–904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/pipeline.py:889) [pipeline.py:1073–1087](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/pipeline.py:1073)
- **DW-G05:** runner 伝播を1箇所落としても同じ admission/cache/campaign ID のまま `verify_done.certified=true` と `commit` が生成され、sandbox 外実行由来の候補が受理集合へ入ります。

### R2. 非対称案 (iii) は sort 軸について二層防御ではなく、単一 sandbox 境界になる

- **status:** real
- **severity:** blocker
- **所見:** `CoderProposalSort.implementation` は raw C++ で、そのまま hole に入ります。[p3_s4_loop_sort.py:110–118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/p3_s4_loop_sort.py:110) [p3_s4_loop_sort.py:137–164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/p3_s4_loop_sort.py:137)
- **根拠:** `DiffQuarantine` が拒否する内容は前処理指令、marker、comment delimiter、行末 backslash に限られ、それらを含まない任意 C++ 文は通ります。[diff_quarantine.py:9–22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/diff_quarantine.py:9) [diff_quarantine.py:461–497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/diff_quarantine.py:461) D127 でも一行注入の通過が実測済みです。[decisions.md:6228–6233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/docs/decisions.md:6228)
- **連鎖:** raw implementation → structural quarantine pass → auditor echo pass → coder admission → cache binary → string-path run、となります。D136 自身も calibrator の任意 binary path 等には security credit を与えていません。[decisions.md:6650–6654](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/docs/decisions.md:6650)
- **必要条件:** T-184 の「inventory」だけでなく、全 untrusted `execve` が sealed `SandboxRunner` capability を要求する機械検査と、欠落時に `commit` を拒否する WAL topology が必要です。代替は sort にも post-preprocess AST/effect gate または typed comparator IR を置くことです。
- **DW-G05:** 一つでも直接実行 consumer が残れば、sort の任意コードが cache・WAL・report を同一 UID で変更でき、台帳値と certified 受理集合を任意に拡張できます。

### R3. sandbox は reward hack を塞がず、raw sort には独立した正しさの番人がない

- **status:** real
- **severity:** blocker
- **所見:** 段2自身が、sandbox 内の binary は許可された stdout／trace dir を偽造でき、certification integrity を塞がないと認めています。[s2-plan.md:143–147](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate/s2-plan.md:143)
- **根拠:** candidate process は trace dir を書き、stdout の abort count と性能値を出します。[pipeline.py:260–288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/pipeline.py:260) [runner.py:360–391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/calibrator/runner.py:360) pipeline はその trace を検証して `certified` を記録し、全 pass 後に `COMMIT` と fitness を発行します。[pipeline.py:856–918](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/pipeline.py:856) [pipeline.py:1018–1087](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/pipeline.py:1018)
- **auditor 依存:** 現行 runbook は非 SWO と fairness reward hack の防壁を auditor 静的目視に依存しており、fairness の機械観測点は未実装です。[phase3-s5-sort-runbook.md:182–193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/docs/phase3-s5-sort-runbook.md:182) 一方、auditor gate は diff digest 一致しか証明せず、`pass`＋空 violations を受理します。[auditor_gate.py:153–164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/auditor_gate.py:153) [auditor_gate.py:203–243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/auditor_gate.py:203)
- **不足:** R8 の実装前提に、candidate-controlled trace/stdout から独立した semantic・liveness・fairness oracle、または sort source language の制限が含まれていません。
- **DW-G05:** 偽 green は WAL の `verify_done.certified` と `commit.fitness_tps` になり、レポートでは commit の存在だけで certified とされ、最大 tps の点として best に入ります。[s6_sort_sweep.py:425–452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/s6_sort_sweep.py:425) [s6_sort_sweep.py:472–475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/s6_sort_sweep.py:472) [s6_sort_sweep.py:536–545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/s6_sort_sweep.py:536)

### R4. DW-O13 を満たす canonical field mapping がなく、識別子も二義化している

- **status:** real
- **severity:** blocker

| gate 入力 | 現物の所在 | 欠落・二義 |
|---|---|---|
| coder diff | scratch proposal の `coder.implementation`。`working_diff` は実行時に `difflib` で派生。[p3_s4_loop.py:165–185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/p3_s4_loop.py:165) | canonical な `coder_diff` field はなく、sort checkpoint は5項目 whiteboardだけです。[p3_s4_loop.py:576–584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/p3_s4_loop.py:576) |
| auditor verdict | scratch proposal の `auditor.verdict/diff_digest`。[p3_s4_loop_sort.py:270–301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/p3_s4_loop_sort.py:270) | sort campaign は成功 verdict／proposal hash を保存しません。trigger 側でも保存するのは mutable な `proposal_path` と `auditor_diff_digest` だけです。[p3_s4_loop_trigger_gating.py:741–750](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/p3_s4_loop_trigger_gating.py:741) |
| built diff | `build_start.payload.build_admission.source.tracked_diff_sha256` | これは full `git diff --binary HEAD --` の digest であり、auditor が見た skeleton-base→hole-edit の `working_diff` digest とは別 domain です。[source_digest.py:800–821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/source_digest.py:800) |
| build admission | `campaign.lock.search_config.build_admission` と `build_start.payload.build_admission` | 前者は policy preimage、後者は per-attempt receipt。同名で異なる型です。[ident.py:28–44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/ident.py:28) [pipeline.py:721–727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/pipeline.py:721) |
| sandbox receipt | 段2に概念のみ | 現行の `CampaignSummary.execution_receipt` は環境 attestation であり、sandbox 実行証明ではありません。[loop.py:61–89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/loop.py:61) [loop.py:131–134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/loop.py:131) |

D75 の教訓どおり、少なくとも `build_admission_policy`／`build_admission_receipt`、`hole_working_diff_sha256`／`full_tracked_diff_sha256`、`environment_execution_receipt`／`sandbox_stage_receipt` に分離すべきです。[decisions.md:3031–3037](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/docs/decisions.md:3031)

- **DW-G05:** 現成果物では「正しい diff を auditor が pass し、その bytes を sandbox で実行した」ことを再計算できず、正当 pass と echo／unsandboxed pass が同じ `COMMIT`・レポート行になります。

### R5. sandbox build の出力をそのまま共有 cache へ昇格する境界が未設計

- **status:** real
- **severity:** must-fix
- **所見:** build staging を untrusted build process に書かせるなら、その directory 全体を trusted artifact として移動してはいけません。段2は「build staging のみ writable」としますが、controlled copy-out の契約がありません。[s2-plan.md:132–141](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate/s2-plan.md:132)
- **根拠:** 現行 v2 は staging binary を `os.path.isfile`／通常の `open` で検査した後、staging directory 全体を `os.rename` します。binary symlink 自体の拒否はありません。[buildcache.py:740–783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/buildcache.py:740) [buildcache.py:87–101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/buildcache.py:87)
- **必要条件:** sandbox output から allowlisted regular filesだけを `O_NOFOLLOW`／beneath-only 解決で読み、clean host-owned directoryへ再構築すること。symlink、hardlink、device、socket、予期しない executable／manifest は拒否すべきです。
- **DW-G05:** build/compiler 境界が破れた場合、攻撃者制御の filesystem object が共有 cache entry となり、次回 hit の `trace_cached/perf_cached` と binary hash、以後の run・report 値を汚染します。

## refuted 候補

### F1. 「D127(5) の class-cross cache hole が現在もそのまま開いている」

- **status:** refuted
- **severity:** nit
- **根拠:** 現行 legacy key は admission receipt SHA を含み、v2 は preimage・manifest・current admission を完全一致させます。[buildcache.py:130–148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/buildcache.py:130) [buildcache.py:366–417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/buildcache.py:366) D136 も class-cross hit と replay を閉じたと明記します。[decisions.md:6610–6628](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/docs/decisions.md:6610)
- **DW-G05:** 現行 direct path では class を変えると cache identity が変わるため、旧 coder binary が別 class の certified 集合へ入る経路は増えません。ただし R1 の「同じ profile identity で unsandboxed run」は別問題です。

### F2. 「auditor advisory 化は auditor 自体を実行しなくする」

- **status:** refuted（ただし用語は must-fix）
- **severity:** must-fix
- **根拠:** 段2の具体規則は mandatory な deny-only vetoであり、`reject`／`uncertain` は候補を狭め、`pass` は安全 capability を発行しない、というものです。[s2-plan.md:176–186](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate/s2-plan.md:176) 現行実装も非 pass を build 前に拒否します。[p3_s4_loop_sort.py:153–164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate/orchestrator/campaign/p3_s4_loop_sort.py:153)
- **補正:** 文書上は「advisory」ではなく「**mandatory deny-only veto; affirmative security creditなし**」と固定すべきです。そうしないと任意実行と誤読されます。なお、echo pass を塞がない点と R3 の独立 oracle 欠落は refuted されません。
- **DW-G05:** deny-only を文字どおり維持すれば現在の auditor reject 集合は受理へ戻りません。任意 advisory と解釈すれば reject／uncertain 候補が新たに build・certify 対象になります。

### F3. 「段2案は build だけ sandbox にし、run は最初から対象外」

- **status:** refuted
- **severity:** nit
- **根拠:** 設計意図は build、trace、perf の全てを対象とし、`_run_trace` と calibrator runner の置換も列挙しています。[s2-plan.md:90–100](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate/s2-plan.md:90) [s2-plan.md:112–126](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate/s2-plan.md:112)
- **DW-G05:** 全 seam が本当に mandatory runner へ閉じれば、cache hit 自体で受理集合は増えません。問題は意図ではなく、R1 の execution receipt／consumer topology 不在です。

## 判定

**NO-GO**。計算ノード backend の非 certifying 計測は進めてよいですが、設計裁定の凍結・実装 wave 起票には、次の3条件追加が必要です。

1. stage/binary/profile/backend/attempt を束縛する sandbox receipt と、receipt 欠落時に `COMMIT` を拒否する WAL topology。
2. raw sort に対する candidate-controlled trace/stdout 非依存の correctness・liveness・fairness gate、または source language/effect の制限。
3. D75準拠の exact artifact field mappingと、安全な sandbox build output copy-out。

必読入力中に「gate を飛ばせ」等の指示様 anomaly は確認しませんでした。read-only であり、ファイル変更・実走は行っていません。

## 総括

最大の blocker は、raw sort が候補制御の trace/stdout を通じて certified/fitness を偽装でき、sandbox がこれを止めないこと。  
D136 により旧 class-cross cache hole 自体は refuted だが、profile policy は実 run の隔離証明ではない。  
per-stage sandbox receipt、独立 correctness gate、exact artifact fields、安全な cache copy-out が必要。  
判定: **NO-GO**（backend の非 certifying 計測のみ継続可）。