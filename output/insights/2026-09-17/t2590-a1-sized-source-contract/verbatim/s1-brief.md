# 段 1 brief — [T-2590] + [T-2081] A-1 balanced5 sized 本走の pilot 専用分岐を一式で揃える

wave: `dev-wave-t2590-a1-sized-source-contract` / worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2590-a1-sized-source-contract` / 基準 commit = local main `1042a1bc95057fa03117d504cfa2b0fafaae60d0` (2026-09-17 00:40 JST 時点)

## 研究前進

論文 A-1 (対測定) の但し書き 1「現行の対測定契約で測り直していない」を外せる唯一の証拠は balanced5 sized 本走 (`paper-story-a1-20260901-balanced5-sized-v1`、D1262 の estimand、D1973 で policy 凍結済み) である。本走は現行 code では起動できない — 計測経路の source 契約・hydrate 入力・依存 source の staging・source binding の生成・amended build の configure argv の受理形が pilot (`…-pilot-v1`、attempt-0004) 専用に固定されている (段 3 sol の数え上げ、`output/insights/2026-09-13/t2164-a1-sized-policy/verbatim/s3-sol.md:109`、`s2-plan.md:493-496`; sized 事前登録 §7.3 も同旨)。本 wave の完了判定は「sized study が pilot と同じ amended source 契約 (canonical pin `511c9538…` + `patches/silo-backoff-fixed.patch` のみ適用) で submit → job preflight → measure → artifact consumer を通る (test/fixture で示す)」かつ「pilot の公開済み受領証 (`output/insights/2026-09-01_paper-story-a1-balanced5-pilot/{receipt,result}.json`) の検証結果が 1 bit も変わらない」。**本走は投入せず、認可 (T-1505) も出さない。**

## 確定済みユーザー裁定 (逐語は `rulings-verbatim.md`)

- D1986 項 5: 「今は認可を出さない。計測経路に残る試験運転専用の分岐を外す実装が閉じた時点で改めて諮る。」前文「各実装は名指しの変更に限定し、付随する gate・台帳・汎用化を足さない」。
- D1323 (T-2081): 「A-1 の対測定は、未コミットの変更を含む CCBench 作業ツリーを受理しない。判定の基準は commit ID が確定できるかどうかに置き、bytes 級の同一性検査は新設しない。」再凍結 (D1262) と同じ変更単位。
- D1973 却下案「本走の実行面まで同じ単位で整える — 1 箇所の限定解除では足りない。証明書と policy の凍結とは別の単位で扱う」→ 本 wave がその別単位。
- D1300: CCBench 受理集合は 5 境界 (submit / job preflight / driver / build 直前 / consumer) で要求する。実装は `ed61448f6` (2026-09-01) で v3 に着地済み。
- ユーザー引数: 対象は `orchestrator/campaign/paper_story_a1_*.py` と契約 JSON。Codex author (D95) + 変異事前登録。本題の分岐整理だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外。規律 2 を緩めない。

## scope (純増)

sized study を pilot と同じ amended source 経路に乗せるための分岐整理 4 点 + T-2081 の閉じ (既存機構が sized を覆うことの確認と記録)。それ以外 (認可、本走投入、新 gate、bytes 級検査、pilot 成果物の再公開、A-2/A-6 への一般化) は入れない。

## 親の provisional 裁定 (攻撃対象)

- (P1) `tools/pegasus/paper_story_a1_paired.sh` は scope 内。引数の列挙は `.py と契約 JSON` だが、数え上げの「hydrate 入力と staging の分岐」の実体は job script 1361〜1371 行 (staging) と 74〜81 / 450〜455 / 984〜989 行 (source 閉包) にあり、ここを揃えないと sized の measure は `--third-party-source-root` 無しで起動して 7133 行で落ちる。job script の変更は分岐条件の置換だけに限る。
- (P2) v1 契約 JSON (`paper_story_a1_source.v1.json`、sha `21477b74…`) の bytes は変えない。pilot attempt-0004 の source binding が `binding_matches` (`paper_story_a1_source.py:32-38`) で CONTRACT_SHA256 に束縛されているため、v1 を書き換えると pilot の公開済み受領証の再検証が落ちる。sized は別 file `paper_story_a1_source.v2.json` (仮称) を足し、module は study_id → (契約 path, sha256) の 2 要素表で選ぶ。`SOURCE_PATHS` も study 別 (pilot の 4 path は不変、sized は v2 契約 path + module + patch + sized 追補 README)。
- (P3) sized 契約は `attempt` を pin しない。pilot の attempt pin は「走行中の study の attempt-0004 から追補を適用した」経緯の産物で、sized には追補前の attempt が存在しない。driver の attempt 名照合 (3410-3412、7126-7128) は pilot 契約にだけ効かせる。対案「attempt-0001 を pin」は bench 前の infra 失敗 (pilot は attempt 1〜3 で経験) のたびに契約版を切る形になるので採らない。
- (P4) sized の source 条件の登録 (追補 README) を `output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md` に置き、v2 契約が `amendment` として sha で束縛する。内容は T-2397 README の source 条件 1〜5 と依存供給を sized study へ同文で適用する宣言 (docs、親が書く)。pilot の T-2397 README を sized の `amendment` に流用する案は、同 README が `study_id: …pilot-v1` / 「適用: attempt-0004」と自己限定しているので採らない。sized 事前登録 README (凍結、sha pin) は編集しない。
- (P5) T-2081 / D1323 は新規実装なし。5 境界 (`_assert_ccbench_acceptance` 2381-2420: submodule 直接の `rev-parse HEAD` + `status --porcelain --untracked-files=no`、`parent_submodule_ignore_independent`、build 直前の `SourceContext.validate` = pin + expected materialization、consumer 境界 5373) が study 非依存に sized を覆うことを test で示し、本 wave の記録で T-2081 を閉じる。commit ID の確定可能性 = 「submodule HEAD が canonical pin かつ tracked clean」+「build source は pin + 指定 patch のみの期待 materialization と一致」。bytes 級検査は足さない。
- (P6) hydrate 入力は pilot と同じ機構 (`IZANAGI_A1_THIRD_PARTY_SOURCE_ROOT` を intent の qsub 変数に載せ、submit で dir 実在、job で `$DEPENDENCY_ROOT/fetchcontent` へ複製、measure で intent と env と staged root を照合)。分岐条件を「pilot か」から「amended source 契約を持つ study か (pilot / sized)」へ置換する。
- (P7) 実装単位は Codex author 1 本 (driver + source module + v2 契約 JSON + job script + tests は 1 つの整合単位)。並列分割はしない。

## 不変条件

- I1: `paper_story_a1_source.v1.json`、`patches/silo-backoff-fixed.patch`、`output/insights/2026-09-11/t2397-a1-source-amendment/README.md`、pilot policy/prereg、sized policy (`a6228bcd…`)/prereg、sizing 証明書の bytes は不変。
- I2: pilot の `_source_relative_paths` の結果 (10 + 4 path、順序込み) と `binding_matches` の判定は不変。`test_paper_story_a1_job_contract.py:421-449` の既存 assert を弱めない。
- I3: `_trace0_commands_match` の受理形は、amended source のとき `-S <amended root>` + FETCHCONTENT 4 token を要求する既存形のまま。sized で受理形を増やさない (DW-O13: 既存 exact 述語の改訂で受理形を増やす = 新設)。
- I4: verifier / anomaly / condition gate / `formal=false` / `promotion_prohibited=true` に触れない。
- I5: 既存 test の削除・skip・xfail・期待値変更をしない (test 関数名集合は基底 ⊆ 現行)。

## 成果物の形

code + tests (Codex author) / `paper_story_a1_source.v2.json` (Codex author、親が sha を検算) / sized 追補 README (親、docs) / insight dir `output/insights/2026-09-17/t2590-a1-sized-source-contract/` (逐語・変異台帳) / spool fragment (worklog・decisions)。本走・認可なし。受入は `tools/dev_wave_wait.py acceptance`。変異 matrix は段 4 で登録。

## 変更面 (実アンカー、HEAD 1042a1bc9)

| file | 行 | 現状 (pilot 限定) |
|---|---|---|
| `orchestrator/campaign/paper_story_a1_source.py` | 11-18 | `CONTRACT_PATH` / `CONTRACT_SHA256` / `SOURCE_PATHS` が単一値 (pilot v1) |
| 同 | 21-28 `load_contract` | 契約 JSON の 4 束縛 (patch/policy/preregistration/amendment) を検算。study 引数なし |
| 同 | 32-38 `binding_matches` | v1 の 3 digest だけ照合 |
| 同 | 44-58 `SourceContext.__init__` | `configuration="a1-attempt-0004"` (ラベルのみ、hash 原像ではない) |
| 同 | 75-85 `materialized` | `load_contract(repo_root)` 固定 |
| `orchestrator/campaign/paper_story_a1_paired.py` | 2243-2244 `_source_relative_paths` | pilot のときだけ `a1_source.SOURCE_PATHS` を足す |
| 同 | 2636-2639 `_v3_group_intent` | pilot attempt-0004 のときだけ契約検算 + hydrate 必須 |
| 同 | 3409-3415 `run_submit` | pilot のときだけ attempt 名照合 + hydrate dir 実在 |
| 同 | 7126-7134 `run_measurement` | 無条件に `study_id == 契約 study_id and attempt == 契約 attempt` を要求 (エラー文 `A1 source amendment requires pilot attempt-0004`)、hydrate env / staged root 照合 |
| 同 | 4860 `_validate_source_binding_for_paths` | `CONTRACT_PATH in relative_paths` で v1 固定の `binding_matches` |
| 同 | 5219-5230 (consumer) | `CONTRACT_PATH in files` で amended admission 検査を発火 |
| 同 | 4979-5060 `_trace0_commands_match` | `amended_source_root` 有無で configure argv 長と FETCHCONTENT token を要求 (受理形は不変) |
| 同 | 8565-8573 | pilot だけ `sizing-pilot.json` を生成 (sized は生成しない、変更不要) |
| `tools/pegasus/paper_story_a1_paired.sh` | 74-81 / 450-455 / 984-989 | pilot policy path 一致のときだけ source 閉包へ 4 path 追加 (3 箇所、test は `count == 3` を pin) |
| 同 | 1361-1371 | pilot policy path 一致のときだけ hydrate staging + `--third-party-source-root` |
| `orchestrator/campaign/pipeline.py` | 1096-1102 | `SourceContext` 型検査 (変更不要) |
| `orchestrator/tests/test_paper_story_a1_job_contract.py` | 421-449, 3190-3215 | source 閉包・submit fixture が pilot 固定 |
| `orchestrator/tests/test_paper_story_a1_paired.py` | 4775-4790 | `binding_matches` の test |

## 模擬 / 実の差

- 段 1 で親が実測したのは code 読解と sha 逆引き (DW-O09: 変更前 sha で `output/` を逆引き → `paper_story_a1_source.py` の sha `0ba074…` が pilot 受領証の `working_sha256` として記録されているが、これは歴史記録であり live pin ではない。`binding_matches` は module の sha を照合しない)。baseline 焦点走 (3 test file) は背景で実測中、結果は段 2 前に brief 末尾へ追記する。
- 計算ノードでの実 build / hydrate は本 wave では行わない (本走を投入しないため)。sized の submit → measure の通しは test fixture (既存 pilot 用 fixture の sized 版) で示す。実機の生死は「pilot が同じ経路で attempt-0004 を完走した」事実に依拠する。

## 既存被覆 (純増の確認)

D1300 / D1323 / D1973 / D1986 項 5 / T-2397 README / sized 事前登録 §7.3 を検索した。failures.md に A-1 source 追補型の F は無し。純増は「sized への対称化」と「T-2081 の閉じの記録」だけ。

## 段 1 末尾追記 — baseline 実測

- 3 test file (`test_paper_story_a1_job_contract.py`、`test_paper_story_a1_paired.py`、`test_paper_story_a1_balanced_sizing.py`) の焦点走: **462 passed / rc=0 / 135.72 秒** (login node、load 42、HEAD 1042a1bc9、非受入形)。log = `/home/SFC/tanab/.claude/jobs/8e3a0dbd/tmp/baseline-a1.log`。
