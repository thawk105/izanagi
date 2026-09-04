結論は docs-only です。既存の対照図を昇格・移動せず、論文ストーリーと図台帳から現物へ直接到達させるのが最小かつ安全です。コード・テスト・生成器・機械設定の変更は要りません。

## A. 既定 adaptive を単独基準線にしている残余の独立再走査

### 走査方法

worktree は clean、`rg --files | wc -l` は `21078` でした。tracked 全テキストを対象に、次の検索式を使用しました。

| 系統 | 検索式 | 結果 |
|---|---|---:|
| identity | `stock[-_ ]adaptive\|stock の適応\|stock適応\|既定.{0,16}(adaptive\|適応 backoff)\|adaptive.{0,16}既定\|BACKOFF_FIXED.?=.?-1\|adaptive_tps` | 503 行 / 154 file |
| constants | `kIncrBackoff\|kMaxBackoff\|BACKOFF_INCR_MILLI\|BACKOFF_MAX_US\|BACKOFF_UPDATE_US\|s100-u10\|s1-u2560\|更新間隔.{0,12}(10\|2560)` | 348 行 / 105 file |
| baseline | `(adaptive\|適応 backoff).{0,48}(baseline\|基準線\|対照\|比較)\|(baseline\|基準線\|対照\|比較).{0,48}(adaptive\|適応 backoff)` | 147 行 / 38 file |
| mechanism claim | `(adaptive\|適応 backoff\|hill-climbing).{0,64}(sweet spot\|勝\|優\|劣\|遅\|殺\|最下\|到達不能\|構造欠陥\|機構)\|(sweet spot\|勝\|優\|劣\|遅\|殺\|最下\|到達不能\|構造欠陥\|機構).{0,64}(adaptive\|適応 backoff\|hill-climbing)` | 59 行 / 27 file |
| figure reference | `three-constants-figures\|t2187_stage` | 17 行 / 5 file |

行数はそれぞれ次の形で算出しました。

```bash
git grep -I -n -E '<検索式>' | wc -l
git grep -I -l -E '<検索式>' | wc -l
```

行折り返しを拾うため、さらに次を `rg -U -I` で走査しました。

```text
(?s)(adaptive|適応 backoff).{0,240}(唯一|単独|baseline|基準線|対照|比較)|(唯一|単独|baseline|基準線|対照|比較).{0,240}(adaptive|適応 backoff)

(?s)(既定|stock|BACK_OFF\s*=\s*1).{0,320}(sweet spot|直接証拠|機構の優|機構として|構造欠陥|到達不能|throughput を殺)|(sweet spot|直接証拠|機構の優|機構として|構造欠陥|到達不能|throughput を殺).{0,320}(既定|stock|BACK_OFF\s*=\s*1)

(?s)BACK_OFF\s*[=:]\s*1.{0,160}BACKOFF_FIXED\s*[=:]\s*-1|BACKOFF_FIXED\s*[=:]\s*-1.{0,160}BACK_OFF\s*[=:]\s*1
```

絞り込みには以下の exact 検索も使用しました。

```text
適応が逃した sweet spot
hill-climbing が sweet spot を捉えているか/逃しているかの直接証拠
tag_bf = "adaptive"
izanagi-backoff-figure-provenance/v2
izanagi-t2187-adaptive-const-figure-provenance/v1
fig2b_backoff_sweep_3workload
docs/paper-story/figures
```

論文 docs から対照図への参照数は、次のコマンドでゼロです。

```bash
git grep -I -n -E 'three-constants-figures|t2187_stage' -- docs ':!docs/archive/**' | wc -l
# 0
```

### 前 wave の 10 単位

未差し替えの単位はありません。現在の実体はすべて差し替え済みです。

| # | 現在のアンカーと確認内容 |
|---:|---|
| 1 | [tools/plotting/plot_backoff.py:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/plot_backoff.py:73) — `DEFAULT_BASELINES=("no-backoff",)`。stock は明示 opt-in のみ。 |
| 2 | [test_plot_backoff_ci.py:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/tests/test_plot_backoff_ci.py:162) — 既定が `("no-backoff",)`、stock 明示指定が受理される期待値。 |
| 3 | [backoff_sweep_report.py:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/campaign/backoff_sweep_report.py:141) — verdict は静的最良対無 backoff のみ。[同:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/campaign/backoff_sweep_report.py:197) で機構 verdict を明示拒否。 |
| 4 | [test_backoff_consumers.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/tests/test_backoff_consumers.py:156) — provenance key が既定 3 定数を明記し、[同:167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/tests/test_backoff_consumers.py:167) で新正文を固定。 |
| 5 | [backoff_sweep.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/campaign/backoff_sweep.py:4) および [同:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/campaign/backoff_sweep.py:191) — 既定 3 定数を文脈点に限定し、機構 verdict に使わない。 |
| 6 | [tools/plotting/README.md:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/README.md:15) — 既定は無 backoff 1 本、stock は既定 3 定数と明記。 |
| 7 | [FIGURE_CONVENTIONS.md:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/FIGURE_CONVENTIONS.md:54) — stock の展開を既定 3 定数へ限定し、[同:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/FIGURE_CONVENTIONS.md:61) で調整済み adaptive を要求。 |
| 8 | [patches/README.md:155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/patches/README.md:155) — [同:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/patches/README.md:159) で観測を既定 3 定数へ限定。 |
| 9 | [figures/README.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/paper-story/figures/README.md:79) と [同:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/paper-story/figures/README.md:186) — fig2b と fig2c の双方で既定値と機構一般を分離。 |
| 10 | [paper-story/README.md:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/paper-story/README.md:63) — 凍結版の古い一般化を列挙し、[同:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/paper-story/README.md:93) で今後の基準線を無 backoff と調整済み adaptive に変更。 |

### 残余

前 wave がまったく挙げていない、成果物を変える material な残余は見つかりませんでした。

ただし byte-level では、旧生成レポートの同一正文が次の 3 file に残っています。件数は次で確認できます。

```bash
git grep -I -n -F 'stock 適応 backoff が静的最良に対してどこに居るか = Cicada の hill-climbing が sweet spot を捉えているか/逃しているかの直接証拠。' | wc -l
# 3
```

| 残存箇所 | DW-G05 の一行影響 | 扱い |
|---|---|---|
| [write-heavy report:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7/reports/backoff-sweep-write-heavy_report.md:27) | 直接読めば既定 adaptive 対静的最良を機構の直接証拠と誤引用できるが、値・certified 受理集合は不変で、paper dossier は安全な 9〜12 行だけを参照する。 | 不変 |
| [balanced report:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e/reports/backoff-sweep-balanced_report.md:27) | 同上。論文値 +11.3% の分母は無 backoff のままで、誤るのは機構解釈だけ。 | 不変 |
| [read-heavy report:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9/reports/backoff-sweep-read-heavy_report.md:27) | 同上。−6.6% の値と受理集合は不変で、旧正文だけが機構一般へ過大化する。 | 不変 |

これらは前 wave が「生成済み campaign report は当時の判断と実測の記録」と明示した既知カテゴリです。また 3 file の SHA-256 は [gain-unification README:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-08-25_paper-story-a3-gain-unification/README.md:252) で束縛されています。直接編集すると既存 proof-chain を壊すため、今回の変更対象にしません。

非該当 hit は次のとおりです。

- [backoff_sweep.py:408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/campaign/backoff_sweep.py:408) の `backoff=adaptive` は一時的なランキング表示で、基準線選択・レポート・台帳・論文主張を作りません。周囲の module 契約も既定 3 定数へ限定済みなのでコード変更対象ではありません。
- `BACKOFF_FIXED=-1 baseline` は inert identity や参照点の検査であり、性能上の機構比較ではありません。
- mutation ledger 内の旧正文は「壊す側」の変異 payload、test の旧正文は不在を要求する負例です。
- 凍結 paper snapshot、古い D、archive、既存 insight の残存は後続 README/D1506 が supersede 済みです。

## B. (P1-a) の是非 — 対照図を論文図の置き場へ昇格させるか

### 「同じ図に並べる」は満たされるか

満たされます。昇格は不要です。

[t2187_stage2_thread_axis.png](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.png) は実見しており、同じ 6 panel・同じ thread 軸に以下を描いています。

- no backoff
- stock adaptive `s100-u10`
- 調整済み adaptive `s1-u2560`
- 追加の調整候補 `s0.5-u2560`、`s1-u640`

provenance を次で集計すると、5 cell、3 workload、8 thread、計 120 行で、stock と `s1-u2560` は各 24 行です。

```bash
jq '{cells:([.primary_values[].cell]|unique),workloads:([.primary_values[].workload]|unique),threads:([.primary_values[].threads]|unique),rows:(.primary_values|length),stock_rows:([.primary_values[]|select(.is_stock_control)]|length),tuned_rows:([.primary_values[]|select(.cell=="s1-u2560")]|length)}' output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.provenance.json
```

したがって T-2239 の視覚的要求は「現物を論文側の入口から参照可能にする」ことで閉じます。ただし「certified な正式対照として variant 採用や論文の性能結論へ使える」までは閉じません。

### 絶対規律 2 との衝突

単に同じ bytes を別ディレクトリへコピーするだけでは、正しさゲートのコードは変わらないため、直接の機械的衝突ではありません。親の「未認証だから即禁止」という根拠は強すぎます。

一方、「論文図へ昇格済み、使用可能」と扱うと実際に次が壊れます。

- [provenance:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.provenance.json:10) と [同:6887](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.provenance.json:6887) は明示的に `NOT CERTIFIED` です。
- provenance の出力 path は [同:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.provenance.json:62)、再現 prefix は [同:6888](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.provenance.json:6888) の repo 外 path を束縛しています。コピー先の paper figure bytes はこの provenance の output ではありません。
- T-2187 の test は [test_plot_t2187_adaptive_consts.py:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/tests/test_plot_t2187_adaptive_consts.py:143) の一時出力を検査する generator test で、現物 paper path を pin しません。
- 既存 paper figure の consumer は fig2b、fig2c、fig4 の basename を個別に固定しています。新しいコピーを自動で認証・検査する directory-wide consumer はありません。

つまり、コピーは「認証された図」にならず、むしろ paper 側の copy と provenance の鎖が切れます。昇格しない provisional 結論には賛成ですが、根拠は「未認証そのもの」だけでなく、凍結物不変更、copy path の provenance 不在、実 asset consumer 不在です。

### 書くべき文の骨格

[figures/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/paper-story/figures/README.md:10) には、図一覧直後へ次の趣旨の独立節を追記します。

> 調整済み adaptive の実対照は paper figure へ未昇格であるが、`t2187_stage2_thread_axis.{png,pdf,provenance.json}` に現物がある。同図は no backoff、CCBench 既定 3 定数、調整済み adaptive を同じ thread 軸へ並べる。これが D1506 の比較を実際に描いた既存図であり、fig2b/fig2c を調整済み adaptive の対照図として代用してはならない。  
> 本図は trace-disabled・直列性未検査で、variant 採用および certified 性能結論の根拠にはしない。論文図への昇格条件は対応する correctness 検査の決着であり、それまでは未認証の観測図としてのみ参照する。

[paper-story/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/paper-story/README.md:93) の「今後の基準線」には次を足します。

> 無 backoff、stock adaptive、調整済み adaptive を同じ軸に描いた現物は figures 台帳の「調整済み adaptive の実対照」節から辿る。したがって執筆者は、既定 adaptive だけを適応側に置いた fig2b/fig2c を機構比較として引用しない。  
> この参照が閉じるのは「実際に同じ図へ並べたこと」までであり、図の値は未認証なので variant 採用・certified claim には使わない。

paper-story README は現物 path を再掲せず figures 台帳の節を指し、所在の正本を一箇所に保つのがよいです。

## C. (P1-b) と (P1-c) の是非

### (P1-b) FIGURE_CONVENTIONS を変更しない

賛成です。

[FIGURE_CONVENTIONS.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/FIGURE_CONVENTIONS.md:3) は図種非依存の規約、[同:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/FIGURE_CONVENTIONS.md:7) は他文書への再掲を避ける設計です。§5 は「何を描くべきか」を定め、具体的な図の所在は paper figure 台帳の責務です。

所在を規約へ加えると、成果物の改名・昇格・後継化のたびに一般規約が更新対象になります。今回の実在欠陥は「論文側台帳から図へ到達できないこと」なので、局所修正先は二つの paper-story README です。

### (P1-c) BASELINE_BY_GENOME を拡張しない

結論には賛成ですが、前 wave の理由 1 と 2 は限定して書き直すべきです。

| 前 wave の理由 | 現在の判定 |
|---|---|
| 3 定数 producer が実在しない | **広い意味では不成立。** [t2187_adaptive_const_probe.py:290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/pegasus/probes/t2187_adaptive_const_probe.py:290) は `BACKOFF_INCR_MILLI`、`BACKOFF_MAX_US`、`BACKOFF_UPDATE_US` を実際に genome へ出す。ただし生成先は専用 result schema であり、`BASELINE_BY_GENOME` を通る v2 producer ではない。 |
| 拡張すると既存 campaign を描けない | **単純な必須 5 値化なら成立するが、不可避ではない。** 現行 validator は [test_backoff_figure_provenance.py:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/tests/test_backoff_figure_provenance.py:253) と [同:435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/tests/test_backoff_figure_provenance.py:435) で 2 値 tuple を作る。3 定数を必須にすれば旧 WAL は unrecognized になる。一方、旧 WAL の欠落を stock default と解釈する互換分岐なら既存図は維持できるため、「どんな拡張でも壊れる」は誤り。 |
| 仮想 producer 向け gate は scope 外 | **成立する。** v2 経路には現在 3 定数 producer が無く、互換分岐まで足すのは未使用経路の一般化になる。 |

既存 3 campaign の WAL に 3 定数が出るかは、次でゼロでした。

```bash
rg -n -o 'BACKOFF_(INCR_MILLI|MAX_US|UPDATE_US)' \
  output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7/runs/wal.jsonl \
  output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e/runs/wal.jsonl \
  output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9/runs/wal.jsonl | wc -l
# 0
```

現行 v2 producer は [plot_backoff.py:599](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/plot_backoff.py:599)、入力 driver は [backoff_sweep.py:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/campaign/backoff_sweep.py:191) で、3 定数を genome に含めません。対して T-2187 は [plot_t2187_adaptive_consts.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/plot_t2187_adaptive_consts.py:39) の別 schema を使います。

したがって `BASELINE_BY_GENOME` は不変でよいです。「producer が一切無い」ではなく「この v2 consumer surface に producer が無い」を根拠にします。

## D. 変更面の実アンカー表

| file | アンカーと現在の逐語 | 変更 |
|---|---|---|
| [docs/paper-story/figures/README.md:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/paper-story/figures/README.md:19) | `fig4_s1a_9pair_direct_comparison... 独立した新図` で図一覧が終わり、次は `fig2_backoff_mechanism` の erratum。 | **追記** — この間へ「調整済み adaptive の実対照、論文図未昇格」節。PNG/PDF/provenance の所在、同軸の系列、未認証、昇格条件を記す。 |
| [docs/paper-story/README.md:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/paper-story/README.md:93) | `今後の基準線。backoff 機構の性能比較は、無 backoff と調整済み adaptive...` | **差し替え拡張** — 散文の基準線指定を figures 台帳の現物節へ結び、fig2b/fig2c を代用しないことと未認証境界を明記。 |
| `docs/spool/worklog/2026-09-03-dev-wave-t2186-t2239-tuned-adaptive-control-1.md` | 新規。命名規則は [docs/spool/README.md:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/spool/README.md:28) の ``<authored>-<wave>-<seq>.md``、正文構造は [worklog/README.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/docs/spool/worklog/README.md:5) の H2 二節。 | **追記** — T-2186/T-2239 の決着、図を昇格せず参照で閉じたこと、未認証境界、静的検査結果を記録。既存 active item の `base:` は実装時に lookup。 |
| [tools/plotting/FIGURE_CONVENTIONS.md:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/plotting/FIGURE_CONVENTIONS.md:61) | `無 backoff と調整済み adaptive ... の 2 本を基準線に置く` | **不変** — 所在は規約の責務外。 |
| [test_backoff_figure_provenance.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/orchestrator/tests/test_backoff_figure_provenance.py:24) | `("0","-1")` と `("1","-1")` の 2 値対応。 | **不変** — T-2187 は別 schema、v2 の 3 定数 producer は不在。 |
| [t2187 provenance:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis.provenance.json:10) | `not_certified: trace-disabled... no serializability check` | **不変** — PNG/PDF/provenance の移動・再生成・改訂なし。 |
| 旧 campaign report 3 file | 各 27 行に旧い「直接証拠」正文。別 insight が SHA-256 を固定。 | **不変** — 既存 proof-chain を壊さず、現行 producer と paper 側の参照境界を正とする。 |

新しい decisions fragment は不要です。D1505/D1506を変更せず適用するだけで、新しい科学的裁定はありません。

## E. 実装面の差分が要るか

要りません。

- 対照図は既に存在し、同軸比較を実現しています。
- generator、schema、baseline 受理集合、certified selection を変える必要がありません。
- `BASELINE_BY_GENOME` 拡張は未使用 surface 向けの一般化となり、明示された scope 外です。
- 旧 report は hash-bound な過去 artifact で、現行 generator の正文は既に修正済みです。
- `backoff=adaptive` の一時ログは persisted report・台帳・論文 consumer を変えません。

新規 file は worklog spool fragment だけです。手動の file 一覧登録は不要です。[spool_fold.py:1220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/spool_fold.py:1220) が ledger directory を動的列挙し、[check_docs.py:1295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2186-t2239-tuned-adaptive-control/tools/check_docs.py:1295) がその validator を呼びます。固定 file allowlist への追加ではありません。

実装後に親が行う静的確認は次で足ります。

```bash
python3 tools/check_docs.py
python3 tools/spool_fold.py --dry-run --show-diff
git grep -I -n -E 'three-constants-figures|t2187_stage' -- docs ':!docs/archive/**'
```

今回は read-only のため、pytest、docs checker、spool dry-run は実走していません。

## F. 変異事前登録の候補

docs-only かつ実装面差分ゼロなので、変異 matrix は免除でよいです。

README の文言を対象に新しい mutation test を作ることは、仮想リスク向け gate の追加に当たり scope 外です。

## 総括

- 採用を勧める変更:

  - `docs/paper-story/figures/README.md` — 既存の同軸対照図の現物、未認証境界、昇格条件を一箇所で管理する。
  - `docs/paper-story/README.md` — 「今後の基準線」を現物の台帳節へ結び、fig2b/fig2c の誤用を防ぐ。
  - `docs/spool/worklog/2026-09-03-dev-wave-t2186-t2239-tuned-adaptive-control-1.md` — T-2186/T-2239 の決着を記録する。

- (P1-a): **賛成。ただし根拠を修正。** 参照だけで「同じ図に並べる」は満たせる。単なる配置は規律 2 を機械的に弱めないが、copy の provenance と現物 pin が無いため昇格は行わない。
- (P1-b): **賛成。** 規約は比較構成、図台帳は所在を持つ責務分離が成立している。
- (P1-c): **賛成。** 3 定数 producer 自体は存在するが別 schema であり、v2 surface には producer が無い。旧 WAL も 3 定数ゼロなので今の拡張は仮想 gate になる。
- 実装面の差分: **不要。コード・テスト・実行可能 script・機械設定は変更しない。**
- 自信が低い判断: 「論文図への昇格」が単なる配置を指すのか、paper-ready 認定まで含むのかは用語上曖昧です。本プランは後者として扱います。また旧 campaign report の byte 残存は hash-bound な歴史 artifact と判断しました。各 report 自体へ隣接 erratum を要求する別運用規則があるなら追加面が必要ですが、現在の consumer と射影資料からはその規則を確認できません。