# 段 1 brief — fig13: B-10 待ち方 grid 正式走 (report `978195.nqsv`) の forest 図

- 起点 local main: `482f19b88` (2026-09-20 19:00 JST 着手直前)。branch `worktree-dev-wave-fig13-b10-waiting-grid`、開始 gate rc=0 (`startup-gate.log`)。
- 台帳 ID 未起票 (ユーザー依頼文がそう明記)。fig11 wave (entry 1738) と同形の軽量版。

## 研究前進 (1 行)

論文ストーリーの B-10 待ち方 grid の判定 (稿 `docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md`、限定 11「論文図は無い」) に、
3 族 Holm の判定と 36 cell の効果量・95% paired-block 区間・等価域 ±3.0% を 1 枚で見せる結果図 fig13 を与える。完了判定 =
png / pdf / provenance.json の 3 成果物が login で実データから rc=0 で出て、figures/README.md の節 + 日本語キャプション正文が着地 test で
provenance と一致し、変異 matrix・焦点走・受入を経て local main に land する。

## scope (実アンカー表)

| 面 | path | 作業者 | 内容 |
|---|---|---|---|
| 実装 | `tools/plotting/plot_b10_waiting_grid_forest.py` (新設) | Codex author (D95) | 生成器。tracked 一次資料 2 file を pin し、repo 外の受領証 2 file を SHA-256 で束縛、判定は再計算して照合 (作らない)、forest 図、fail-closed layout check、provenance |
| 実装 | `orchestrator/tests/test_plot_b10_waiting_grid_forest.py` (新設) | Codex author | 実寸 fixture (3 workload × 3 block × 15 点 × 5 rep = 135 record、36 cell、3 族)、負例、着地 test、`__main__` harness |
| docs | `docs/paper-story/figures/README.md` | 親 | 一覧表に fig13 行を 1 行追加 + 末尾に `# \`fig13_b10_waiting_grid_forest\` — …` 節 (何を示す図か / 既存図との関係 / 入力 / 再現 / 作図規約への適合 / キャプション正文 / proof chain / 着地 bytes の SHA-256) |
| docs | `tools/plotting/README.md` | 親 | 節 1 つ (command example) |
| 成果物 | `docs/paper-story/figures/fig13_b10_waiting_grid_forest.{png,pdf,provenance.json}` | 親が login で生成 | 凍結物 |
| 記録 | `output/insights/2026-09-20/fig13-b10-waiting-grid/README.md`、`docs/spool/` fragment (worklog) | 親 | 一次資料・変異台帳・走記録 |

触らない: 稿 (凍結)、report の provenance JSON / report .md (tracked、凍結)、`docs/paper-story/README.md` (results 表は**ユーザー指示で触らない**。
表の「図は無い」は起草時点の記述として残る)、既存 fig1〜fig12 の bytes、他の生成器・test、`FIGURE_CONVENTIONS.md`。gate・検査・台帳の新設は scope 外 (ユーザー指示)。

## 確定済みユーザー裁定・拘束

- D95 (実装面は Codex author、親は docs のみ)。`tools/plotting/FIGURE_CONVENTIONS.md` §1〜§10 (入力からその場で再計算・不確かさ・provenance・計測機の外・fail-closed layout・実寸 fixture・実データ実走)。
- 事前登録 発効版 (commit `77b33e37d`) §3: 書けるのは「登録した 2 実装の間で待ち方の違いが throughput を動かすかを事前登録手続きで検定した」「有意な族の方向・効果量・信頼区間をこの contrast に限って限定付きで」まで。
  書けない: 機序 (脱同期だけ)、ばらつき全般の効果、直交切り分けの一般化、`binary` / 3 水準 ladder、検出力の範囲内。
- ユーザー指示 (依頼文): 区間が ±3% に収まることを「等価性の成立」と呼ばない。36 cell の個別有意差に読み替えない。右 tail 2 稿 (`2026-09-16` / `2026-09-19` 稿) と合成しない (D2157 の精神)。
- D1678 (判定は 2026-09-07 に閉じた。図は判定を改めない)。D12 (`different` は成否の宣告ではない)。D1637 (2 本目の論文と共用しない)。絶対規律 2 (`official_certification` false、採用根拠にしない)、絶対規律 7 (稿・report の bytes 不変、当時の判定と現行主張を混ぜない)。
- F36 型: 稿を `caption_source` として provenance が SHA-256 で束縛し、稿は provenance の hash を持たない (一方向)。

## 一次資料 (着手時に実測、稿 §4.1 / §4.2 と全一致)

| 資料 | path | SHA-256 |
|---|---|---|
| report provenance JSON (tracked、判定・135 record・束縛) | `output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json` | `a4390603f20fbc8fdb74c482a17ae880f292e340e79846c31f5d923d71789fca` |
| report .md (tracked) | `output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_report_978195.nqsv-23409962b76b.md` | `e237d17db4f02818ea27049165fa90da4c19adea1bc8bca9b165b73b77e8e768` |
| 稿 (caption_source、凍結) | `docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md` | `8dc6d69538c6785c0e3e56073ccc86c97e82699972265d5c521159a6cf72045a` (記録するが生成器の pin にはしない = 稿の現 SHA を provenance に写す。着地 test が現物と照合) |
| report 受領証 (repo 外) | `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/23409962b76be959bb523a0cd5a31bc1/submit-receipt.json` | `93a1cd74ce279c6c8c876a7ab60fb772b216f25cf59f4eff70d0b0e2b8b429b4` (= provenance JSON `submission.receipt_sha256`) |
| report job 結果 (repo 外) | 同 root `submissions/23409962b76be959bb523a0cd5a31bc1/job-attempts/978195.nqsv/job-result.json` | `d5d4a0ee4c503c1b4b6a811f998949f7a76434a575c4ed8d0bfad849eafd082b` |

DW-O13 (gate 入力の実在と値域、着手時に実測): `judgement.families[]` は 3 件 (workload ∈ {balanced, read-heavy, write-heavy} × shape `symmetric-modulo`)、各 `pairs` 18、
`differences` 18 値 (順序 = block-1 μ2→100、block-2、block-3 = block-major / μ-minor、records の `median_tps` からの再計算と abs 1e-12 で一致)、`raw_p` は 2^18 分母の分数
(6702 / 70 / 2 ÷ 262144)、`status` `testable`、`reasons` `[]`、`holm_p` ≤ 0.05、`outcome` `different`。`judgement.cell_effects[]` は 36 件 (3 workload × {constant, symmetric-modulo} × μ ∈ {2,5,10,25,50,100})、
key = `workload` / `shape` / `mean_us` / `effect` / `ci95_low` / `ci95_high` / `status` (全 `estimable`) / `equivalence_margin_pct` (全 3.0) / `equivalence_relation` (`inside-equivalence-range` 32、
`overlaps-equivalence-boundary` 4、他 0)。constant 18 cell は effect 0 / CI [0, 0]。symmetric-modulo 18 cell は「3 block の対相対効果 (sm/const − 1) の平均 ± 4.302652729911275 × 標本 sd / √3」で
再計算して差 0 (bit 一致)。`preregistration.spec.analysis` に `alpha` 0.05、`equivalence_margin_pct` 3.0、`confidence_interval.critical_value` 4.302652729911275 / `degrees_of_freedom` 2、
`permutation.enumeration` `all-2^18`、`holm_families` 3 件、`exposure.minimum_calls_per_cell` 10000。`records[]` 135 件、key = `workload` / `block_id` / `point` (文字列、
`none` / `adaptive` / `zero-loop` / `constant-mu<μ>` / `symmetric-modulo-mu<μ>`) / `shape` (`none`・`adaptive` は null、`zero-loop` は `constant` で `mean_us` 0 → **登録 grid の μ に無いので除外**) /
`mean_us` / `median_tps` / `throughputs` (5) / `cv` / `abort_count` / `backoff_call_count` / `correctness_certified` (全 true) / `missing` (全 false) / `unstable` (全 false) /
`official_certification` (全 false) / `execution_host` / `request_id`。top-level: `schema_version` `b10-backoff-shape-provenance/v2`、`official_certification` false、`pin` `511c953`、
`submission` = {`request_id` `978195.nqsv`, `nonce`, `phase` `report`, `receipt_sha256`, `source_commit` `2a338449b…`, `prereg_commit` `77b33e37d…`, `job_script_sha256`}。
受領証 (schema `pegasus-b10-submit-receipt/v2`) は `dry_run` false / `phase` report / `request_id` / `nonce` / `prereg_commit` / `source_commit` / `job_script_sha256` / `submitted_epoch` 1788581651 を持ち、
job 結果 (`pegasus-b10-job-result/v1`) は `driver_rc` 0 / `completed_epoch` 1788582054 / `request_id` / `nonce` / `phase` / `source_commit` を持つ。report .md には
`## Paired sign-flip permutation + Holm` 節 (3 行、`outcome=different, pairs=18, raw_p=…, holm_p=…`) と `## Cell effects and 95% paired-block intervals` 節 (36 行) がある。

## 不変条件

1. 判定・効果・区間・等価域との関係・Holm p は report provenance JSON から読み、生成器は**再計算して一致を要求するだけ**で、新しい閾値・補正・有意差・等価性検定を作らない。
2. 稿・report JSON / .md・既存 fig1〜12 の bytes 不変。新設 file 以外の実装面に触らない。
3. caption は英文・決定的で、固定文 (下の 8 文) を逐語で含み、禁句を含まない。日本語キャプション正文は figures/README.md の節に親が書き、英文 caption は provenance と同一文字列で README に逐語収録する。
4. provenance は tracked 3 file (provenance JSON・report .md = pin、稿 = caption_source、SHA 記録) と repo 外 2 file (受領証・job 結果 = pin、root 相対 path) を束縛し、`validate_repo_closure` は repo 外を読まない。
5. FIGURE_CONVENTIONS §9: 保存前の renderer-backed layout check、重なり・逸脱で 3 成果物を 1 つも出さない。§10: fixture 実寸、本物の Figure を検査へ通す、実データで実走。
6. `orchestrator/tests/test_official_perf_closure.py` の走査規則: 生成器の `if` / `while` / 三項の条件式に `perf` を含む名前 (`perf_*`、`*_perf`、`_perf_`) を置かない (records の `perf_preflight_receipt` / `performance_binary_sha256` は読まない)。
7. 既存 test の期待値を変えない。新 test file は `__main__` harness と `skiputil` を持ち、`test_plain_runner_coverage.py` の制約を満たす。
8. 稿の限定 3 / 5 / 9 / 10 / 13 / 16 を caption と README の言い方に写す (機序なし・床値判定なし・検出力なし・合成なし・成否宣告なし・等価性検定ではない)。

## (P1) 図の形 — 親の provisional 裁定 (攻撃対象)

1 行 × 3 panel (write-heavy / balanced / read-heavy)、各 panel は y = μ 6 行 (2, 5, 10, 25, 50, 100 µs; 上から下)、x = `symmetric-modulo` 対 `constant` の対相対効果 (%)、**x 範囲は 3 panel 共通**。
各行: constant 参照 cell = 0 の位置に空丸 (効果 0・区間 [0, 0] は構成上の参照)、symmetric-modulo cell = 塗り印 + 95% paired-block 区間の横線 (cap 付き)、
区間の材料である 3 block の対相対効果 = 小さい灰色の縦 tick (区間の後ろ)。等価域 ±3.0% は帯 (axvspan)、0 は縦線。`overlaps-equivalence-boundary` の 4 cell は印の形を変える (凡例で説明)。
panel 題 = 族の判定 (`outcome`、Holm p、raw p の分数表記 `n / 2^18`、対 18、18 対の和の符号)。suptitle に report request と事前登録の識別、脚注に条件 (Pegasus 48 スレッド、silo、YCSB、pin `511c953`、
`official_certification: false`、「区間が帯の内側でも等価性ではない」「cell ごとの有意差は判定しない」)。凡例 1 つ。図 1 枚で 36 cell 全部 (constant 18 は 0 の空丸として) を描く。

## 成果物の形

- provenance schema `izanagi-b10-waiting-grid-forest-figure-provenance/v1`。key: `schema`, `generated_utc`, `generator{path,sha256}`, `tracked_inputs[3]`, `external_inputs[2]`, `report{request_id,nonce,phase,submitted_epoch,completed_epoch,driver_rc,source_commit,prereg_commit,job_script_sha256}`,
  `official_certification` (false), `ccbench_pin`, `analysis{alpha,equivalence_margin_pct,critical_value,degrees_of_freedom,pairs_per_family,enumeration}`, `families[3]` (workload, shape, pairs, raw_p, raw_p_numerator_2pow18, holm_p, status, outcome, differences[18], sum_of_differences, direction),
  `cells[36]` (workload, shape, mean_us, effect, ci95_low, ci95_high, status, equivalence_relation, block_effects[3] (constant は [0,0,0])), `summary{inside,overlaps,outside,indeterminate,estimable}`, `crosschecks{…}`, `measurement_conditions`, `outputs[2]`, `artist_series`, `caption`, `reproduction{cwd,argv,command}`。
- CLI: `python3 tools/plotting/plot_b10_waiting_grid_forest.py [--repo-root PATH] [--evidence-root PATH] OUT_PREFIX` (既定 evidence root `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape`)。`fig<N>_` でない prefix は拒否。

## 分割・環境

- 段 5: Codex author 1 本 (unit worktree `.codex/worktrees/fig13-b10-unit-impl`、所有 = 生成器 + test + `probe-fig13/` scratch)。親は docs。
- 段 6: 敵対 review 2 本 (A: 過剰・削除レンズ固定 (DW-S03 型)、B: 正しさ境界・caption の限定・事前登録 §3 逸脱・等価性の読み替え)。must-fix があれば fix 1 本 → 焦点再レビュー 1 本。変異 matrix は計算ノード dispatch。
- test 実走 (焦点走・変異・受入) は計算ノード dispatch (`tools/run_tests.py`)、作図は login (計測機の外)。所在 = worklog 末尾。
- 編集面重複検査 (19:05): branch tip hit は既着地 wave の `[T-2638]` 残差記録 commit のみで fig13 / 新生成器 path に hit 0、47 worktree の未 commit 差分 0。pin 閉包: `fig13` / 生成器名 hit 0、
  変更する README 2 file の byte pin なし (着地 test は節内の caption と SHA 行だけ)。

## 言わないこと (成果物影響、DW-G05)

放置しても certified 選択・レポート・台帳の値は変わらない (図は判定の写しで、判定の入力にならない)。図が無い状態が続くと論文の結果節に図が無いだけ。
