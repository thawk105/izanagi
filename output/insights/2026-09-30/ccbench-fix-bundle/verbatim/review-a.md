## 所見

- **R1 · must-fix · [run_judge.sh](</work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v1/run_judge.sh:25>)**: 検査器の rc を `rc` file に保存した後、最後の `printf` が成功するため、検査器が rc=1 でも job 自体は rc=0 で終わります。**放置時:** D297 不合格を dispatch の成功として読め、正しさ判定を誤ります。**推奨:** 記録後に検査器の rc を返し、rc=0 に加えて report の `result: pass` を合格条件にしてください。

- **R2 · must-fix · [launch_one.py](</work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v1/launch_one.py:75>)**: 登録の実データ正例は F に「既存の `#if TRACE`」があることを要求します。段 4 の erratum E1 はその枝が無いと確認し、末尾に新しい枝を足す形へ訂正しています。現行 script はここで停止するため、Cicada job は完走できません。**放置時:** 登録の生死確認が欠け、Cicada の正しさ成果物も合格になりません。**推奨:** E1 の新規 `#if TRACE` 枝を作り、rc=0・32 文脈を確認してください。

- **R3 · should · [check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/tools/check_trace0_preprocess_identity.py:1171)**: Cicada file の実比較は 32 件なのに、上位 `context_matrix.expected_context_count_per_file` は従来の 16 を表示します。file 別の新項目は 32 を示すため、同一 report 内で件数が食い違います。**放置時:** 一次資料や consumer が上位値を読めば、Cicada の被覆を 16 件と誤記します。**推奨:** 上位項目を path 別の期待数へ変更するか、全 file 共通値ではないことを示す形式へ改めてください。

- **R4 · should · [check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-fix-bundle/tools/check_trace0_preprocess_identity.py:615)**: 16 値組合せの値は `defines` に残りますが、`context` タグと不一致例外には overlay しか出ません。失敗時には該当する 4 macro の組合せを特定できません。**放置時:** どの選定 context で D297 が赤になったか、エラー本文だけでは一次資料に示せません。**推奨:** Cicada の値組合せをタグと不一致例外に含めてください。

- **R5 · should · [run_judge.sh](</work/SFC/tanab/tmp/ccbench-fix-bundle-2026-09-30/scripts-v1/run_judge.sh:22>)**: job 側は合成 A の親と B′の tree・差分 path を確認しますが、A の blob が修正 tip と一致することは再照合しません。`mk_synth.sh` は生成時に照合していますが、job に渡す `synth.bundle` と `synth.oids` の組についてはその主張を検証していません。**放置時:** 差し替わった合成 A に対する D297 pass を、所定の修正 hunk に対する pass と取り違えられます。**推奨:** job 内でも F→各修正 tip の path・blob と A を照合してください。

## 正しいと確認した点

- `_head_defines(..., Genome("cicada", {}), oid)` は `source_rel` が無くても genome の protocol から Cicada の CMake を選びます。供給表による絞り込み、4 macro の 0/1 検査、old/new 供給名集合の一致、16 組合せ×2 overlay、比較 0 件・件数不足・未知 macro の拒否は静的に確認しました。
- 追加テストの負例は期待する層のエラーを指定しています。`overlays[:-1]` の注入は期待数 32 を維持するため、M6 の「実数から期待数を導出」を殺す構成です。ただし M1〜M6 の変異実走と単一理由性は未確認です。
- `mk_synth.sh` の manifest は F→各修正 tip から作られ、A は F に各 patch を適用して作られます。生成時の blob 照合と A→B′の厳密な差分 path 照合もあります。`verify_inputs.sh` は tip・tree・親列・祖先を固定値で照合します。
- 正しさ script は commit witness を `--expected-commits` に渡し、C 行数、巡回、integrity 数値、Cicada の `READ_WTS_MISMATCH` を照合します。Silo には `--require-gate-witness` と certified 判定があり、Cicada の indeterminate は certified と記録していません。Cicada の promotion genome も `compile_commands.json` の `-D` と照合します。
- E1 の末尾への新規 `#if TRACE` 枝は、TRACE=0 で消える変更を 32 文脈で通す正例として妥当です。それ単独で値組合せの感度を証明するものではなく、その役割は反既定値の負例が担います。

## 総括

**R1 と R2 の修正前に計算 job を合格判定へ使えません。** 親の焦点テスト 336 passed は承知していますが、変異と計算 job は未実走です。このレビューも静的点検であり、変異耐性や実データでの合格は確認していません。