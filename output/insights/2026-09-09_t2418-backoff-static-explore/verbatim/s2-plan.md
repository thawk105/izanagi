## 編集面アンカー表

| file | 現行 anchor | 実装内容 |
|---|---|---|
| [backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:81) | L81 `EXTENDED_RUN_KIND = "extended"`、L82 `T2266_RUN_KIND = "t2266-tail"`、L83 `RUN_KINDS = ...` | L82 と L83 の間へ `T2418_RUN_KIND = "t2418-explore"` を追加し、L83 を三要素にする。L89 `T2266_CLAIM_SCOPE` の後、L91 の comment の前へ `T2418_*` 定数群を追加する。既存 `EXTENDED_*` / `T2266_*` は変更しない。 |
| [backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:403) | L403 `_t2266_points`、L423 `return points`、L426 `def measurement_order` | L423 と L426 の間へ `_t2418_points(tag)` と `_t2418_ordered_points(tag)` を追加する。前者は `none`、`adaptive`、静的 3 点を作り、後者だけが既存 workload seed で shuffle する。 |
| [backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:436) | L436 `t2266_measurement_order`、L441 `t2266_genomes`、L443 `return ...`、L446 condition gate | L443 と L446 の間へ `t2418_measurement_order(tag)`、`t2418_genomes(tag)` を追加する。 |
| [backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:497) | L497 `t2266_config_for`、L536 `return ident.bind_environment_contract(...)`、L539 `_T2266RepCapture` | L536 と L539 の間へ `t2418_config_for(tag, workload, *, contract=None)` を追加する。workload literal oracle の照合、environment contract binding は既存二経路と同型にする。 |
| [backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:635) | L635 `_T2266RepCapture.reps_for` の return、L638 `_finite_number` | L635 と L638 の間へ `_T2418RepCapture` を追加する。T2266 class の改名・共通化はせず、同じ rep 捕捉契約を T2418 名と診断で実装する。 |
| [backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:646) | L646 `_t2266_point_label`、L661 unexpected point | L661 と L664 `_load_t2266_report_points` の間へ `_t2418_point_label` を追加する。許可する物理値は独立な `T2418_REALIZED_US` のみ。 |
| [backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:752) | L752 T2266 loader の return、L755 `_t2266_report_document` | 間へ `_load_t2418_report_points` を追加する。certified campaign view、WAL の committed/verify/bench binding、全 rep の有限性を検査し、exactly 5 committed genomes を要求する。 |
| [backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:787) | L787 T2266 document の終端、L790 `materialize_t2266_report` | 間へ `_t2418_report_document` を追加する。JSON の top-level disclosure と各点の `claim_scope`、全 5 rep の throughput/abort-rate 配列を構成する。 |
| [backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:848) | L848 T2266 materializer の return、L851 `run_workload` | 間へ `materialize_t2418_report` を追加する。専用 `.dat` / `.json` を create-only で生成する。T2266 artifact stem は触らない。 |
| [backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:856) | L856 run-kind validation、L862 `if T2266`、L868 `else` | L868 の前を `elif run_kind == T2418_RUN_KIND` に分岐し、T2418 の config/genomes/order/capture を選ぶ。最後の `else` は extended 専用にする。 |
| [backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:946) | L946 `require_all_binary_hashes=(run_kind == T2266_RUN_KIND)` | この式は変更しない。T2418 は `_prebuild_backoff_binaries` L319 の無条件 `_require_distinct_static_binary_hashes(builds)` を通り、符号化後の静的 amounts 4000/6000/11999 の相異を検査する。T2266 固有の全 8 genome 検査も不変。 |
| [backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:975) | L975 完走判定、L981 `materialize_t2266_report` | 同じ完走条件の中で run kind を分け、T2418 のときだけ `materialize_t2418_report` を呼ぶ。未完走時に探索 report を作らない。 |
| [backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:1000) | L1000 `--run-kind`, `choices=RUN_KINDS` | parser 自体は変更不要。L83 の tuple 更新により `t2418-explore` を受理する。 |
| [backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_extended_sweep.py:1014) | L1014 expected-genomes の二択、L1019 T2266 完了検査 | T2418 を含む三択へ変更し、T2418 は `summary.total == 5`、`committed == 5`、`aborted == 0`、専用 `.dat/.json` の存在をすべて要求する。 |
| [test_backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/tests/test_backoff_extended_sweep.py:268) | L268 certified-view helper 終端、L271 最初の test | T2418 の 5-point certified-view fixture と rep-capture helper を追加する。 |
| [test_backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/tests/test_backoff_extended_sweep.py:393) | L393 T2266 identity test 終端、L395 report test | T2418 の exact grid、identity、disclosure test を追加する。L279–289 の `EXTENDED_SWEEP_US[-1] == 1000` test は一切変更しない。 |
| [test_backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/tests/test_backoff_extended_sweep.py:461) | L461 T2266 report test 終端、L463 next test | T2418 report の実 WAL consumer test を追加する。 |
| [test_backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/tests/test_backoff_extended_sweep.py:878) | L878 patched-tree routing test 終端、L880 main completeness test | T2418 が condition gate、prebuild、campaign の順に同じ genome 群を渡す test を追加する。 |
| [test_backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/tests/test_backoff_extended_sweep.py:897) | L897 existing main test 終端、L899 next helper | T2418 main の exactly-five と report artifact 完了条件を追加する。 |
| [test_backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/tests/test_backoff_extended_sweep.py:1030) | L1030 run-kind shell test | 既存 test を保ちつつ T2418 の case、forwarding、stage、finalizer を検査する assertions を追加する。 |
| [b10_backoff_grid.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/b10_backoff_grid.sh:186) | L186–189 run-kind case | accepted pattern を `extended|t2266-tail|t2418-explore` とし、診断にも三値を列挙する。 |
| [b10_backoff_grid.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/b10_backoff_grid.sh:579) | L579 T2266 stage、L581 `else` extended stage | `elif [[ ... == "t2418-explore" ]]` を挿入して `CURRENT_STAGE=t2418_explore_sweep` とする。 |
| [b10_backoff_grid.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/b10_backoff_grid.sh:589) | L589–591 T2266 だけが `--run-kind` を追加 | 条件を「非 default の T2266 または T2418」に広げる。L594 の extended-only add-analysis/report 分岐は不変。 |
| [b10_backoff_grid.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/b10_backoff_grid.sh:624) | L624–641 T2266 finalizer | 直後へ `elif run_kind == "t2418-explore"` を追加し、WAL の unique commit が exactly 5、かつ専用 `.dat/.json` が regular non-symlink file であることを要求する。 |
| [submit_b10_backoff_grid.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/submit_b10_backoff_grid.sh:7) | L7–9 usage | `--run-kind extended|t2266-tail|t2418-explore` と表示する。 |
| [submit_b10_backoff_grid.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/submit_b10_backoff_grid.sh:36) | L36–39 accepted-values case | 三値を exact に受理する。default の L12 `extended` は維持する。 |
| [submit_b10_backoff_grid.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/tools/pegasus/submit_b10_backoff_grid.sh:184) | L184 QSUB_ENV、L185–187 T2266 forwarding | T2266 または T2418 の非 default run kind を `B10_RUN_KIND=...` として qsub へ渡す。 |

[backoff_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore/orchestrator/campaign/backoff_sweep.py:58) は編集しない。L58 `_BASE`、L88 `_require_backoff_condition_gate`、L172 `_official_durable_root_policy` は既存 import のまま利用する。指定された no-touch 3 ファイルにも変更を提案しない。

## 新 RUN_KIND の定義

追加する定数と値は次で固定する。

```python
T2418_RUN_KIND = "t2418-explore"
T2418_REQUESTED_US = (2000, 4000, 9999)
T2418_REALIZED_US = (2000, 4000, 9999)
T2418_UNREALIZED: dict[int, str] = {}
T2418_REPORT_SCHEMA = "t2418-backoff-static-explore-report/v1"
T2418_CLAIM_SCOPE = "exploratory_backoff_tail_only_not_formal_series"
T2418_FORMAL_GRID_STATUS = "not_selected_in_this_wave"
T2418_FORMAL_STOPPING_CRITERION_STATUS = "not_defined_in_this_wave"
```

campaign identity は以下にする。

- `spec_slug`: `t2418-backoff-static-explore-v1-silo-{tag}`
- `search_tag`: `sweep`
- `trial`: `t2418-backoff-static-explore-v1`
- `search_config["scale"]`: `t2418-backoff-static-explore-v1`
- `spec_content`: `T-2418 exploratory static-backoff right-tail measurement; not a formal series; workload={tag}`
- report stem: `t2418-backoff-static-explore-{tag}`

追加関数は `_t2418_points`、`_t2418_ordered_points`、`t2418_measurement_order`、`t2418_genomes`、`t2418_config_for`、`_T2418RepCapture`、`_t2418_point_label`、`_load_t2418_report_points`、`_t2418_report_document`、`materialize_t2418_report`。

5 genomes の unshuffled 定義は exact に次とする。

```text
none       BACK_OFF=0 BACKOFF_FIXED=-1
adaptive   BACK_OFF=1 BACKOFF_FIXED=-1
fixed-2000us BACK_OFF=1 BACKOFF_FIXED=4000
fixed-4000us BACK_OFF=1 BACKOFF_FIXED=6000
fixed-9999us BACK_OFF=1 BACKOFF_FIXED=11999
```

`git grep -n -e 't2418-explore' -e 't2418-backoff-static-explore' -e 'T2418_' -- .` を tracked repo 全体に実施し、現行 tree では一致ゼロだった。既存 `t2266-tail` と run kind、slug、trial、scale、report stem のいずれも衝突しない。

## 探索開示の設計

`t2418_config_for` の `search_config` と T2418 JSON report の top level の両方へ、同じ exact fields を載せる。

```json
{
  "run_kind": "t2418-explore",
  "claim_scope": "exploratory_backoff_tail_only_not_formal_series",
  "exploratory": true,
  "formal_series": false,
  "exploration_values_us": [2000, 4000, 9999],
  "requested_us": [2000, 4000, 9999],
  "realized_us": [2000, 4000, 9999],
  "unrealized": [],
  "formal_grid_status": "not_selected_in_this_wave",
  "formal_stopping_criterion_status": "not_defined_in_this_wave"
}
```

配置先は以下。

- campaign lock に束縛される `search_config`: 上記全 field、5-entry `grid`、seed、measurement order を保持する。
- `.json` report: 上記全 fieldに加え、campaign/workload、5 points、各 5 rep、correctness 状態を保持する。
- `.dat` report: `# provenance: {...}` の JSON comment に同じ開示を埋め込み、数値行は静的 3 点だけとする。
- 各 JSON point: `claim_scope`、`source_measurement="trace_disabled"`、`correctness_verified=true`、`performance_certified=false`、`certified=false` を載せる。
- completion/failure/reservation/submission receipts: 既存の `run_kind` binding で `t2418-explore` を保持する。科学的開示の正本は search_config と専用 report とし、receipt schema は増やさない。

`formal_grid_status` は「探索後に選ぶ本格格子が、この wave ではまだ選択されていない」、`formal_stopping_criterion_status` は「第2段の停止基準が未定で、この wave では事前登録しない」という D1813 の境界を明記する。具体的な飽和閾値は実装しない。

## PBS 経路の変更点

- job の run-kind case は `extended|t2266-tail|t2418-explore`。
- stage は `t2418_explore_sweep`。failure receipt の `stage` と `run_kind` から探索走だと識別できる。
- `SWEEP_COMMAND` は T2418 に `--run-kind t2418-explore` を付与する。
- `backoff_overthrottle.py` と既存 extended report は引き続き `extended` のみ。T2418 report は driver 内で完走後に生成する。
- finalizer は T2418 の WAL に unique committed variants が exactly 5 あることと、`t2418-backoff-static-explore-{workload}.dat/.json` の存在を検査する。
- submit script は CLI usage、case、qsub environment の三箇所で新値を扱う。manifest/submitted/failed receipts は既存コードにより run kind を記録する。
- `EXPECTED_WALLTIME_S=18000`、各 cap、PBS `05:00:00` は変更しない。

## 追加テスト

- **Exact constants/identity:** 三つの物理値、schema、claim scope、run kind、slug/trial/scale を独立 literal と比較する。値・version・identity の取り違えを殺す。
- **Exact five-genome projection:** `[(0,-1),(1,-1),(1,4000),(1,6000),(1,11999)]` と exact 比較する。context 欠落、未符号化値、点の増減を殺す。
- **Independent seeded order:** hard-coded labels と hard-coded workload seeds から test 側で shuffle した列と exact 比較する。固定順、seed 誤用、別格子流用を殺す。
- **Config disclosure:** 上記開示 field/value と `grid` の exact flags を検査する。単なる `run_kind` 追加だけで探索境界が欠落する変異を殺す。
- **T2418 static-hash rejection:** T2418 genomes の二つの静的 amount に同じ SHA を返し、`_prebuild_backoff_binaries` が拒否することを検査する。静的 SHA guard の除去を殺す。
- **Run-path ordering:** event 列が patch → materialization → Masstree preparation → condition gate → prebuild → campaign であり、gate と prebuild が同じ exact 5 genomes を受けることを検査する。gate/prebuild bypass や別 run-kind routing を殺す。
- **Report/WAL integration:** 5 points × `p2_2.REPS` を実 capture → immutable WAL → certified consumer → `.dat/.json` へ通し、開示、rep arrays、3 static rowsを exact 検査する。summary だけで report を捏造する変異を殺す。
- **CLI completion:** total/committed が 5、aborted 0、両 report 存在時だけ成功し、4 commits、abort、片方欠落では失敗する。緩い完了判定を殺す。
- **PBS and submit routing:** `bash -n` に加え、三値 case、T2418 forwarding、`t2418_explore_sweep`、finalizer の `len(commits) != 5`、専用 stem を pin する。片側 script だけの実装を殺す。

候補集合自身から導いた membership、`all(value in candidates ...)` のような恒真的 assertion は使わず、物理値・wire 値・identity・点数を test 側の独立 literal と exact 比較する。

## P1〜P4 への評価

- **P1 支持。** search_config だけでも campaign identity は分離できるが、第2段が読む数値入口、全 rep の記録、探索境界を伴う可搬 artifact、PBS finalizer の完了証拠が不足する。L646–848 の既存 T2266 report 形式を壊さず、T2418 専用 `.dat/.json` を追加するのが妥当。
- **P2 支持。** D1813 の「3点」は静的探索点であり、brief の完了条件は明示的に「3探索点＋文脈2点」。`none` と `adaptive` は workload ごとの右側変化を解釈する基準で、正式系列へ混ぜることとは別問題。exactly 5 genomes とする。
- **P3 支持。** job L354–379 は実行 script、qsub 時 SHA、`HEAD` blob の三者一致を要求するため commit 前投入は失敗する。wave commit 後に同じ worktree から投入すれば immutable な投入元を保て、動き続ける main checkout より再現可能性が高い。land 待ちは不要。
- **P4 支持。** `t2266-tail` と同じ `t<task>-<purpose>` 形式で、repo 全体の exact search は衝突ゼロ。campaign identity と artifact stem も `t2418-backoff-static-explore-v1` 系へ分離するため、既存正式系列と混同しない。

## 残る不確実性

- 第2段の本格格子と飽和停止基準は意図的に未定であり、本実装では status field に留める。探索結果を見る前に数値基準を追加してはならない。
- 5 genomes が既存 8-genome T2266 と同じ walltime 枠に収まる見込みは強いが、本段では実測していない。
- read-only 指示に従い、ファイル変更、pytest、`bash -n`、PBS 投入は実行していない。テストが緑とは報告しない。

## 総括

`EXTENDED_SWEEP_US` と T2266 系を不変に保ったまま、`t2418-explore` を専用 identity、exactly 5 genomes、専用 report、探索境界の machine-readable disclosure、PBS 完了検査まで一貫して追加できる。condition gate は既存 L927、静的 binary hash 相異検査は既存 L319 の経路をそのまま通し、walltime・反復数・freeze bytes・no-touch 面は変更しない。