# [T-2482] campaign verifier epoch の保証文言を現物の被覆範囲へ合わせた — 63 本目は import 先ではなく subprocess 委譲先だった

- 日付: 2026-09-16
- wave: dev-wave-t2482-scope-wording (branch `worktree-dev-wave-t2482-scope-wording`)
- 起点: ユーザー直接指示 (2026-09-16、`/dev-wave` 引数)。「文言修正であって verifier の対象拡大ではない。
  被覆を広げる仕事へ変えない。仮想リスク向けの gate・検査・台帳・一般化は scope 外」。
  起票は `docs/archive/worklog-phase3-0909-1383.md` の [T-2482]。
- 正本: D1651 (文言が持つべき要素)、D1884 (閉包が閉じるまで名乗りを広げない)、
  D1896 (本 wave のユーザー指示が上書き)、設計判断は本 wave の decisions fragment。
- 基準: local main `e667c8c139004221723ee223b7d8f09fba5f9be1` で着手、段 4 前に
  `a1b40608cbbdefb62846e6224313d12c2bce9dae` へ ff-only。
- 実装 commit: `29f463719` (段 5)、`bfc53cc95` (段 6 fix)。
- authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾)。

## 1. 何を直したか

`orchestrator/campaign/artifact_admission.py` の 2 定数と、それを独立 literal で照合する test 2 か所
(`orchestrator/tests/test_artifact_admission.py` の `test_real_e0_is_rejected_only_by_certified_epoch_gate`、
`orchestrator/tests/test_s1_9pair_figure_provenance.py` の `CURRENT_E0_EPOCH`)。

| 定数 | 旧 | 新 |
|---|---|---|
| `CAMPAIGN_VERIFIER_EPOCH_SCOPE` | curated exact 62 path; 2026-09-01 の静的 import 発見集合 131 module のうち、既存 24、明示 import 先 36、実行時 package 初期化 2 を収載; source-import 推移閉包ではない | curated exact 63 path; source-import 推移閉包ではない; 発見集合は収載 tuple を起点に静的 import と package 初期化を辿った集合であり、2026-09-16 (a1b40608c) の実測では 162 module、うち収載 63 |
| `CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE` | 同発見集合の未収載 69 module、(verifier 3 path)、および data/schema、生成物、subprocess、… を含む非 import 委譲は本 map の外であり、完全性を主張しない | 同実測の発見集合の未収載 99 module、同発見集合に入らない module、(verifier 3 path)、および data/schema、生成物、subprocess、… を含む非 import 委譲は本 map の外であり (収載 path の source bytes は委譲先であっても本 map の内)、完全性を主張しない |

`CONTRACT_LOADER_RELATIVE_PATHS`、E1 の導出 (domain + path + blob だけで文言は入らない)、
`CampaignVerifierEpoch.__post_init__` の一致検査、受理述語、`PRE_T733_*`、`FROZEN_E0_EPOCH`、
docstring は変えていない。

## 2. 現物の被覆範囲 (実測)

T-2344 の probe 原本 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-reachability/probe_closure_v2.py`
(sha256 `e4843f31d68071568752140830e08c6791c45c16f427096497d2415571570fbf`、
`output/insights/2026-09-09/t2344-closure-reachability/verbatim/probe-closure.md` のコード部と bit 一致) を
新規に書かずに実行した。出力は本 dir の `closure-*.json`。

| commit | 収載 | 発見集合 | 未収載 | 1 段展開 | 備考 |
|---|---|---|---|---|---|
| `2143a49c0` (T-2344 測定 commit) | 63 | 140 | 77 | 81 | T-2344 の記録と一致 (正例対照) |
| `e667c8c13` (着手時 main) | 63 | 162 | 99 | 83 | 2143a49c0 との差は +22 / -0 |
| `a1b40608c` (取り込み後 base) | 63 | 162 | 99 | 83 | e667c8c13 と発見集合が完全一致 |

- 収載 tuple が不変でも発見集合は 1 週間で 140 → 162 へ動いた。**食い違いの源は収載の段階実装だけではなく、
  収載 member 側の import の変化にもある。** これが D1896 (「D1884 の実装単位で同時に直す」) の前提に
  無かった新事実であり、日付・commit 付きの測定事実として書く理由である。
- `orchestrator/verifier/__main__.py`・`cli.py`・`orchestrator/verify.py` は発見集合の外 (除外欄の別記は
  二重計上ではない)。`s8b_oracle_report.py` も外。`autonomous_trial_completeness.py` は 09-09 には外だったが
  09-16 には内 (index 15)。発行器の名前は snapshot 依存なので文言へ書かない。
- **63 本目 `orchestrator/campaign/verify_fanout_worker.py` は import 先ではない。** 発見集合 162 の
  `edges` にこの file を target に持つ member は 0 本。`orchestrator/campaign/pipeline.py:836` が
  ssh 経由 `python -B -m orchestrator.campaign.verify_fanout_worker` で起動する subprocess 委譲先を、
  T-2429 (`2a9ba783f`、2026-09-08) が明示収載した。旧文言の「subprocess … を含む非 import 委譲は本 map の外」は
  この 1 本について事実と食い違っていた。旧文言の内訳 (24 / 36 / 2) はこの 1 本を分類できない。

## 3. 文言が受理・digest・記録に効く経路 (実測)

- E1 preimage: `_CAMPAIGN_VERIFIER_EPOCH_DOMAIN` + tuple 順の path + blob (artifact_admission.py:1056-1064
  付近)。scope 文字列は含まれず、lock にも記録されない (読み取り時の既定値)。
- 完全一致で照合する consumer: `autonomous_trial_completeness._require_compatible_layer3_epoch`
  (記録済み layer3 report の epoch を現行 validator の値と比較)。照合対象になる記録実物は、repo の
  `output/` (insight 除く) で `backoff-sweep-silo-read-heavy-sweep-6f169f90/reports/layer3_report.json` の 1 本
  (非 certifying・E0・2026-09-16 保存・読む test なし)。外部実測定 root 23 dir の JSON に scope 欄を持つものは 0 本。
- `s8b_oracle_artifacts.validate_campaign_verifier_epochs` は scope を非空文字列としか検査しない。
- **親の一般化を子が反証した 2 点 (記録のみ):** (a) `artifact_admission.py` 自身が収載 path なので、
  新規 lock の E1 は本変更で変わる。記録済み map から再導出する E1 は不変。(b) 同 file 全 bytes の sha256 が
  admission receipt の `validator.sha256` (artifact_admission.py:1249 → :329) と B-4 projection hash
  (p3_b4_closed_critic.py:636) に入り、completeness / B-4 検証が現行値と照合する。いずれも D170 (d) と
  B-4 事前登録本文 (「閉包 member の bytes が変われば 3 値は同時に無効…書き直す」、欄は未記入) が既に
  限界として記す既知の性質で、本 wave 固有ではない。互換機構は scope 外。

## 4. 段 3・段 6 の所見と裁定

- 段 3 レンズ A (正しさ境界)・レンズ B (整合と実効性): 独立に同じ must-fix (非 import 委譲の一括除外が
  収載済み worker と矛盾) を出した。親の追加実測と一致。should-fix は E1 不変の限定、bytes hash 経路の反証、
  bytes pin の限定。nit は日付の係り先、発行器名の省略、歴史/現行の文言同一が判定に効かないこと。
  裁定は `verbatim/s4-ruling.md`。親の (P3) (内訳を残す) は撤回。
- 段 6 レビュー A: 所見ゼロ。レビュー B: should-fix 1 (「除く」の係り先が一意でない) → 採用、fix 子 1 本。
  焦点再レビューの対応表は `verbatim/s6-focus.md`。

## 5. 変異台帳

harness: `tools/mutation_harness.py --runner-mode dispatch --detached` (wave worktree 直接、固定 HEAD `bfc53cc95`)、
runner argv: `python3 tools/run_tests.py orchestrator/tests/test_artifact_admission.py orchestrator/tests/test_s8b_oracle_report.py orchestrator/tests/test_s1_9pair_figure_provenance.py -q -rf --force-dispatch`。
spec・台帳は本 dir の `mutation-spec-*.json` / `mutation-*.json`。

**本 wave の変異は kill ではなく診断感度 pin である (DW-M03 / M08)。** 差分は説明文字列だけで受理集合を
変えないので、赤は「独立 literal との不一致」という診断シグナルの pin として記録する。

### probe (spec sha256 `94df1652…`、全件 SURVIVED 登録で観測 node を収集)

baseline PASSED (466 passed)。

| # | 変異 | 観測 | node |
|---|---|---|---|
| M0 | `artifact_admission.py` の comment 1 語だけ (drift 対照) | **SURVIVED、赤 0** | — |
| M1 | SCOPE `63 path` → `62 path` | 4 | A::test_real_e0_is_rejected_only_by_certified_epoch_gate、S::test_p1_…、S::test_p3_…、S::test_p8_… |
| M2 | SCOPE `; source-import 推移閉包ではない` を削除 | 4 | 同上 |
| M3 | EXCLUDED `未収載 99` → `未収載 69` | 4 | 同上 |
| M4 | EXCLUDED 括弧句 (source bytes の例外) を削除 | 4 | 同上 |
| M5 | EXCLUDED `、完全性を主張しない` を削除 | 4 | 同上 |
| M6 | test A の literal `162` → `161` | 1 | A::test_real_e0_… |
| M7 | test S の literal `同発見集合に入らない module、` を削除 | 3 | S::test_p1_…、S::test_p3_…、S::test_p8_… |

(A = `test_artifact_admission.py`、S = `test_s1_9pair_figure_provenance.py`)

- **F358 の核は空。** M0 が赤 0 なので、この焦点集合には closure member の bytes 変化だけで落ちる node が無い。
  よって delta = 観測そのもので、delta が空の変異は 0 本。M0 は harness の SURVIVED 検出の正例でもある。
- 帰属: 赤の理由は `test_artifact_admission.py:1371` (identity_scope) / `:1376` (excluded_scope) の
  AssertionError と、`test_s1_9pair_figure_provenance.py:155` の `ProvenanceError: HISTORICAL_RAW E0 differs`
  (`:384-385` の `CURRENT_E0_EPOCH` 辞書完全一致) だけ。`test_output_tail` で確認した。
- 観測は段 2 の静的予測 (M1〜M5 = 4、M6 = 1、M7 = 3) と完全一致。

### final (spec sha256 `be08f8c97ab7a3528aa57b16c3913bec67ddc09339ff7ef723514df084499400`、観測 node を期待へ登録)

固定 HEAD `bfc53cc95`、runner sha256 `d339cae4…`、tool sha256 `1dbf1b60…`。
**baseline PASSED、M0 SURVIVED (期待一致)、M1〜M7 7/7 KILLED、MISMATCH 0、期待 node 完全一致。**
probe と final の観測 node 集合は同一。M1〜M7 の `failed_nodes` の交差 (素朴な核) は 0、
M0 の観測 (真の drift 核) も 0 で、F358 の差し引き後も 7 本すべての delta が非空である。

### M4 の erratum と補走 M4x (spec sha256 `d80089c84cbe72df2bd0ca37c571c64691d9128cf03f79b7281609c58e5fe088`)

段 6 の焦点再レビューが指摘した。probe / final の M4 は追補 1 の登録 (先頭空白 + 括弧句だけを削除) と
違い、括弧句 + 読点を削除して先頭空白を残す形で走った (連結結果 `…本 map の外であり 完全性を主張しない`)。
fix 子が文字列 literal を 2 行に分けたため、登録どおりの anchor が source 上で行境界を跨ぎ、preflight が
anchor count=0 で止まったのを親が 1 行に閉じた anchor へ再照準したのが原因。意味 (source bytes の例外句を
落とす) と赤の理由 (literal 不一致) は同じだが、登録どおりの単独変異の実測ではないので erratum として残す。
行境界を跨ぐ anchor で登録どおりの M4x (連結結果 `…本 map の外であり、完全性を主張しない`) を
KILLED 期待 (M3/M5 と同じ 4 node) で補走した。

結果 (`mutation-m4x.json`、固定 HEAD `bfc53cc95`): **baseline PASSED、M4x KILLED、期待 4 node と完全一致**。
assertion の diff は `-  map の外であり (収載 path の source bytes は委譲先であっても本 map の内)、完全性を主張しない` /
`+  map の外であり、完全性を主張しない` で、登録どおりの変異が走ったことを本文で確認した。

### 変異の総括

| # | 変異 | 登録 | 結果 |
|---|---|---|---|
| M0 | comment だけ (drift 対照) | SURVIVED | SURVIVED (赤 0) |
| M1 | SCOPE 63 → 62 | KILLED 4 | KILLED 4 |
| M2 | SCOPE 非推移閉包句を削除 | KILLED 4 | KILLED 4 |
| M3 | EXCLUDED 99 → 69 | KILLED 4 | KILLED 4 |
| M4 | EXCLUDED 括弧句 + 読点を削除 (erratum: 登録と差) | KILLED 4 | KILLED 4 |
| M4x | EXCLUDED 空白 + 括弧句を削除 (登録どおり) | KILLED 4 | KILLED 4 |
| M5 | EXCLUDED 完全性非主張句を削除 | KILLED 4 | KILLED 4 |
| M6 | test A literal 162 → 161 | KILLED 1 | KILLED 1 |
| M7 | test S literal 集合外句を削除 | KILLED 3 | KILLED 3 |

計算ノード job: 焦点走 1 + probe 9 + final 9 + M4x 2 = 21。

## 6. 実測したこと / していないこと

実測した:
- 閉包寸法 3 commit (上表)。
- 焦点走 3 file (`29f463719`、Pegasus job 1633): 466 passed / 赤 0。
- 変異 probe / final (上表)。
- 全史 provenance 監査: 各 commit 後に rc=0、新規違反なし。

していない・主張しない:
- **被覆を広げていない。** 収載 tuple は 63 のまま。D1884 の段階実装は本 wave の対象外。
- **文言が将来も正しいとは主張しない。** 発見集合の数値は 2026-09-16 (a1b40608c) の測定事実であり、
  次の import 変化で「その時点の値」になる。日付と commit を書いたのはそのためである。
- **file bytes の hash 束縛 (validator sha256・B-4 projection hash・新規 lock の E1) の互換性は扱っていない。**
  D170 (d) と B-4 事前登録本文が既に限界として記す。記録済み成果物は書き換えていない (規律 7)。
- 受入全走は記録 commit を含む最終 tip へ投入し、結果は受領証 (`dev-wave-jobs/dev-wave-t2482-scope-wording/`)
  を正本とする。本文に件数を書かない。

## 7. 一次資料

| path | 内容 |
|---|---|
| `closure-head-e667c8c13.json` / `closure-head-a1b40608c.json` / `closure-control-2143a49c0.json` | 閉包寸法の実測 (probe 原本の出力) |
| `mutation-spec-probe.json` / `mutation-probe.json` | probe の spec と台帳 |
| `mutation-spec-final.json` / `mutation-final.json` | final の spec と台帳 |
| `verbatim/s1-brief.md` / `verbatim/s1-evidence.md` | 親 brief と実測記録 |
| `verbatim/s2-plan.md` | 段 2 plan (codex) |
| `verbatim/s3-lensA.md` / `verbatim/s3-lensB.md` | 段 3 敵対相談 |

`verbatim/s3-lensA.md` は可逆最小正規化を施した (DW-S07)。原文は 11 行 (39, 40, 43, 44, 47, 48, 51, 52, 55, 56, 72)
の行末に Markdown の hard break (半角空白 2 つ) を持ち `git diff --check` に抵触したため、行末の空白だけを
除去した。可視文字は不変。原文 sha256 `9e49dd75927261fae32b8d5f1e98e2f5eee8885c22bac51870881511a06f3590`
(11073 bytes)、正規化後 sha256 `d4e5c419b1799537dd2400c97fe338cdb2c75ab4cccb028454c025bc1d5d847d` (11051 bytes)。
復元は上記 11 行の行末に半角空白 2 つを付ける。原文は
`/home/SFC/tanab/.claude/jobs/a16ed969/tmp/codex-artifacts/dev-wave-t2482-scope-wording/stage3-lensA.md` と
codex launcher の receipt (`output_sha256`) に残る。
| `verbatim/s4-ruling.md` | 段 4 裁定・plan v2・追補 1 |
| `verbatim/s5-author.md` | 段 5 実装子の報告 |
| `verbatim/s6-reviewA.md` / `verbatim/s6-reviewB.md` / `verbatim/s6-fix1.md` / `verbatim/s6-focus.md` | 段 6 |
