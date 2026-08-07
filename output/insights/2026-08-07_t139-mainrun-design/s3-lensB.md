NO-GO

## 総括

本走は投入不可です。段 2 自身の「現時点 NO-GO」は妥当ですが、解除手順にも未解決 blocker があります。

特に、request `892042` は D162(10)(i) を満たす一方、構造化 `env_tag` と実環境 attestation がなく (ii) は未成立、consumer もなく (iii) も未成立です。現案の vertical slice は「発火条件成立後の実装」ではなく、D162 を人間が明示的に supersede する変更です。

また、現 PBS の worst-case は `3298/3300` 秒で余白 2 秒です。6 rep と washout の最小待機 1410 秒を加えた現行 cap 構造は約 4708 秒となり、1 時間 allocation に収まりません。

### [blocker] 1. D162 の発火条件は (i) だけ成立している

[判定] request `892042` は 3 arm、実走前 commit、checkout、pin を持つため (i) と (ii) の一部は成立します。しかし raw に `env_tag` と実環境 attestation がなく、(ii) は連言として false です。(iii) の consumer も 0 件です。「positive probe があるから9層を原子的に許可」は発火条件の充足ではなく、D162(10) の明示的変更を要します。

[根拠: docs/decisions.md:8049-8055; output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/preregistration-witness.tsv:1-10; output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/throughput.tsv:1-31; tools/pegasus/probes/t139_positive_control_probe.pbs:65-71; output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/preregistration.md:50,107-108; docs/pegasus-runbook.md:628-635; output/insights/2026-08-05_t337-qualification-authority/mechanization-design.md:3-7,24-28; /work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:374-417]

[成果物影響: attestation 不在の measurement を発火根拠にすると、環境同一性を証明しない receipt から qualification 経路を開き、正例の受理集合を無裁定で拡大する。さらに plan の表は9層だが裁定項目2は producer・validator・最初の consumer・検査しか列挙せず、欠けた層を実装済みと数える余地がある。]

[最小の直し方] 次のどちらかを裁定項目として明記してください。

1. 構造化 `env_tag`、checkout、pin、正式な env attestation を持つ新しい3-arm trigger probeを先に取得し、実在 consumer hook も別途成立させる。
2. D162(10) を人間が明示 supersedeし、既存 consumer 不在から列挙した全層を同時実装できる例外を新 D で定める。

後者なら「D162 を満たした」とは記録せず、「D162 の条件を変更した」と記録する必要があります。

### [blocker] 2. `declared_use_class` はまだ確定名ではない

[判定] T-479 は `artifact_role` を使わないことだけを裁定し、`declared_use_class` は第一候補です。plan は新 D と D75 一意性検査なしに raw schema の確定 field として扱っています。

[根拠: docs/archive/worklog-phase3-0805-199.md:3-8,18-21; /work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:62-74]

[成果物影響: producer と consumer が異なる field 名を実装すると、正当な receipt が全拒否されるか、RF だけ閉表外の別名を許す例外が生じる。]

[最小の直し方] 実装 wave で repo 全体の一意性を再検査し、T-318/T-337 の literal を supersedeする新 D と同じ変更単位で field 名を確定してください。

### [blocker] 3. D19／roadmap の原子性は未履行で、段階0だけでは遡及的に直らない

[判定] paired 設計は worklog (139) で実質採用済みですが、roadmap は今も「同一 session で測らない」としています。段階0の方向は正しいものの、過去の裁定と同じ変更単位には戻せません。ユーザーによる paired 例外の再確認と、roadmap・D19限定の同時記録が必要です。

[根拠: docs/archive/worklog-phase3-0803-138-139.md:15-16,347-357; docs/decisions.md:6506-6511; docs/roadmap.md:219-226; docs/roadmap-history/README.md:20-27; /work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:36-45]

[成果物影響: 同じ paired raw に RF 専用同時領域と既存 unpaired 3% floor の二つの解釈が残り、正例の成立・不成立が consumer ごとに反転しうる。roadmap:225-226 には D134 が反証済みの「max 手続き」「high-abort ほど大きい」も残る。]

[最小の直し方] 本走・実装・preregistration より前に、ユーザーが paired 例外を再確認し、その同じ commit で以下を行ってください。

- roadmap §3.6 の限定例外と反証済み二文の訂正
- D19 の適用前提を限定する新 D／spool fragment
- 「この commit 未成立なら次段へ進まない」という land gate

協議改訂なので history 版上げは不要です。

### [blocker] 4. `E[D−κS]>0` は Q2 の一意な帰結ではない

[判定] これは `E[D]/E[S] > κ` を選ぶ実装で、Q2 の「stock 比の相対量」から許される一案ではありますが、`E[D/S] > κ` とは非同値です。Q2 はこの二択を裁定していません。

[根拠: output/insights/2026-08-03_t338-rf-statistical-design/package.md:77-88; docs/archive/worklog-phase3-0803-138-139.md:11-14; /work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:109-115,297-312]

[成果物影響: 例えば `(S,D)=(100,10),(1000,50)`、`κ=0.06` では、`E[D/S]=7.5%` は pass ですが、`E[D−κS]=-3` は fail です。同じ raw の `P_w` と最終受理が反転します。]

[最小の直し方] Q2 追補として次を明示裁定してください。Q1 の総量型との整合からは前者を推奨できますが、既裁定扱いはできません。

- ratio-of-means: `E[D]/E[S] > κ`
- mean-of-ratios: `E[D/S] > κ`

### [blocker] 5. `d_plan` が裁定済み d≈1.0 を結果依存で引き下げる

[判定] plan は「d=1を維持」と述べながら、pilot の下側効果が0.5なら `d_plan=0.5` として、より小さい効果を拾うため J を増やします。これは worklog (142) が「d=0.5 の約42 clusterを最初から払わない」と裁定した方向と一致しません。

[根拠: docs/archive/worklog-phase3-0803-142-143.md:3-15; /work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:20,117-143,145-157]

[成果物影響: J と費用が増え、d≈1では判定不能だった小効果が有意になり、正例として通る実験結果集合が広がる。]

[最小の直し方] planning alternative は d=1.0 に固定し、pilot は共分散・schedule・infra率の推定に使ってください。保守的下限が1を下回る場合は `design_not_feasible` とするか、d<1を許す新しい費用裁定へ返してください。

### [blocker] 6. 親 brief の P3 は裁定違反のまま凍結されている

[判定] P3 は `G>0` を落としており誤りです。plan の棄却結論は正しいですが、「D162 が三条件を要求する」という引用は誤りで、正本は Q9／worklog (142) です。plan 本体では pilot成分・IUT・負例に G が復元されており、追加の書き落としは確認できませんでした。

[根拠: output/insights/2026-08-07_t139-mainrun-design/brief.md:44-48; docs/archive/worklog-phase3-0803-142-143.md:16-21; output/insights/2026-08-03_t338-rf-statistical-design/package.md:257-268; /work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:18,86-90,184-227,287-295; docs/decisions.md:8018-8025]

[成果物影響: P3 の二条件だけなら `N>0` かつ分母十分でも `X≥stock` の候補が通り、`RF>1` を正例へ混入できる。plan 自身の W2 負例がその反例になっている。]

[最小の直し方] 凍結 brief は書き換えず、段4裁定で P3 を明示 refuted とし、primary を workload ごとの `D>δ_D ∧ N>0 ∧ G>0` に固定してください。根拠の参照先も Q9／worklog (142) へ直します。

### [blocker] 7. `rf_positive_artifact` に恒真相当の自己根付き gate と欠落項がある

[判定] 数学的に常に true な連言項はありませんが、次の三つは入力集合を producer 自身が選べるため、意図した保証に対して恒真相当です。また環境 attestation・accounting・liveness の semantic validation が受理述語にありません。

| 項 | false になる入力 | 判定 |
|---|---|---|
| `raw_schema_valid` | 禁止された `eligibility_status` を追加 | 到達可能 |
| `exact_J_complete` | prereg J=11 に対し10 cluster | 到達可能。ただし attempt完全性に依存 |
| `all_attempts_bijective` | registry にある request の raw 欠落 | 到達可能だが、失敗requestをregistryとrawの両方から落とすと通る |
| `no_correctness_anomaly` | verifier anomaly を持つ raw | 到達可能だが、plan の `correctness` fieldだけでは自己申告化する |
| `schedule_and_washout_valid` | order不一致、gap不足 | 到達可能。timestampの証拠根が未定 |
| `pairing_valid` | arm identity欠落・不一致 | 到達可能で、validator導出なら妥当 |
| `candidate_series_alpha_valid` | cap超過・累積α超過 | 到達可能だが、新しい自己申告 `parent_family_id` でresetできる |
| `P_W1/P_W2` | N、D−κS、G の任意のLCB≤0 | 到達可能 |
| `fieller_ok_*` | 非有界、不連結、lower≤0、upper≥1 | 到達可能 |

[根拠: /work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:62-74,190-227; docs/decisions.md:5504-5509,8014-8025; output/insights/2026-08-05_t337-qualification-authority/mechanization-design.md:74-86; docs/decisions.md:6898-6913; docs/pegasus-runbook.md:45-48]

[成果物影響: 失敗submissionのfile-drawer、correctness anomalyの自己申告消去、成功後のfamily ID再発行がすべて通り、誤った certified artifact を発行できる。attestation fieldが「存在する」だけでも schema は通るため、共有ノード汚染も拒否されない。]

[最小の直し方]

- D141 の login controller を唯一の submitter とし、qsub response を結果前に外部根付き台帳へ記録する。
- family registry head・候補上限・alpha台帳を最初のtrial前のcanonical rootへ束縛する。
- correctness booleanを信用せず、raw verifier evidenceから再実行する。
- `environment_attestation_valid`、`allocation_accounting_valid`、`liveness_valid`、単独性／競合検査を明示連言にする。
- 「失敗requestをregistry/raw双方から削除」「新familyでreset」「anomalyをcleanと申告」の変異を必須killにする。

### [blocker] 8. `weak_denominator_not_certifiable` が閉表に結線されていない

[判定] 固定状態名を宣言しただけで遷移述語がなく、表の `unbounded_not_certifiable`／`disjoint_not_certifiable` と競合します。したがって exact-one の状態閉表になっていません。

各 shape 自体には反例入力があります。

- stableな正負の比 → boundedの below／partial／stock-exceeding
- 境界を跨ぐbounded集合 → `boundary_ambiguous`
- 分母平均が弱い入力 → unbounded／disjoint
- `D_j≡0, N_j≡1` → `A=0,B=0,C=1` で Fieller集合は empty

最後の empty は有効な raw からも生じるので、一律 `invalid_confidence_set` とするのも誤分類です。

[根拠: docs/decisions.md:8031-8033; /work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:243-271]

[成果物影響: 受理自体は false 側でも、材料レポートの状態値・理由・proof chain が `weak_denominator_not_certifiable` にならず、consumerのexact state dispatchが不一致になる。]

[最小の直し方] `fieller_shape` と `qualification_status` を別軸にしてください。分母の信頼集合が0を除外できない条件を明示し、そのとき status を必ず `weak_denominator_not_certifiable` とする一方、shape は unbounded／disjoint／empty として併記します。empty-valid と representation-invalid も分離してください。

### [blocker] 9. 6 rep＋washout は現 allocation予算に収まらない

[判定] plan は危険を認識していますが、実行可能な cap 再配分を示していません。現 PBS の静的総和は `3298/3300` 秒で、plan の `3290` は誤りです。

6 repでは36 arm runになります。30秒 arm wait と60秒 block間waitを重複分は最大値として数えても、最小待機は

`36×30 + 11×(60−30) = 1410秒`

です。性能runも6本増えるので worst-case capは90秒増えます。現 driver内訳2310秒に加えると3810秒、PBS外側込みでは約4708秒です。

[根拠: tools/pegasus/probes/t139_positive_control_probe.pbs:53-62,332-338; tools/pegasus/probes/t139_positive_control_probe.sh:370-373,486-512; /work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:354-362]

[成果物影響: performance開始後にdeadlineへ達すると `post_performance_failure` となり、Q8によりreserve置換不可です。`exact_J_complete=false` となりpilot covarianceもmain artifactも成立しません。開始前に落ちても同じ決定的予算不足でreserveが連続失敗します。]

[最小の直し方] 各 `deadline_run`、washout、非timeout処理を含む executable cap ledgerを作り、十分な余白込みで内部deadline以下にしてください。無理なら walltime／内部deadlineを延ばして費用表を再計算するか、hash束縛済みbinaryの事前生成等でallocation内buildを削減します。数値確定前のpilot投入も不可です。

### [blocker] 10. point単価の測定方法が成立せず、24 allocationは承認不可

[判定] `rbudgetcheck` の group差分へ他requestの消費が混ざるなら、pilot 1〜2本を走らせても request単価は得られません。scheduler accountingはrequest identity・elapsedの証拠にはなりますが、repo内一次資料にはpoint換算式がありません。D141も換算を推測しないと裁定済みです。

[根拠: /work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:377-407,434-435; docs/decisions.md:6898-6913; docs/pegasus-runbook.md:270-275,777-789]

[成果物影響: 最大費用が不明のまま24本を承認すると、Q5の費用裁定を迂回する。途中でpoint上限へ達すればJ未達となり、artifactは恒常的に判定不能になる。]

[最小の直し方] 正しい測定は、D141 controllerが target request直前／会計反映後の `rbudgetcheck` を取り、同じ窓に他のSFC chargeが無いことを証明するか、管理者のrequest別point台帳／公式換算式を得ることです。分離不能なら正確な単価は測れません。その場合はユーザーが総point上限を先に裁定し、1本ずつ保守的上限を更新する以外にありません。費用未知の24本一括承認は NO-GO です。

### [blocker] 11. queue待ち中のHEAD進行に対する成功経路がない

[判定] 現 probe は期待commitとjob開始時のlive HEADが一致しなければ終了します。これは別bytes実行を防ぎますが、旧commitのjobが成功する保証ではありません。pilotとmainは別prereg commitになるため、各batchのHEAD寿命を明示しない24本設計は実行不能です。

[根拠: tools/pegasus/probes/t139_positive_control_probe.pbs:65-71; docs/decisions.md:9122-9125; /work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:76-95,364-372,389-407]

[成果物影響: queue中にHEADが進むと複数allocationが一斉にpre-performance failureとなり、pointとreserveを失って `exact_J_complete=false` になる。逆にHEAD一致検査を緩めれば、pilot／mainで別bytesを実行する穴が再び開く。]

[最小の直し方] pilot用とmain用にそれぞれ専用のdetached・immutable checkoutを作り、当該batch全requestの終端までHEADを進めないでください。controllerが各qsubへ期待commit/hashを束縛し、queue滞留期限と期限超過時の閉じた失敗分類も事前登録します。aggregate 24 allocation-hoursをcalendar wall-clockと呼ばないことも必要です。

### [nit] 12. P1〜P6棄却とarm中央値の再判定

[判定]

- P1: external pilot・非poolは防御側の選択として妥当。ただしplanの反例はnaive poolingだけを反証し、全internal-pilot手法の不可能性までは証明しません。
- P2: 現5順列を「exact balance」と呼ばない訂正は正しいです。5 rep自体はQ6で禁止されておらず、planが示すcluster横断counterbalanceなら候補に残せます。
- P3: 棄却は正しいですが、根拠はD162ではなくQ9／worklog (142)です。
- P4: confirmatory thresholdとして棄却する防御判断は妥当です。planのいうとおりD126(4)への文字どおりの違反ではありません。
- P5: J=11の無条件固定を棄却するのは妥当ですが、d<1への引下げは blocker 5です。
- P6: producerだけ先行の棄却は正しいです。代案は blocker 1のD162手続きを要します。
- arm中央値: Q1は `m=arm代表値` までしか固定していないので、中央値は `E[N]/E[D]` と形式矛盾しません。ただし未裁定であり、平均とはRF・Fieller・Jが変わります。

[根拠: output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/preregistration.md:53-62,124-130; output/insights/2026-08-03_t338-rf-statistical-design/package.md:58-64; docs/archive/worklog-phase3-0803-138-139.md:355-372; /work/1/SFC/tanab/dev-wave-jobs/t139-mainrun-design/s2-plan.md:12-32,316-352,411-441]

[成果物影響: P2はallocation数とcarry-over分散、P4は受理閾値、arm代表値はRF点値・Fieller集合・必要Jを変える。]

[最小の直し方] P2は「現5順列の同一反復を棄却、5 rep一般は未棄却」と書き分けてください。arm代表値はユーザー裁定9が確定するまで記号 `m` のまま保持し、preregistrationで固定します。

## 未検証の懸念

gen_S の `104 request / 31 running` という一時点だけから、pilot→J決定→mainのcalendar完了時刻は推定できません。履歴service rate・queue優先度・SFC内の同時chargeが提示資料にないため、具体的な日数見積りは未検証です。

静的検査のみで、pytest・build・Pegasus実走は行っていません。