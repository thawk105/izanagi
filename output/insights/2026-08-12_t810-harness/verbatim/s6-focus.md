静的再レビューの結論は **NO-GO** です。76 passed は受け入れますが、元所見 16 件は **closed 8 / partial 7 / regressed 1** で、全件 closed ではありません。

特に commit `1892d8b1` の「blocker 9 件と must-fix 7 件を閉じる」は実装と一致しません。

## 所見対応表

| ID | 元所見 | 判定 | 根拠 |
|---|---|---|---|
| revA-1 | receipt と実 attempt file の切断 | **closed** | coordinator/node receipt、measurement、estimate input hash を実ファイルから再構成し、外部 aggregate と exact 比較する。[t810_validator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:863) |
| revA-2 | forbidden roots が caller 任意 | **closed** | production では repo から exact 3 path を内部導出し、symlink target も走査する。[t810_validator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:1321) |
| revA-3 | writable root と attempt/baseline/witness が非束縛 | **partial** | 全 path の descendant 検査は入ったが、単一の共通祖先 root を要求し、裁定前 plan の least-authority な `control/<id>` / `attempts/<id>` capability を表現できない。[t810_validator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:398) [plan.md](/work/1/SFC/tanab/dev-wave-jobs/t810-harness/s2/plan.md:175) |
| revA-4 | pre/post lineage が閉じない | **partial** | lineage fields は増えたが、baseline を pre witness より先に publish する。失敗 baseline 内の全 payload から5状態を試せば witness bytes/hashを再構成でき、失敗 pre を post へ昇格可能。[validate_t810.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/validate_t810.py:143) [t810_validator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:1565) |
| revA-5 | approved Git identity が自己申告 | **partial** | Git identity は approval receipt の digest に束縛されたが、その receipt 自体が unauthenticated な caller 任意ファイル。置換 repo と新 receipt を同時発行できる。[validate_t810.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/validate_t810.py:78) |
| revA-6 | claimed state を分類に使用 | **closed** | classifier は claimed を破棄し、最後に equality finding としてのみ使う。[t810_validator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:799) |
| revA-7 | frozen presence matrix を読まない | **regressed** | 全 field を読むようになったが、`completed-12-plus-preserved-dropped` を completed 12 だけへ縮め、脱落 slot の実在 measurement/execution を拒否する。[t810_validator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:1014) [t810_validator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:1067) |
| revA-8 | calibration symlink / bind alias | **closed** | env symlink target を列挙し、repo 全 directory と writable root の dev/inode も比較する。[t810_validator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:552) |
| revA-9 | witness 時点の snapshot が未封印 | **partial** | root/nlink/common-dir/alternates と witness 後再走査は改善。ただし最後の走査完了後から rc=0 までの変更を止める lease/lock はなく、有限回再走査の TOCTOU は残る。[validate_t810.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/validate_t810.py:171) |
| revB2-1 | approval receipt / constructor bypass | **partial** |通常 constructor は拒否するが、外部 trust root が無いことを artifact 自身が明記している。自己発行 receipt は依然受理される。[t810_preregistration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_preregistration.py:142) [t810_prereg_v1.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/policies/t810_prereg_v1.json:570) |
| revB2-2 | estimator に重複 FSM | **closed** | estimator 側 FSM は削除され、validator へ一本化された。 |
| revB2-3 | golden が runtime estimator を拘束しない | **partial** | loader conformance は追加されたが、実 attempt の `estimate.json` を再計算・出力照合しない。nonceと measurement hash集合だけ合えば任意の `tau_hat` が通る。[t810_validator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:956) |
| revB2-4 | F backend / 等号境界 | **closed** | F値は frozen binary64 hexへ固定され、τ上下限と slope の exact scalar vector が追加された。[t810_estimator_v1.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_estimator_v1.py:22) |
| revB2-5 | 独立 oracle が部分的恒真 | **closed** | 固定 F hex を用いる別式、負分散入力、exact scalar 境界で元の具体的欠陥は閉じた。 |
| revB2-6 | benchmark argv/seed だけでは closure 不足 | **partial** | benchmark argv と permutation は凍結したが、build/qsub argv、raw→log、secondary quantities、downstream consumer は明示的に unfrozen のまま。[t810_preregistration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_preregistration.py:459) |
| revB2-7 | hidden design | **closed** | `design` 全枝を exact literal/schema で再帰閉包している。[t810_preregistration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_preregistration.py:511) |

閉じていないのに「全件 closed」と扱われているのは、少なくとも **revA-3/4/5/7/9、revB2-1/3/6** です。fix 子報告は概ね `partial` と慎重でしたが、commit 題名と fixA の「blocker 2〜4 と must-fix 3件は閉じた」という総括は過大です。

## 焦点確認

- `GIT_OPTIONAL_LOCKS=0` は問題ありません。観測用 subprocess の optional `index.lock` だけを止めています。実 index は `ls-files --stage`、git-dir inventory、tracked bytes、最終再走査で引き続き検出され、別プロセスの mandatory lock や実 index 更新には影響しません。[t810_validator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:329)

- loader conformance に循環はありません。preregistration loader から遅延 import し、estimator 側は preregistration module を import していません。7 matrix + 3 scalar の固定小入力なので、性能上の罠も見当たりません。[t810_preregistration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_preregistration.py:784)

- `try/except` の握り潰しで rc=0 へ倒す箇所は見つかりませんでした。CLI 最外周は `BaseException` も rc=2 にします。[validate_t810.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/validate_t810.py:190)

## 残存・新規所見

### blocker — approval authority が依然自己発行可能

`--approval-receipt` は任意 pathで、署名・issuer・固定 trust root がありません。テスト fixture 自身も artifact bytes から receipt を生成しています。

**成果物影響:** artifact・Git identity・receipt を一緒に差し替えると、N/R/τ*/判定式/repository参照をすべて「承認済み」として変更できる。

### blocker — estimate の値を検証していない

`estimate.json` は hashと入力 measurement 集合だけを検査し、schema、τ値、gate、結論 codeを `evaluate_t810()` で再計算しません。正例 fixture も任意の `"tau_hat": "0.001"` だけで通っています。[test_t810_validator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_validator.py:205)

**成果物影響:** 同じ measurement bytes のまま `τ̂`・区間・結論 code・材料レポートを任意値へ変更できる。

### blocker — rc=2 の pre baseline を偽 witness で再利用できる

baseline は witness より先に残り、witness は非秘密の決定的 JSON + SHA-256 です。成功した同一 invocation の証明にはなっていません。

**成果物影響:** 投入前 gate が完了していない attempt を post 合格へ昇格し、proof chain の pre 成功参照を偽造できる。

### must-fix — 正当な `terminal_reduced` を過剰拒否

凍結前 plan は「脱落 slot は実在分を保存」としているのに、実装は非 completed execution を常に0件、measurement集合を completed 12だけにします。[plan.md](/work/1/SFC/tanab/dev-wave-jobs/t810-harness/s2/plan.md:491)

**成果物影響:** 12完了 + 1途中脱落という正規形を certified 集合から除外し、τレポートを「結果なし」へ変える。

### must-fix — `reached_slots=[]` を誤って不完全 receipt にする

`pre_release_invalid` は reached slots exact であり、ready timeout が0到達でも正規に表現できるはずですが、実装は `not reached` を一律拒否します。[t810_validator.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:889)

**成果物影響:** retry可能な zero-reached attempt を非 retry の不完全状態へ変え、attempt台帳と次 attempt の受理可否を変える。

### must-fix — writable capability の正規形と実装が不一致

正本化前 plan は `control/<attempt-id>` または `attempts/<attempt-id>` 自体を capability root としますが、現CLIは両者の共通祖先を要求し、各 path を strict descendant にします。

**成果物影響:** 正規の least-authority rootを拒否するか、広い祖先 capabilityを要求して別 attempt/control 配下への誤配置余地を増やす。

## land 前の最小修正集合

1. Approval receipt と Git identity を、caller が生成できない固定 trust rootへ束縛する。
2. 実 measurement から estimator 入力を構築し、`estimate.json` の全出力を再計算して exact照合する。
3. pre witness の成功確定後にだけ baselineをpublishし、最終snapshotを排他的な静穏leaseの内側で封印する。
4. `terminal_reduced` の途中脱落、zero-reached `pre_release_invalid`、control/attempt の2 capability rootを正例として凍結し直す。

## 総括

**NO-GO。**

最も危険な残存点は、**approval receipt に固定 trust rootがなく、凍結 artifactとGit identityをcallerがまとめて自己承認できること**です。これが残る限り、個々のhash chainやgoldenを強化しても、proof chain全体のauthorityが恒真化します。