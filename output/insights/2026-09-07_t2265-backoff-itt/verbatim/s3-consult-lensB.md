## 総括

静的検査では、現計画のまま凍結・投入してはいけない重大な不一致がある。

特に重要なのは次の 5 点である。

1. `prereg-draft.md` と `s2-plan.md` が、推定量の符号、seed、等価判定、再投入回数、性能試験の有無で一致していない。
2. 草稿の zero-throughput 除外は処置後 outcome による除外になり得る。
3. 「write-heavy 48 以外は gradient 0 が 39〜51%」という親の一般化は、親自身の表の balanced 48 と矛盾する。
4. trace-enabled 主推定量は、計装された系の診断推定量に限定しなければ絶対規律 1 に触れる。現 artifact は生 throughput を保持するため、図・本文・worklog への滑落経路が残る。
5. driver 行番号を動かす計画なのに、既知の deferred-gate 台帳 3 node が変更閉包から漏れている。

一方、計画した cell・workloads・threads は既存 validator を変更せず到達可能であり、新しい Pegasus 投入体も不要である。pytest は指示どおり実行していない。

## 所見 1 — 事前登録草稿と段 2 計画は同一の試験を定義していない

**主張**

少なくとも次が食い違っている。

- 草稿は `Z=1 minus Z=0`、すなわち反転 minus 推奨を定義するが、段 2 は推奨 minus 反転を定義する。
- 草稿は既定 seed と splitmix64 由来の 12 値、段 2 と qsub は SHA-256 由来の別の 12 値を使う。
- 草稿は 95% CI 全体で等価を判定するが、段 2 は 90% CI による TOST を使う。
- 草稿は同一 seed の再投入を 1 回まで、段 2 は 2 回までとしている。
- 草稿の測定条件は trace-enabled 18 run だけで、段 2 の trace-disabled 7 block、5 cell、3 対比、欠測規則を事前登録していない。

**根拠 (file:line)**

草稿の符号は [prereg-draft.md:80-86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/prereg-draft.md:80)、段 2 の逆向き定義は [s2-plan.md:26-44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:26)。seed は [prereg-draft.md:139-166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/prereg-draft.md:139) と [s2-plan.md:101-121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:101) で別物である。CI は [prereg-draft.md:110-114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/prereg-draft.md:110) と [s2-plan.md:62-80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:62)、再投入は [prereg-draft.md:142-144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/prereg-draft.md:142) と [s2-plan.md:133-139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:133) が異なる。草稿の build は trace-enabled のみである [prereg-draft.md:65-76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/prereg-draft.md:65) 一方、性能計画は段 2 にだけある [s2-plan.md:141-156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:141)。

**正しさ境界か整合か**

正しさ境界である。どの文書を先に commit しても、もう一方の解析または投入を実行すれば事前登録違反になる。

**提案**

段 2 の設計を採るか草稿を採るかを先に裁定し、単一の final doc、解析、qsub 逐語を同一仕様へそろえる。性能 7 block を実施するなら、その全条件を final doc に入れる。これは gate の追加ではなく本試験を一意にするための必須修正である。

**反証されたら何が変わるか**

草稿が廃棄予定の単なるメモで、final doc は段 2 から全面生成されると確認できれば、実装 blocker ではなく草稿だけの不整合になる。

## 所見 2 — zero-throughput の event 単位除外は ITT を壊し得る

**主張**

草稿は `T_i` または `T_{i+1}` が 0 の更新を落とし「割当と独立」としている。しかし `T_{i+1}` は現在の割当後に観測される outcome であり、割当が zero commits を引き起こす可能性を排除できない。これは禁止した処置後除外そのものである。

**根拠 (file:line)**

outcome と除外定義は [prereg-draft.md:80-86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/prereg-draft.md:80)、独立との主張は [prereg-draft.md:129-134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/prereg-draft.md:129)。現 parser は `window_commits=0` を拒否せず、正値を要求するのは `window_us` と `step_us` だけである [t2187_adaptive_const_probe.py:1058-1087](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:1058)。段 2 はこの問題を認識し、1 件でもあれば主判定全体を inconclusive とする [s2-plan.md:123-131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:123)。

**正しさ境界か整合か**

正しさ境界である。割当別の zero outcome 発生率が違えば、event を落とした平均差は ITT ではない。

**提案**

段 2 の fail-closed 規則を final doc に採用する。別の finite outcome を採るなら、結果を見る前に数式と意味を固定する。

**反証されたら何が変わるか**

実装契約により全 admissible run で `window_commits>0` が保証され、その保証が測定前に検証されるなら、実害のない到達不能分岐になる。ただし現 parser にはその保証がない。

## 所見 3 — trace-enabled 主推定量は計装系限定でなければ規律 1 に滑る

**主張**

trace-enabled build で window throughput の割当差を推定すること自体は、対象を「計装された診断系の局所応答」に限定すれば成立する。しかし「推奨方向が throughput を X% 改善した」「機構が効いた」と書けば性能比較へ滑る。名称を診断にしただけでは十分でない。

**根拠 (file:line)**

絶対規律 1 は性能比較を trace-disabled build に限定する [CLAUDE.md:58-65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/CLAUDE.md:58)。草稿は診断限定を述べる一方 [prereg-draft.md:34-40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/prereg-draft.md:34)、結果を throughput のパーセントで表示し [prereg-draft.md:80-86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/prereg-draft.md:80)、trace-enabled の `p1`/`p0` median_tps 比較も残す [prereg-draft.md:116-127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/prereg-draft.md:116)。driver は top-level では `headline_eligible=false` を設定する [t2187_adaptive_const_probe.py:3224-3237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:3224) が、row は raw `throughputs`、`median_tps`、`abort_rate` を保持し、row-level には `throughput_scope` しかない [t2187_adaptive_const_probe.py:3361-3402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:3361)。

**正しさ境界か整合か**

図・本文・worklog が「実システムの性能効果」へ一般化すれば正しさ境界である。top-level metadata を常に伴って診断値としてだけ表示する限り、残るのは整合上の事故経路である。

**提案**

final doc と解析結果の推定対象名に `trace-enabled diagnostic system` を入れる。診断値を性能表へ流さず、trace の `p1/p0 median_tps` 比較は削るか診断専用節へ隔離する。図・判定表・worklogにも同じラベルを値の隣へ置く。

**反証されたら何が変わるか**

全 consumer が top-level `headline_eligible=false` を必ず検査し、診断値を性能表へ出せないと現物で示せれば、滑落経路はほぼ閉じる。

## 所見 4 — 未認証表示は概ね守られるが、隣接表示と文言修正が必要

**主張**

認証の exact 2 cell は `tuned` と 11-field `cw-as-dyn` であり、12-field の `p0/p1/p2` は全て未認証である。scope 外に置くこと自体は規律 2 の緩和ではないが、未認証値を選択・fitness・正しさ主張へ使わないことが条件である。

また、共通 `NOT_CERTIFIED` 文言は「trace-disabled performance runs only」と書かれており、診断 artifact にも同じ文言を載せる現実装とは矛盾する。

**根拠 (file:line)**

認証 cell は [t2187_adaptive_const_probe.py:221-246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:221)、exact 契約は [t2187_adaptive_const_probe.py:1152-1176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:1152)。草稿と段 2 も未認証を明記する [prereg-draft.md:40-41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/prereg-draft.md:40)、[s2-plan.md:158-171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:158)。共通文言は [t2187_adaptive_const_probe.py:65-67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:65) で、診断 payload にも無条件で入る [t2187_adaptive_const_probe.py:3228-3237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:3228)。

**正しさ境界か整合か**

未認証値を「正しい variant の性能」と読ませれば正しさ境界である。共通文言の矛盾自体は provenance の整合問題だが、build 種別の誤読につながる。

**提案**

性能表・図・結論の値の隣に「未認証、正しさ主張なし」を置く。認証済み・fitness・選択結果へ昇格させない。診断 artifact には診断用の正確な `not_certified` 文言を使う。

**反証されたら何が変わるか**

下流 consumer が `kind`、`throughput_scope`、`backoff_trace` を優先し、共通文言を build identity として読まないと証明できれば、文言問題は低優先度になる。

## 所見 5 — 主層選択の根拠は親自身の表と矛盾する

**主張**

「write-heavy 48 以外は gradient 0 が 39〜51%」は誤りである。balanced 48 は 3 cell で 2.1%、7.4%、8.1% であり、少なくとも勾配発火の観点では十分に活性である。

**根拠 (file:line)**

balanced 48 の実値は [stage1-measurements.md:25-27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/stage1-measurements.md:25)。その直後の一般化は [stage1-measurements.md:37-39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/stage1-measurements.md:37) で表と矛盾する。同じ誤りが [brief.md:34-36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/brief.md:34) と [prereg-draft.md:91-93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/prereg-draft.md:91) に転載されている。

**正しさ境界か整合か**

主層を結果を見る前に選ぶ根拠の正確性に関わるため、統計的正しさ境界である。ただし write-heavy 48 が backoff 中央値 5〜6 µs で最も床から離れる点までは表が支持する。

**提案**

「唯一発火する層」という根拠を撤回し、「最も床から離れ、最大の処置差を期待した層」に限定する。balanced 48 も活性だったことを明記し、副次層にした理由を別途固定する。

**反証されたら何が変わるか**

39〜51% が gradient 0 以外の別指標を指すと示されれば表現問題になるが、現見出しと本文ではその読みは成立しない。

## 所見 6 — 生死確認は outcome-blind pilot ではあるが「結果を 1 つも見ていない」ではない

**主張**

生死確認では policy 2 の event 数、割当比、実現率、可否率という処置依存の構造結果を見ており、検出力と主層の説明に利用している。brief の「反実仮想の結果を 1 つも見る前」は過大である。

また、同じ既定 seed の決定的 LCG prefix が各 run で 0.52 前後になったことは実装の生存確認にはなるが、物理過程との統計的独立性を証明しない。

**根拠 (file:line)**

brief の強い主張は [brief.md:8-12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/brief.md:8)。実際に見た構造値は [stage1-liveness.md:33-54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/stage1-liveness.md:33)、それを設計根拠へ使った記述は [stage1-liveness.md:61-79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/stage1-liveness.md:61)。草稿はこの限定をより正確に開示している [prereg-draft.md:22-32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/prereg-draft.md:22)。LCG が毎回進む実装は [cicada-adaptive-counterfactual.patch:548-563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/patches/cicada-adaptive-counterfactual.patch:548) だが、草稿はそこから独立性まで主張している [prereg-draft.md:59-63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/prereg-draft.md:59)。段 2 は形式的独立を主張しない [s2-plan.md:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:121)。

**正しさ境界か整合か**

事前登録の透明性と ITT の因果ラベルに触る正しさ境界である。構造 pilot の実施自体は違反ではない。

**提案**

「outcome を見ていない構造 pilot」と表現し、見た field と、それが event 数・反復数の決定へ使われたことを残す。「割当列は厳密に独立」は撤回し、事前固定された疑似無作為割当による近接効果と限定する。

**反証されたら何が変わるか**

割当 seed が試験ごとに真正乱数から独立抽出され、その手順まで事前固定されていたと示されれば、独立性への異議は弱まる。現計画の固定 seed 列では該当しない。

## 所見 7 — DW-O13 と F660 には静的な到達不能 blocker はない

**主張**

計画の診断 cell、workloads、threads、rep index は既存 `_validate_backoff_trace_contract` と PBS の exact literal に一致する。性能 5 cell も `_validate_grid_contract` を変更せず通る。投入は既存 PBS が既存 Python driver を実行するだけで、新規解析 module は offline である。

**根拠 (file:line)**

診断 literal は [t2187_adaptive_const_probe.py:266-270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:266)、契約は [t2187_adaptive_const_probe.py:2698-2724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:2698)、PBS 側は [t2187_adaptive_const_probe.pbs:20-23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:20) と [t2187_adaptive_const_probe.pbs:136-143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:136)。性能 grid は exact `none` 1 本と stock control 1 本を要求する [t2187_adaptive_const_probe.py:445-473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:445) だけで、同型 5 cell が既存テストを通る [test_t2187_adaptive_const_probe.py:1406-1418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/orchestrator/tests/test_t2187_adaptive_const_probe.py:1406)。PBS は既存 driver を直接実行する [t2187_adaptive_const_probe.pbs:57-60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:57)、[t2187_adaptive_const_probe.pbs:365-383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:365)。解析 module を投入面へ接続しない計画は [s2-plan.md:217-232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:217)。

**正しさ境界か整合か**

現物上は整合している。validator の新設・緩和や新規 Pegasus 実行体は不要である。

**提案**

既存 validator は変更しない。seed argv の追加は処置 identity を実際の binary へ届けるための入力配線として限定する。

**反証されたら何が変わるか**

admission registry が path ではなく現 bytes/hash を固定している場合は登録更新が必要になる。ただし registry 自体は射影対象外で、brief の自己申告 [brief.md:24-26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/brief.md:24) 以外に独立確認できる根拠はない。

## 所見 8 — `pending` 置換の pin 閉包から既知の deferred 台帳 3 node が漏れている

**主張**

直接の `"pending"` consumer だけでなく、driver/PBS 改行で失効する既知の行番号 pin も変更閉包に入る。段 2 のテスト計画は後者を列挙していない。

**根拠 (file:line)**

直接変更が必要な箇所は次である。

- 新 prereg path と hash helper: [t2187_adaptive_const_probe.py:80-81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:80)、[t2187_adaptive_const_probe.py:812-815](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:812)
- top-level metadata: [t2187_adaptive_const_probe.py:2727-2737](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:2727)
- row metadata: [t2187_adaptive_const_probe.py:3361-3388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:3361)
- `"pending"` の逐語テスト: [test_t2187_adaptive_const_probe.py:2021-2036](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/orchestrator/tests/test_t2187_adaptive_const_probe.py:2021)
- driver/PBS bytes の変更に伴い自動更新される `driver_sha256` / `pbs_sha256`: [t2187_adaptive_const_probe.py:777-783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:777)、対応テスト [test_t2187_adaptive_const_probe.py:2065-2076](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/orchestrator/tests/test_t2187_adaptive_const_probe.py:2065)
- 説明 consumer として段 2 が挙げた `patches/README.md`: [s2-plan.md:212-215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:212)

さらに一次資料は `test_ccbench_spawn_sites.py` の deferred gate 台帳 3 node が sink を行番号で pin し、driver 書換えで赤くなると明記する [README.md:89-110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-counterfactual/README.md:89)。段 2 の列挙 [s2-plan.md:253-280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:253) にはない。

歴史的記録である [README.md:136-142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-counterfactual/README.md:136) と [stage1-liveness.md:81-85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/stage1-liveness.md:81) の `"pending"` は当時の事実なので変更対象ではない。

**正しさ境界か整合か**

直接 hash の top-level/row 一致は provenance の正しさ境界である。deferred 台帳 3 node は整合・実効性の問題だが、未更新なら必須検査が赤になる。

**提案**

変更閉包に、driver、PBS、現在の probe test、新解析 test、既存説明 consumer、deferred 台帳 3 node を入れる。台帳 3 node は新しい gate の追加ではなく既存 pin の機械的追随である。

**反証されたら何が変わるか**

driver の最終 diff が pin 対象行より後だけを動かし、3 node の行番号が不変なら台帳更新は不要になる。現計画は冒頭付近から変更するため、その可能性は低い。

## 所見 9 — 12-field 一般を新事前登録へ束縛する計画は範囲が広すぎる

**主張**

段 2 は「12-field policy cell を含む run」全般へ新 hash を付けるとしている。しかし parser と grid validator は任意の 12-field policy grid を許す。新事前登録が exact `p0/p1/p2` と固定 axes だけを覆うなら、任意 grid へ同 hash を付けることは束縛範囲の過大表示になる。

**根拠 (file:line)**

広い emission 計画は [s2-plan.md:187-203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:187)。現 parser は 12-field の任意 label・policyを受理する [t2187_adaptive_const_probe.py:334-431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:334)。performance grid も exact 5 cell には限定しない [t2187_adaptive_const_probe.py:445-473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:445)。

**正しさ境界か整合か**

`counterfactual_preregistration` が「この artifact は本書の試験条件を満たす」という意味なら provenance の正しさ境界である。単なる参照 pointer なら整合上の曖昧さにとどまる。

**提案**

validator は変更せず、hash emission を exact 診断 literal と exact 性能 5-cell literal に限定する。別 grid は従来どおり生成可能だが、新事前登録に適合したとは表示しない。

**反証されたら何が変わるか**

field の契約が「適合ではなく関連文書への任意 pointer」と明文化されるなら過大束縛ではなくなる。ただし草稿は bytes 束縛として説明している [prereg-draft.md:10-20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/prereg-draft.md:10)。

## 所見 10 — seed は cell identity 以外の build identity を全て変える

**主張**

policy 2 の seed を変えると、cell文字列と `_cell_identity` は変わらないが、canonical genome、genome hash、source evidence、generator receipt、buildcache key、通常は binary sha256 が seed ごとに変わる。既存 artifact と新 artifact は同じ cell label でも同一 build ではない。

**根拠 (file:line)**

seed は compile define である [cicada-adaptive-counterfactual.patch:35-36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/patches/cicada-adaptive-counterfactual.patch:35)、[cicada-adaptive-counterfactual.patch:90-92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/patches/cicada-adaptive-counterfactual.patch:90) ため、policy 2 の constexpr state に入る [cicada-adaptive-counterfactual.patch:265-282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/patches/cicada-adaptive-counterfactual.patch:265)。現 driver でも seed は genome に入る [t2187_adaptive_const_probe.py:563-586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:563) 一方、cell identity には入らない [t2187_adaptive_const_probe.py:589-608](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:589)。genome から evidence と buildcache が導出される [t2187_adaptive_const_probe.py:3274-3307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:3274) ためである。

**正しさ境界か整合か**

分析が cell label だけで identity を畳み、異なる seed binary を同一 binary と主張すれば正しさ境界である。seed を run-level treatment identity として保持する限りは意図した整合である。

**提案**

解析上の run identity を最低でも `(exact cell literal, step_policy_seed, binary_sha256)` とする。同一 seed から期待 genome を再計算して束縛する。12 diagnostic artifact 間で genome、buildcache key、binary sha の一致を要求してはいけない。policy 0/1 は計画どおり既定 seed の genome を維持する。

既存 liveness artifact は歴史的事実として有効だが、`pending`、旧 driver/PBS、既定 seed の artifact なので本試験の 12 run に混ぜない。

**反証されたら何が変わるか**

build system が seed define を identity から意図的に除外しながら正しい seed binary を構築すると示されれば一部は変わるが、現コードは genome と source evidence を key に含めるため該当しない。

## 所見 11 — 性能 7 block の固定 cell 順は時間ドリフトと完全に交絡する

**主張**

全 block が `none, stock, p0, p1, p2` の同じ順で、driver も各 workload・threads 内で cell 順に測る。そのため `p1/p0`、`p2/p0`、`p2/p1` は cell と job 内時刻が固定的に交絡する。段 2 自身もこれを認めている。

**根拠 (file:line)**

7 本の qsub は同じ cell 順である [s2-plan.md:303-312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:303)。driver の実行順は workload、threads、cell の順である [t2187_adaptive_const_probe.py:3333-3356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/tools/pegasus/probes/t2187_adaptive_const_probe.py:3333)。段 2 は残留ドリフトを明記する [s2-plan.md:326-330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:326)。旧事前登録はこの問題に対し block ごとに開始位置を巡回した [dynamic-backoff-preregistration.md:79-80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/docs/dynamic-backoff-preregistration.md:79)。

**正しさ境界か整合か**

性能対比を cell 効果として解釈すれば統計的正しさ境界である。「固定順を含む記述値」としか読まないなら実効性の問題にとどまる。

**提案**

validator や実行体を変えず、7 block の qsub cell 順を事前登録した巡回順へ変える。解析は `cell_order` を検査する。固定順を維持する裁定なら、性能対比は順序交絡した探索的記述であり因果的な優劣判定を出さない。

**反証されたら何が変わるか**

測定期間中に job 内時間ドリフトが無いことを独立に示せれば交絡は実害を失うが、結果後の確認だけで主張を昇格させるべきではない。

## 所見 12 — scope 外の一般化と、必要な閉包を分ける必要がある

**主張**

offline 解析 module 本体は brief が要求した推定量計算なので scope 内である。一方、任意 CLI や source 全文から `"pending"` を禁止する文字列テストは、事前登録と実測を成立させる必須要件ではない。逆に、hashの top-level/row 一致、seedが policy 2 binaryへ届く検査、解析の trace/performance 分離、既存 line pin の更新は必須閉包であり、仮想リスク向けの新 gate ではない。

**根拠 (file:line)**

解析 module は brief の明示 scope [brief.md:10-12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/brief.md:10) に入る。任意 CLI は [s2-plan.md:219-232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:219)、source 上の `"pending"` 全禁止は [s2-plan.md:255-260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:255)。一方、診断値を性能表へ流さないことは規律 1 を守る直接条件である [s2-plan.md:234-251](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:234)。

**正しさ境界か整合か**

任意 CLI と文字列全禁止テストは scope 整合の問題である。hash・seed・build・分析入力の束縛は測定 identity の正しさ境界である。

**提案**

本 wave では公開 CLI を作らず、必要なら既存 Python API を親が明示 path で呼ぶ。`"pending"` の source 全文禁止ではなく、生成された対象 artifact の field が exact 64 lowercase hex であることを検査する。必要な consumer・台帳更新は「新設」ではなく既存閉包として実施する。

**反証されたら何が変わるか**

CLI が今回の実測を起動する唯一の既存経路であるなら scope 内へ戻る。段 2 は API を直接公開面としているため、現記述からは必須ではない。

## 親 brief と親の実測への異議

- brief の「反実仮想の結果を 1 つも見る前」は成立しない。正確には「outcome-blind の構造 pilot を見た後、確認的 outcome を見る前」である。
- 「write-heavy 48 以外は gradient 0 が 39〜51%」は親自身の balanced 48 の表に反する。主層選択の説明を修正する必要がある。
- P1-3 の「1 更新 ITT は常時反転 run 効果の近似」は、別軌跡と未測の carryover のため採れない。段 2 が棄却した判断は妥当である [s2-plan.md:317-324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:317)。
- stage 1 の単一 legacy run の run 内 SE は、12 run の cluster SD の実測値ではない。草稿の「±3% を解像できる」という表現は計画仮定に格下げすべきである [stage1-measurements.md:35-36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/stage1-measurements.md:35)、[s2-plan.md:82-100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-backoff-itt/output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md:82)。
- liveness の outcome 未閲覧は、指定された inspector 本体が射影対象外だったため独立検証できない。現状の根拠は親の自己申告だけである。

## 見つからなかったもの (探したが無かった)

- `_validate_backoff_trace_contract` または `_validate_grid_contract` を改訂しなければ planned cells が通らない、という blocker は見つからなかった。
- 新しい `.pbs`、投入用 `.py`、`.sh` を作らなければ測定できない F660 blocker は見つからなかった。
- 認証 exact 2 cell、patch A hard pin、既存 literal を緩める計画は見つからなかった。
- patch C 自体を seed 引数化のために変更する必要は見つからなかった。既に seed compile option と LCG を持つ。
- 指定 11 ファイル内の path search では、`counterfactual_preregistration` の別の role 名・group 名による key-side pin は見つからなかった。実名を特定できたのは一次資料が告知する deferred 台帳 3 node までであり、対象ファイルが射影外なので node 名・現在行番号は根拠なし。