## 逐条照合の結果

1. `refuted` — arm 表の不一致はない。3 workload の `ycsb_rratio`、variant/baseline 名、role、contrast、protocol、`BACK_OFF`、`BACKOFF_FIXED`、`NO_WAIT_LOCKING_IN_VALIDATION`、`NO_WAIT_OF_TICTOC`、`WAL` はすべて `workloads[*].arms[*]` と一致した。[本文:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:18) [policy:188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:188)

2. `refuted` — 規模の不一致はない。`scale` の `expected_verify_configs=["legacy"]`、`extime_s=3`、`records=1000000`、`threads=48`、`ycsb_max_ope="10"`、`ycsb_rmw="0"`、`ycsb_zipf_skew="0.9"` がすべて本文に投影されている。[本文:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:30) [policy:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:109)

3. `real` — 配置の数値、3 root seed、`pilot_pairs_per_workload=60`、`pilot_pair_blocks={6,5,12,6}` は一致するが、`pairing.schedule_receipt_schema` が本文に無く、`effective_root_seed_preimage` は逐語不一致で、さらに arm block と pair block が混同されている。詳細は「不一致」に記す。[本文:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:36) [policy:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:56)

4. `refuted` — 観測 8 field は集合として完全一致した。本文、`_ROW_KEYS`、`_BALANCED_RECEIPT_REP_KEYS` はいずれも `arm, block, block_position, ended_at_ns, group, pair_index, started_at_ns, tps` の過不足なしである。[本文:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:68) [sizing:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/tools/size_paper_story_a1_balanced.py:74) [driver:1581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:1581)

5. `refuted` — sizing 側の物理順検査は本文どおりである。12 pair block の lead を 6/6 と数え、各 group の隣接 2 pair block が `{variant-first, baseline-first}` であることを拒否条件付きで検査する。[本文:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:75) [sizing:473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/tools/size_paper_story_a1_balanced.py:473)

6. `refuted` — sigma の作り方は policy と実装に一致する。60 差、連続 5 対の12平均、標本 SD、`alpha_c=1/20`、df=59/11、`sqrt(5)`、両上側係数、`max`、baseline 60点の算術平均と有限正条件を個別に確認した。[本文:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:100) [policy:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:121) [sizing:488](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/tools/size_paper_story_a1_balanced.py:488)

7. `refuted` — `k=t(1-(1/120)/2,n-1)`、`h`、`L/U`、`B=3/100×baseline mean`、4分類、invalid 条件は `_count_outcomes` と一致する。実装は improvement、regression、bounded、fallback の順に排他的 mask を作る。valid では `h>=0`、かつ baseline が正なので `L>B` と `U<-B` は同時成立せず、本文の順位と同じ結果になる。[本文:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:121) [sizing:560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/tools/size_paper_story_a1_balanced.py:560)

8. `refuted` — 3条件の delta と成功方向は一致する。policy の `positive-six-percent` / `negative-six-percent` が実装の `positive-two-floor` / `negative-two-floor` に対応し、それぞれ improvement / regression を成功とする別名関係も正しい。[本文:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:141) [policy:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:131) [sizing:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/tools/size_paper_story_a1_balanced.py:54)

9. `real` — `n_grid`、昇順探索、片側 Clopper–Pearson、`1/(60*j*(j+1))`、次候補への進行、`no-passing-n` は一致するが、本文の「全試行・全条件の合計 alpha ≤ 1/20」は workload scope を欠き、実装全体とは一致しない。詳細は「不一致」に記す。[本文:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:154) [sizing:630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/tools/size_paper_story_a1_balanced.py:630)

10. `refuted` — sizing root seed の原像は実装と1文字単位で一致し、実際の SHA-256 も記載 digest と一致した。子 seed 文法も一致し、`attempt` は certification のみ、かつ search-pass 候補ごとに1から増える。headline policy にも `search_trials=20000` と `certification_trials=100000` が実在する。[本文:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:172) [sizing:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/tools/size_paper_story_a1_balanced.py:33) [headline:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_headline.v1.json:156)

11. `real` — `quality` の全6 field、CCBench pin、5 boundary は一致する。一方、`execution` は全 field の投影になっておらず、複数 field が本文から欠落する。詳細は「不一致」に記す。[本文:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:185) [policy:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:22) [policy:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:91)

12. `refuted` — 16 の無効規則は policy と本文で、文字列・大文字小文字・句読点・順番を含め完全一致した。driver の `V3_INVALID_RULES` とも完全一致し、1文字の差もない。[本文:209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:209) [policy:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:38)

13. `refuted` — `rerun` の4理由は順番も一致し、閉じた列挙と performance output による再走禁止も一致する。[本文:230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:230) [policy:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:99)

14. `refuted` — 感度分析は正しい。`1-(1-0.001)^120 = 0.11313281241393625`、すなわち `11.313281...%` なので「約11.3%」と一致する。[本文:268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:268)

15. `refuted` — pilot 後にしか存在しない `planned_sigma` 実値、baseline mean 実値、採用 `n`、分類結果は本文に書かれていない。記載はすべて算出手順と将来の結果型に留まる。[本文:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:96)

16. `refuted` — policy bytes の SHA-256 値は本文にない。実際の policy hash `405e26…079c4` は本文中に出現せず、自己参照禁止の説明だけである。[本文:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:3)

## 不一致

`real` — 本文は「1 arm ブロックは5 rep。ブロックは全部で12本」と書くが、実装上は6 group × 4 arm block = 24 arm block である。12 は `sizing.pilot_pair_blocks.total`、すなわち5対からなる pair block の数で、各 pair block に2つの5-rep arm block がある。本文の39–42行は arm block と pair block を分けて書き直す必要がある。[本文:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:39) [policy:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:170) [driver:1534](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:1534)

`real` — `pairing.schedule_receipt_schema = "paper-story-a1-balanced-schedule-receipt/v1"` が本文のどこにも投影されていない。依頼された `pairing` 全 field との一致を満たさない。[policy:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:66) [driver:1562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:1562)

`real` — seed 原像 template が1文字単位では一致しない。本文は `<64 文字の小文字 16 進>|counter=<0 起点の 10 進>`、policy と driver が要求する文字列は `<64-lowercase-hex>|counter=<zero-based decimal>` である。意味の翻訳ではあるが、逐語照合の要件には不合格である。[本文:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:56) [policy:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:71) [driver:1262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:1262)

`real` — alpha 上限の scope が一致しない。本文は無限定に「全試行・全条件の合計 ≤ 1/20」とするが、`certification_attempt` と `_alpha_spending_summary` は workload ごとにリセットされ、certificate も `all-attempts-per-workload` と明記する。したがって実装は各 workload で最大 `1/20`、3 workload 全体では最大 `3/20` である。登録済みのより厳しい全体 `1/20` を緩めず、発効前に整合させる必要がある。[本文:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:162) [sizing:640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/tools/size_paper_story_a1_balanced.py:640) [sizing:783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/tools/size_paper_story_a1_balanced.py:783)

`real` — `execution` の全 field は本文へ投影されていない。完全に欠けるのは `durable_measurement_base`、`materialization`、`materialization_relative_path`。`campaign_shape` は「fresh exact-two-arm balanced-five-rep」の `fresh` がなく、`schedule_round_definition="one complete workload schedule"` も明示されていない。[本文:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:187) [policy:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:22)

## 裁量の余地

`real` — `A` と `B` の役割対応が本文に明記されていない。実装では `bit=0` が `(variant, baseline)` の後に `(baseline, variant)`、すなわち `A=variant`、`B=baseline` で固定されるが、本文は `A^5 B^5…` の記号だけを示す。このままでは人間可読本文だけから seed bit と物理 arm 順を一意に復元できない。[本文:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:43) [driver:1531](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:1531)

`refuted` — 「必要なら」「必要に応じて」「適宜」は存在せず、再走理由・観測 field・分類・候補範囲は閉じている。上記の A/B 未定義と欠落 field 以外に、測定後の判定者裁量へ開いた文言は確認しなかった。[本文:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:68)

## 恒真な保証

`real` — 「探索20,000、認証100,000を凍結」と「n 範囲28..4096を凍結」は sizing 実装の拒否条件になっていない。`SizingConfig.validate()` は試行回数を `1..1,000,000`、`n_min/n_max` を `28 <= n_min <= n_max <= 4096` の任意値として受理する。さらに sized certificate consumer は選択 `n/df/k/sigma` を照合するだけで、certificate 内の試行回数・candidate grid を照合しない。このため、例えば1試行や縮小 grid の certificate でも後段へ到達しうる。[本文:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:156) [sizing:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/tools/size_paper_story_a1_balanced.py:100) [driver:1028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:1028)

`refuted` — 本文は16規則すべてに実装済み保証があるとは主張しておらず、「登録した判定規則であり、実装完全性の証明ではない」と明示する。この限定により、16規則の文字列列挙自体は恒真な実装保証にはなっていない。[本文:277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:277)

`refuted` — 未発効なのに発効済みとする保証はない。policy の `preregistration.path/sha256` はともに `null` で、driver はこの状態で execution を拒否する。[policy:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:87) [driver:1472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:1472)

## 未照合の項目

`real` — `compute-job-body-preflight` と `before-each-trace-and-perf-build` における実際の CCBench 拒否は未照合である。射影された driver 内では `login-submit`、`driver-measurement`、`artifact-consumer` の3呼出しだけを確認でき、残る面を実装する job shell・pipeline/build 側は必読射影に含まれていない。[driver:2066](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:2066)

`real` — bench lock の実取得・全 block 保持、各 arm block 前の competing-tenant probe、settle の実行回数は policy と driver の受渡しまで照合したが、実行主体である `run_campaign` / pipeline 内部は射影外なので未照合である。[driver:1527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:1527)

`real` — 「生成側と検証側は別実装」の検証側は、指定されたファイル群に実体がないため未照合である。sizing generator は確認したが、独立した replay/verification 実装の挙動は確認していない。[本文:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:181)

`real` — 制約どおりテストは実行していない。結論は指定ファイルの静的検査と、読み取り専用の文字列・式計算による。

## 総括

- 最優先: 20,000/100,000 と n=28..4096 が実装上固定されず、後段 consumer も逸脱 certificate を拒否しないため、発効を止める。
- 次点: alpha `1/20` は本文が全 workload 合計、実装が workload ごとであり、厳しい側を緩めず整合させる。
- 12 pair block / 24 arm block を明確に分離し、`A=variant`、`B=baseline` を明記する。
- `schedule_receipt_schema` と逐語どおりの effective-root preimage template を本文へ追加する。
- `execution` の欠落 field と `campaign_shape` / `schedule_round_definition` の不足を補う。