## 所見 — 計器

静的検査では、正しさゲートを緩める変更は見つかりませんでした。F/X とも Vmid は版比較の後、lock 読みの前にあり、X の `recheck_abort` は修理で追加した再読不一致の return だけで増え、その経路で保留 hit も破棄します。[F 計器](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/mocc-g2-probe-F.patch:175)、[X 計器](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/mocc-g2-probe-X.patch:175)、[X の計数箇所](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/mocc-g2-probe-X.patch:206)。macro off と `#line`、TRACE との干渉についても、静的検査で成立する攻撃は見つかりませんでした。実前処理・実走による確認は行っていません。

## 所見 — runner と判定

- **should** — F 側の対照は R0 不成立や verifier 判定不能の走も合算します。[moccfix_probe.py](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:329)、[同ファイル](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:348)。放置すると、不完全な F 走だけに G2 や class A が出ても、判定 JSON の `T_F_G2_control_established`／`F_class_a_control_established` が `true` になり得ます。対照の件数と成立判定には、R0 と verifier を通った走だけを使い、不完全な走は別件数で示してください。

arm の OID 照合、patch の順次厳密適用、同一 commit 内の前処理比較、build と verifier の source 指定、反復構成、F/X の先後交替、6 並列、2 job × 14 batch の充足、X 側の R0・G2・class A の成功式、固定費と batch 費の記録について、静的検査で成立する攻撃は見つかりませんでした。[moccfix_probe.py](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:327)、[同ファイル](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:529)、[同ファイル](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:601)。

## 所見 — CI build と D297

- **must-fix** — D297 の `result_name` は両 compiler の失敗理由が期待と違っても、常に「意図した修理差分」です。[run_judge.sh](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/run_judge.sh:121)。放置すると `expected: false` の判定 JSON でも、D297 の記録名が意図した不合格だと誤表示します。両方の `expected_failure` が真のときだけこの名称を付け、それ以外は理由未確定の名称にしてください。
- **should** — `diff-tree.raw` と変更 path は記録しますが、裁定 R5 が求める「F→X の source diff は修理 hunk だけ」という記録がありません。[run_judge.sh](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/run_judge.sh:75)、[同ファイル](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/run_judge.sh:130)。放置すると D297 の成果物だけでは、同じ path 内の余分な変更を確認できません。F→X の source diff を成果物に保存し、修理 hunk との照合結果を記録してください。

CI build の親 OID 固定、依存 pin と offline 供給、`--userns`、D297 の GCC 11/12 と header 用 4 引数、rc=1 の stderr 理由照合について、静的検査で成立する攻撃は見つかりませんでした。[run_ci_build.sh](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/run_ci_build.sh:9)、[run_judge.sh](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/run_judge.sh:88)。

## 総括

退避された 11 ファイルは `tools.sha256` と一致しました。**must-fix 1 件、should 2 件**です。禁止に従い、編集・build・テスト・benchmark・dispatch は行っていません。