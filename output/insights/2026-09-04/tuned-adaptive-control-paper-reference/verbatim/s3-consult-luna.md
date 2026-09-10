## 所見

1.

- 見出し: **must-fix — 生きた paper-story README では、未認証の性能値と但し書きが離れており、数値だけを引用できる。**
- 根拠: [docs/paper-story/README.md:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/paper-story/README.md:84) は「`48 スレッドで +186.6% / +244.4% / +335.2%`」と述べるが、未認証の明示は同 `:102-103` の「`trace-disabled の性能測定のみで、直列性の検査を通していない`」まで現れない。D1506 自体も [docs/decisions.md:46923](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/decisions.md:46923) の数値と、同 `:46939-46940` の限界が離れている。プランの追記案 [s2-plan.md:137](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/artifacts/t2186-t2239-tuned-adaptive-control/s2-plan.md:137) は「今後の基準線」に但し書きを足すだけで、既存の数値段落を隣接修正しない。
- 影響: `README.md:84-89` だけを抜き出すと、認証済みの比較結果として引用できてしまう。
- 提案: `README.md:84` の段落冒頭または数値と同じ文に「以下は未認証の trace-disabled 観測値」と追記する。D1506 は履歴として変更せず、生きた入口側で遮断する。

2.

- 見出し: **must-fix — 「T-2189 の決着が論文図への昇格条件」という案は、正しさ検査を十分条件にしている。**
- 根拠: プランは [s2-plan.md:123](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/artifacts/t2186-t2239-tuned-adaptive-control/s2-plan.md:123) から `:128` で、現 provenance の出力 path が repo 外であり、paper path を pin する test と directory-wide consumer が無いと正しく指摘する。一方、同 `:135` の提案正文は「`論文図への昇格条件は対応する correctness 検査の決着`」と単数の十分条件として書く。
- 影響: T-2189 が通っただけで、path と provenance が結び付かない copy まで paper-ready になったように読める。
- 提案: 「T-2189 は必要条件であり、それだけでは昇格しない。別途昇格が決着するまでは未認証観測図」とする。「昇格条件」という十分性を含む表現は削る。新しい gate の提案は不要。

3.

- 見出し: **must-fix — figures 台帳へ足す節には Pegasus と旧 `linux-baremetal` の非結合境界が隣接していない。**
- 根拠: 提案正文 [s2-plan.md:132](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/artifacts/t2186-t2239-tuned-adaptive-control/s2-plan.md:132) から `:135` は図の系列と未認証を述べるが、Pegasus、CCBench 版、patch、反復、集約、`clocks_per_us` の差を述べない。この節は [docs/paper-story/figures/README.md:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/paper-story/figures/README.md:17) から `:19` の旧図一覧直後へ入る。新図は provenance `:72-74` の `env_tag=pegasus`、`ccbench_commit=511c953`、patch あり。旧図は figures README `:128-149` の `linux-baremetal`、`6656e93`、5 反復、`clocks_per_us=1800`。
- 影響: figures README だけを読む執筆者が、隣接する旧図と新図を同じ比較系列や時系列として並べる経路が残る。
- 提案: 新図 path と同じ段落に「旧 fig2b/fig2c とは環境、CCBench、patch、反復、集約、`clocks_per_us` が異なり、同じ図・表・時系列・再現判定へ畳まない」と明記する。

4.

- 見出し: **must-fix — 編集予定の figures README には caption 正文の既存一致 pin があるが、プランの検証集合に無い。**
- 根拠: [orchestrator/tests/test_s1_9pair_figure_provenance.py:790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/tests/test_s1_9pair_figure_provenance.py:790) から `:792` は `provenance["caption"] not in readme` を拒否する。これは path や README の SHA でなく caption 本文を key に張る pin である。プランの検証は [s2-plan.md:204](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/artifacts/t2186-t2239-tuned-adaptive-control/s2-plan.md:204) から `:210` の docs checker、spool dry-run、grep だけ。
- 影響: 追記時の整形で既存 fig4 caption が動いても、予定された検査では検出されない。
- 提案: caption 節を逐語不変と明記し、親の関連テストへ `test_s1_9pair_figure_provenance.py` を追加する。新規 test は不要。

5.

- 見出し: **nit — A-1 の旧 v2 比較は「過去 policy」だけでなく、現在も既定選択される実行 surface と test 期待値を持つ。**
- 根拠: [paper_story_a1_paired.py:8583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/campaign/paper_story_a1_paired.py:8583) は `submit --study-id` の default を旧 `STUDY_ID` にする。旧 policy [paper_story_a1_paired.v2.json:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/campaign/paper_story_a1_paired.v2.json:2) から `:16` は `adaptive` 対 `static10` で、adaptive は `BACK_OFF=1, BACKOFF_FIXED=-1`。job body も [paper_story_a1_paired.sh:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/pegasus/paper_story_a1_paired.sh:37) から `:43` で旧 study を既定にする。test は [test_paper_story_a1_job_contract.py:1208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/tests/test_paper_story_a1_job_contract.py:1208) から `:1213` と同 `:1918-1919` でこれを固定する。ただし policy `:30-35` は `formal=false`、`promotion_prohibited=true`、`result_authority=exploratory`。
- 影響: プランの「残余なし」という列挙は不完全。ただし D1506 は測定自体を禁じず、旧 policy も昇格禁止なので、現状だけで規律 2 違反にはならない。
- 提案: 「非該当」にこの live legacy default と test pin を列挙する。既定を外す変更は本 wave に入れず、必要なら**裁定パッケージ候補**とする。

6.

- 見出し: **凍結境界への byte 変更提案は見つからない。**
- 根拠: [docs/paper-story/figures/README.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/paper-story/figures/README.md:5) は README 自身を可変入口、`:6-8` は PNG/PDF/provenance を凍結物とする。プラン [s2-plan.md:182](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/artifacts/t2186-t2239-tuned-adaptive-control/s2-plan.md:182) から `:188` の変更対象は 2 README と新規 spool fragment だけで、既存 asset は不変。既存 insight も [2026-09-02_cicada-adaptive-three-constants.md:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants.md:172) で未昇格を明記する。
- 影響: nit
- 提案: 現方針を維持する。

変更ごとの主張強度は次のとおりである。

- figures README 追記: 数値を新しく作らないが、全数値を持つ図へ直接リンクする「未認証の観測比較」。図自体にも [plot_t2187_adaptive_consts.py:591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/plot_t2187_adaptive_consts.py:591) から `:595` の `NOT CERTIFIED` 表示が入る。
- paper-story README 追記: 性能値の認証ではなく、執筆時の参照先と引用禁止範囲を定める運用主張。ただし既存数値段落の隣接但し書きが必要。
- worklog fragment: 数値主張ではなく T-2186/T-2239 の終端主張。終端正文は「図への到達を閉じた」までに限定し、T-2189 の correctness 完了を含意してはならない。
- code、test、生成器、既存図: 不変。D1506 の射程を超えて既定 adaptive の測定を禁止する変更は提案されていない。

## 独立走査の結果

主要検索式と件数は以下。件数は `git grep -I -n/-l` の行数/file 数である。

| 検索式 | 行 / file |
|---|---:|
| プランの identity 式 | 503 / 154 |
| プランの constants 式 | 348 / 105 |
| プランの baseline 式 | 147 / 38 |
| プランの mechanism claim 式 | 59 / 27 |
| `three-constants-figures\|t2187_stage` | 17 / 5 |
| `BACK_OFF...1...BACKOFF_FIXED...-1` と逆順、同一行 | 61 / 28 |
| 同じ組合せを `rg -U`, 240 byte 窓 | 288 / 51 |
| `11 状態`、`{0,100,...,1000}`、`560` と到達不能・機構語 | 19 / 9 |
| `186.6\|244.4\|335.2\|41.7\|66.6\|77.1` | 9 / 8 |
| `adaptive_tps`、stock alias、既定 3 定数 | 274 / 66 |
| `-1=stock`、`branch:stock-adaptive`、`BACKOFF_FIXED=-1 baseline/reference` | 16 / 14 |
| adaptive 語を要求せず、定数と直接証拠・sweet spot・機構主張を結ぶ式 | 23 / 12 |
| 旧「hill-climbing が sweet spot を捉えた直接証拠」正文 exact | 3 / 3 |

pin 走査:

- `docs/paper-story/figures/README.md`: path 参照 11 行 / 9 file。現 SHA-256 `1503f749...` の exact pin は 0。本文 pin は test `:790-792` の fig4 caption 一致が 1 件。
- `docs/paper-story/README.md`: path 参照 39 行 / 27 file。現 SHA-256 `1ca5003d...` の exact pin は 0。本文一致 test は見つからない。
- 新規 worklog fragment: 既存 path pin は 0。代わりに [docs/spool/README.md:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/spool/README.md:28) の filename 規則、[docs/spool/worklog/README.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/spool/worklog/README.md:5) の H2 二節、同 `:64-88` の `remaining/base` 規則、[tools/spool_fold.py:1220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/spool_fold.py:1220) の動的列挙に pin される。

残余:

- 旧 campaign report 3 件の正文は現存する。各 `:27`。これはプラン記載どおりで、SHA は [gain-unification README:258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-08-25_paper-story-a3-gain-unification/README.md:258)、`:261`、`:264` に pin されているため不変が正しい。
- A-1 v2 の live default surface と tests はプラン未列挙。上記所見 5 のとおり、現時点では「測定可能だが exploratory、昇格禁止」と分類する。
- `all_adaptive_discrete_states` は [test_backoff_extended_sweep.py:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/tests/test_backoff_extended_sweep.py:164) に残るが、正文 `:165-166` は既定 11 状態の literal coverage だけで、性能や機構の優劣を主張しない。前 wave の nit 分類は維持できる。
- patch の `-1=stock adaptive` は [patches/silo-backoff-fixed.patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/patches/silo-backoff-fixed.patch:9) から `:12` の branch identity。比較主張ではないため「触れない」は維持できる。
- `backoff_requested_us.py:93` の `adaptive BACKOFF_FIXED=-1 baseline` も source-inert の比較基準であり、性能基準線ではない。
- 凍結 snapshots、claim-evidence、既存 insights、decisions、archive の分類は現時点でも成立する。

`rg --files` は 21078、`git ls-files` は 20140、`git status --short` は 0 件だった。テストは実行していない。

## 親 brief 自身への所見

1.

- 見出し: **must-fix — 「T-2186 完了済み、carry は stale」は、差し替え部分の完了と item 全体の完了を混同している。**
- 根拠: 親 brief [s1-brief.md:23](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/verbatim/s1-brief.md:23) から `:26` は T-2186 完了・carry stale と断定する。しかし根拠にした前 wave insight 自身が [t2186-replacement-insight.md:73](/work/1/SFC/tanab/dev-wave-jobs/2026-09-03_t2186-t2239-tuned-adaptive-control/verbatim/t2186-replacement-insight.md:73) から `:77` で、直列性未検査かつ「実際の対照として同じ図に並べるところまでではない」と明記する。現行 worklog も [docs/worklog.md:3482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/worklog.md:3482) で T-2186 を active carry している。
- 影響: 新 worklog が T-2186/T-2239 の終端と T-2189 の correctness 終端を混同し得る。
- 提案: 「前 wave で 10 単位の差し替えは着地済み。ただし T-2186 は現物への論文側導線が未了なので active、T-2189 は別途未了」と訂正する。carry 全体を stale と呼ばない。

2.

- 見出し: **親 brief の「3 定数 producer が実在しない」は広すぎるが、プランは正しく修正している。**
- 根拠: brief `:35-40` は producer 不在を一般化するが、[t2187_adaptive_const_probe.py:290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/pegasus/probes/t2187_adaptive_const_probe.py:290) から `:299` は 3 定数を genome へ実際に出す。一方、v2 の対応表は [test_backoff_figure_provenance.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/tests/test_backoff_figure_provenance.py:24) から `:27` の 2 値対応で、既存 3 WAL の 3 定数 hit は 0。プラン `:156-176` は「v2 consumer surface に producer が無い」へ正しく限定する。
- 影響: brief 単体を正本化すると、別 schema の実在 producer まで不存在扱いになる。
- 提案: プランの限定表現を採る。`BASELINE_BY_GENOME` は本 wave では不変でよい。

3.

- 見出し: **親の図実体・セル数・環境についての実測値は独立照合できた。**
- 根拠: provenance [t2187_stage2_thread_axis.provenance.json:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.provenance.json:72) から `:74` は Pegasus、`511c953`、patch SHA を記録する。同 `:1063-1078` は tuned `s1-u2560`, n=7、同 `:1959-1974` は stock `s100-u10`, n=7。独立集計は 5 cell、3 workload、8 thread、120 行、各 cell 24 行だった。
- 影響: nit
- 提案: 数量主張は維持できる。ただし未認証は同 provenance `:10` と `:6887` のとおり不変。

4.

- 見出し: **「実装面の差分 0」は維持可能だが、A-1 legacy default を不存在扱いしてはならない。**
- 根拠: A-1 v2 は実在するが、policy `:30-35` が exploratory・promotion prohibited と明記し、D1506 は既定 adaptive の測定を禁じない。新図の直接参照、環境境界、但し書き、caption pin は docs と既存 test 実行だけで閉じる。
- 影響: code 変更を本 wave に混ぜると、凍結 policy と互換 route の別裁定へ scope が拡大する。
- 提案: 実装差分 0 を維持する。legacy default の扱いを変えるなら**裁定パッケージ候補**として分離する。

## 総括

- must-fix は、未認証数値への隣接但し書き、昇格条件の十分性撤回、Pegasus/旧環境の非結合文、既存 caption pin の検証追加、親 brief の「T-2186 完了・carry stale」訂正。
- nit は、A-1 live legacy default の走査結果への明記と `all_adaptive_discrete_states` の名称。
- 凍結物の byte 変更提案は無い。実装面の変更も本 wave には不要。
- 絶対規律 2を機械的に緩める提案は無い。ただし現行案には、数値だけを抜ける導線と、T-2189 を昇格の十分条件に読ませる文があり、そのままでは文書上の境界が弱い。
- D1506 の射程を超えた測定禁止もない。A-1 legacy routeや明示 `stock-adaptive` 描画は、機構優位へ昇格しない限り禁止対象ではない。
- 自信が低い判断は A-1 legacy default の運用意図である。実行可能な既定 surface なのは確実だが、凍結研究の再現専用として意図的に残したかはコードだけでは確定できないため、変更提案ではなく裁定パッケージ候補とした。