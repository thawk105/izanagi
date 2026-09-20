# [T-2810] 凍結 v2 g1 の launch validator を official 成果物の現物形へ整合する — journal allowlist の追随と段階 6 lineage の改訂 (2026-09-20)

wave `dev-wave-t2810-g1-launch-validation`、着手時 local main `482f19b88` → 編集前に 2 回 ff-only で `800178b39` へ (main はその後も進み、受入の post-claim merge で揃える)。
専用 handoff は repo 外 (`/home/SFC/tanab/.claude/jobs/25fa5bc0/tmp/handoff-t2810.md`)、wave artifact dir は
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2810-g1-launch-validation/` (逐語・evidence・codex 成果物・変異台帳の原本、本 README の `verbatim/` `evidence/` `mutation/` はその写し)。
依頼の逐語は `verbatim/T-2810-origin.md`。前提資料は [T-2724] の一次資料 `output/insights/2026-09-20/t2724-ax-delegated/README.md` §5。

## 1. 入力と出所

| 対象 | 実体 | 出所 |
|---|---|---|
| validator | `orchestrator/campaign/s8b_ratified_freeze.py` の `_JOURNAL_KEYS` / `_validate_journal` / `_launch_validate` 段階 6 | 現物 (base `800178b39`) |
| official run | `output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` (journal 213 record、cert、manifest、result) | 現物、導入 commit X1' `cc82edc8c` (`git log --diff-filter=A`) |
| 世代 G | `32ba8cae4` (G^ = X1'、世代文書 1 file だけを導入) | 現物 |
| A / X | `a3bf67a8c` / `70e87c9c9` (D2180) | 現物 |
| producer | `s8b_floor_campaign.py` の `campaign-start` (6548 行付近) と `reservation-preflight` (7620 行付近)、`floor_liveness.py` の `_RESERVATION_BINDING_KEYS` | 現物 |
| 裁定 | D2077 (一方向順序)、D2120 項 2、D2180、D2184 (pin 前進の波及) | decisions |

## 2. brief 前の前提実測で判明した新事実 (N1〜N4)

- **N1 (T-2304 の帰結):** 着手時 main (`482f19b88`、ccbench pin `e9e477ca`、policy epoch `db6bc9ea…`) の live P3 (g1 path、`evidence/p3-before-g1.json`) は
  `v2-execution: launch-validate: [manifest-invalid] binaries[rr20::backoff_fixed_best] admission receipt が不正: receipt admission policy が現行 policy と不一致`
  で **journal 検査より手前 (段階 4 の manifest 検査) で止まる**。一次資料 §5 の `journal-state-invalid` は T-2304 land 前の観測。D2184 は live 経路へ
  `expected_policy=None` を入れないと決めており (規律 2)、新 main への移行は [T-2812]。本 wave は policy 照合を触らない。
- **N2:** journal の不整合は `reservation-preflight` (現物 12 key = producer の binding 付き形) だけでなく、**`campaign-start` の binding 2 key
  (`pbs_jobid` / `submission_nonce`) も** `_JOURNAL_KEYS` (15 key exact) と不一致 (`evidence/journal-keys-probe.txt`)。producer は両 event とも
  `external_checkpoint_binding` の有無で 2 形を書く。
- **N3:** journal + 段階 6 を一時変異 (DW-O19、`git checkout --` で復元、sha256 一致) して policy 照合なしの正規経路 `reverify_published_freeze` を実 repo に走らせると、
  段階 4 semantic・5 binding・6 lineage・7 exemption を通過し **段階 8 の full scan で `closure-hit-mismatch`** (rr80 未申告 hit =
  `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`、X2 で main に載った未発効候補、世代文書と同 bytes) (`evidence/reverify-probe-journal-stage6-mutated.json`)。
  exact exemption (`_active_chain_exempt_exact`) は V1・世代文書・approval・pointer の 4 path だけで、候補 path は runbook §3 W-3 のとおり走査除外ではない。
  validator の修復では解けない chain 成果物側の問題 → 依頼の「別の不整合が出たら記録して止める」に当たる (§8)。
- **N4:** 現物 topology は cert C = result 導入 = X1' = G^。一次資料 §5 の α 文言「C < 導入 < G」を厳密に読むと現物を満たさず、現物に合う述語は
  C ≤ i ≤ G (同一を含む祖先関係)。

## 3. 裁定 (段 4、`verbatim/s4-adjudication.md`)

- 択一: **α** (段階 6 を「各 artifact の一意・非 merge 導入 i について C ≤ i ≤ G」+「世代文書 path の導入集合 == {G}」へ) を採る。
  β (G を result と同 commit で作り直す) は D2120 項 2 (b) の再裁定が要り、γ (導入条件を課さない) は受理集合を最も広げる。
  相談 B の第 4 案 δ (`i == frozen_at_head`) は独立 fixture の `frozen_at_head` が v1 由来で launch core は V1a を検査しないため fixture 全面変更が要り、
  D2077 が要求しない保証 (全 closure の初導入 = captured HEAD) を課すので採らない。
- 相談 A / B の所見はすべて real・採用: A-1 (`reservation-preflight` は任意・高々 1 件・campaign より前)、A-2 (旧 checkout への一般化を書かない)、
  B-1 (上限 i ≤ G は段階 3 の G-tree 実在 + 一意導入から従う重複検査、独立保証に数えない)、B-2 (受理集合の一般化 — 現物 i=C だけでなく中間 commit・
  分岐合流も受理 — を明示して決める)、B-3 (効能を「validator の互換性修復 + 新 main の historical reverify が段階 8 に到達」に限定)、B-4〜B-6 (should)。
- 受理集合の変化 (明示):

| 対象 | 変更前 | 変更後 | 保たれる制約 |
|---|---|---|---|
| journal `reservation-preflight` | 未知 event として拒否 | base 10 key (+ binding 2 key)、任意・高々 1 件・`campaign-start` より前 | 型: `formula` 非空 str、`shared_dependency_prebuild` bool、7 数値 field は int > 0 (bool 拒否) |
| journal `campaign-start` の binding | exact 15 key で拒否 | binding 2 key を optional に受理 (両 key 揃い、非空 str) | claim 状態と値は `reservation-preflight` と一致 (片側 claim・値不一致は拒否)。binding は記録内の整合情報で PBS job の外部認証ではない |
| 段階 6 result / measurement_closure の導入 | 導入集合 == {G} (全 artifact が G で同時初導入、C < i) | 各 path の一意・非 merge 導入 i について C ≤ i ≤ G (DAG 上の祖先関係、同一を含む)。現物 (i = C = G^)、fixture (i = G)、中間 commit、C 後に分岐して G 前に合流する形を受理 | 履歴不変 bytes (`_immutable_introductions`)、一意導入、G/H/worktree の bytes・mode、raw hash・semantic・binding・scan、段階 7 の active chain との `generation_commit` 一致 |
| 段階 6 世代文書 path | (検査なし、G 偽装は result 導入 == {G} が担っていた) | 導入集合 == {G} (cause `generation-introduction`、既存負例の期待不変) | — |
| cert C・policy 照合・scan 除外・他 event の集合 | — | 不変 | — |

## 4. 実装 (段 5 Codex author `verbatim/s5-author.md`、統合 commit `dc5b0f39b`、fix1 `0d943f9cb`、fix2 `083a45ee9`)

- production `s8b_ratified_freeze.py` +99/−10 (+ fix1 docstring 6 行): `_JOURNAL_BINDING_KEYS`、`_JOURNAL_KEYS["reservation-preflight"]`、`_validate_journal` の
  binding 拡張・型・件数・順序・claim・値一致、`_assert_artifact_introduction_interval` (捕捉済み graph と full OID だけ、HEAD 再解決なし)、世代文書導入 {G}、
  docstring の保証境界。cause = `journal-binding-type` / `reservation-preflight-type` / `reservation-preflight-count` / `reservation-preflight-order` /
  `journal-binding-claim` / `journal-binding-mismatch` / `artifact-introduction-merge` / `artifact-introduction-before-cert` / `artifact-introduction-outside-generation` /
  `generation-introduction`。
- test `test_s8b_ratified_verify.py` +309/−3: 独立 fixture に `artifacts_at_certificate` option (cert と run artifacts を同じ C に、G は世代文書だけ)、新規 test 17 関数 /
  63 ケース + helper 5 関数 (正例 4、journal 負例 51、実 Git DAG での lineage 負例 3 (base 導入 / merge 導入 / 複数導入)、区間の一般化正例 2 (中間・分岐合流)、
  独立 fixture の G 偽装、helper 単体の上限 (重複検査の単体試験と明記))。既存 test の期待値は不変 (wrong_g=A の `generation-introduction`、C=G の `cert-lineage`)。
- `test_s8b_oracle_driver.py` +7/−5: `_ACTIVATED_G1_REFUSALS` の第 2 要素を N1 の live 真値へ (第 1 要素 = layer-2 hit は不変)、comment。
  T-2304 (pin 前進) の統合時に本来追随すべきだった held 真値を本 wave で補完した (held node は受入で走らないので赤にならず、T-2304 wave は気づいていない)。
- 段 6 レビュー 2 本 (`verbatim/s6-review-A.md` / `s6-review-B.md`): **must-fix 0 / GO ×2**。RA-1 (should、M12 は受理→拒否の kill ではなく拒否段階の契約検出、
  M4 の独立 killer は `both` に限定 → 変異台帳の別枠記録)、RA-2 = RB-3 (nit、docstring → fix1)、RB-1 (直積 parametrize の縮約は任意 → 維持)、RB-2 (記録の正確化 → 本 README)、
  RB-4 (comment の経緯は維持可 → 維持)。
- **fix2 = 段 4 追補 1 (`verbatim/s4-addendum-1.md`、`verbatim/s6-fix2.md`):** 焦点走 1 (統合 commit、10 file) の赤 1 件 = 既存
  `test_generation_two_rejected_before_artifact_io` (g2 の RatifiedFreeze の `generation_number` だけを 1 に射影して「generation-scope 以外の gate は全 green」を pin) が、
  裁定 §2-2 項 3 の「世代文書 path を `_gen_path(ratified.generation_number)` から引く」で g1 の文書の導入を g2 の G と照合して赤になった (本差分に帰属、既存 test の期待は
  誤りでない)。追補 1: path は G 自身が追加した path (`_added_paths` + `_GEN_RE`) からちょうど 1 つ選び、その導入集合 == {G}。`generation_number` と path の世代番号の一致は
  要求しない (段階 2・段階 7 が担う)。G が merge なら追加集合が空で 0 個 → 拒否 (git の `diff-tree -r <merge>` が空になることは焦点再レビューが実 merge commit で確認)。
  fix2 +10/−1 行、production の他の箇所・test は不変。
- 焦点再レビュー 1 本 (`verbatim/s6-focus-1.md`、DW-O16): 所見対応表 = RA-2/RB-3/RB-1/RB-4/追補 1 closed、RA-1/RB-2 partial (記録側で対応 = 本 README §6.2 / §4)、
  regressed 0、新所見 0、**GO**。派生値 (焦点走の件数・fix 行数・統合 commit の行数・実装子報告の数値・trailer) を原データから再計算して一致。

## 5. 実 repo の実測 (統合 commit 後、無変異、login node、`evidence/`)

| # | 経路 | 結果 | 証明範囲 |
|---|---|---|---|
| (e) | `load_ratified_freeze(root)` | generation 1、sha `7e1114…`、G `32ba8cae4` | 批准 loader は成功 (T-2724 と同じ) |
| (a) | `reverify_published_freeze` (policy 照合なしの正規 public 経路、`_resolve_historical_contract_sha256`) | `closure-hit-mismatch` (rr80 未申告 = 候補 path)、75.8 s | **段階 4 semantic・5 binding・6 lineage・7 exemption を通過して段階 8 に到達**。歴史 reverify の成功ではない (候補 hit で止まる、rr20 側は未到達) |
| (b) | `launch_validate` (live) | `manifest-invalid` / `binary-admission` (現行 policy 不一致)、0.3 s | D2184 のとおり段階 4 で止まる。journal / 段階 6 には到達しない |
| (c) | runbook §2 P3 gate-check、g1 path | rc=2、`allowed: false`、拒否 2 件 = layer-2 hit + (b) の文字列 | 更新後 `_ACTIVATED_G1_REFUSALS` と集合 exact 一致 (`compare_refusals.py`)。held checks 3 件は不変 |
| (c') | 同、v1 path | rc=2、既知 4 件 | T-2724 の `after-v1.json` と集合 exact 一致 (不変) |
| (d) | `assert_g1_floor_selection_identity` | None (0.02 s) | live 経路だけが持つ選択 identity 検査は通る |

(a) の時間は login node の値で一般化しない。

**fix2 後の再実測 (HEAD `083a45ee9`、`evidence/reverify-after-fix2.json`、`p3-after-fix2-g1.json`):** (e) loader 成功 (activation_head `083a45ee9`)、
(a) `closure-hit-mismatch` (同じ候補 path、92.2 s)、(b) `manifest-invalid` (0.27 s)、(c) rc=2、拒否 2 件が更新後 `_ACTIVATED_G1_REFUSALS` と集合 exact 一致 —
統合 commit 後と同じ (fix2 は段階 6 の世代文書検査だけを変え、現物 G は世代文書 1 file を追加する commit なので観測は変わらない)。

## 6. 検査

### 6.1 焦点走 (計算ノード dispatch、`tools/run_tests.py --force-dispatch`、所要は runner の報告時間)

| 走 | tip | 対象 | 結果 |
|---|---|---|---|
| 焦点走 1 (`focus-impl-1`、request 13500.nqsv) | 統合 commit `dc5b0f39b` | 10 file (`test_s8b_ratified_verify`、`test_s8b_oracle_driver`、`test_s8b_binding_driftguards`、`test_s8b_terminal_evidence`、`test_s8c_preregistration_invariant`、`test_s8c_preregistration_predicates`、`test_s8b_ratified_freeze`、`test_s8b_gate_core_exact_launch_validated`、`test_plain_runner_coverage`、`test_pytest_collection_config`) | 974 passed / 13 skipped / **1 failed** (`test_generation_two_rejected_before_artifact_io`、本差分に帰属 → 追補 1 / fix2)、249.8 s |
| 焦点走 2 (`focus-fix2-1`、13525.nqsv) | fix2 `083a45ee9` | 17 file = 上の 10 + DW-O26 の consumer 7 (`test_official_perf_closure`、`test_pegasus_floor_tools`、`test_s8b_holdout_admission`、`test_s8b_oracle_judge`、`test_s8b_oracle_report`、`test_s8b_verdict`、`test_t080_freeze_migration`) | **1876 passed / 13 skipped / 0 failed**、245.6 s (焦点走 1 の集合を包含、赤 1 件は解消) |
| held 診断走 (`focus-held-1`、13527.nqsv、`IZANAGI_RUN_GROWTH_HELD_TESTS=explicit-user-command`、hold 台帳は不変) | fix2 `083a45ee9` | held 6 node (`test_s8b_oracle_driver` 4 + `test_s8b_binding_driftguards` 2、実 repo を root) + tmp repo 2 + `-k` で一致した 1 | **9 passed / 0 failed**、80.8 s |

13 skipped は既存の growth hold 由来。実装子 (sandbox) の pytest は新 test 64 件だけ緑で、既存回帰は socket 制約で未実走だった (`verbatim/s5-author.md`) — 親の焦点走が受入証拠。

### 6.2 変異 matrix (DW-M08、独立 clone @`083a45ee9`、計算ノード dispatch、probe → final)

変異は production `s8b_ratified_freeze.py` の M0 (等価 comment、SURVIVED 期待) + M1〜M14 (裁定 §3、M12 の old 文字列は fix2 の新 block へ差替え、追補 1)。runner =
`tools/run_tests.py --force-dispatch` で `test_s8b_ratified_verify.py` + `test_s8b_oracle_driver.py` + `test_s8b_binding_driftguards.py` (`-q -rf`)。独立 clone
(`git clone --local` + `update-ref main 083a45ee9`、submodule 再帰初期化、D1009) を `tools/mutation_worktree.py --runner-mode dispatch --detached` で走らせた。

**probe (`mutation/mutation-spec-probe.json`、sha256 `b0f04c2c…`、全件 SURVIVED 登録で観測 node を集める、20:33〜23:15 JST、計算ノード混雑で 1 走 5〜15 分):**
baseline PASSED、M0 SURVIVED (harness の SURVIVED 検出の正例)、M1〜M14 は全件で赤 node を観測 (`MISMATCH` = SURVIVED 登録に対する赤、probe の設計どおり)。
観測 node (`mutation/mutation-probe-summary.json`、原本 sha256 `17c624e3…`) は段 6 レビュー A の帰属表と一致:

| 変異 | 観測 node | 帰属 |
|---|---|---|
| M1 reservation allowlist 削除 | 53 (reservation を持つ journal test 全部 + 正例 unbound / bound) | 正常 reservation が `journal-event` で拒否される |
| M2 binding optional 拡張削除 | 26 (binding 付きの test) | 正常 binding が `schema-keys` で拒否される |
| M3 claim 一致検査削除 | 3 (`binding_one_sided_claim` ×2、`binding_campaign_without_reservation`) | 片側 claim が受理される |
| M4 binding 型検査削除 | 12 (`binding_invalid_type` 全部) | `both` 4 ケースは受理への転化 (独立 killer)、単独 event 8 ケースは値不一致検査の別 cause (契約差分、RA-1) |
| M5 値一致検査削除 | 2 (`binding_value_mismatch`) | 値不一致が受理される |
| M6 reservation 型検査削除 | 24 (`reservation_invalid_integer` 21 + `_other_type` 3) | 型不正が受理される |
| M7 件数検査削除 | 2 (`reservation_duplicate`) | 2 件が受理される |
| M8 順序検査削除 | 2 (`reservation_after_campaign`) | campaign 後の reservation が受理される |
| M9 下限削除 | 1 (`artifact_lineage_rejected[before-cert]`) | C より前の導入が受理される |
| M10 非 merge 検査削除 | 1 (`[merge]`) | merge 初導入が受理される |
| M11 一意導入 → 先頭 | 1 (`[multiple]`) | 複数導入が受理される |
| M12 世代文書 {G} 検査削除 | 2 (新 `generation_introduction_independent` + 既存 `floor_source_introduction_must_be_exact_generation_commit`) | **受理集合の kill ではない**: 段階 7 が `scan-exemption-invalid` / `active-chain-mismatch` で拒否し、cause の exact assertion が赤になる = 拒否段階 / cause の契約検出 (RA-1、DW-M08 の diagnostic sensitivity pin 別枠) |
| M13 上限削除 | 1 (`artifact_upper_bound_helper`) | 重複検査の helper 単体試験だけが殺す (B-1) |
| M14 段階 6 を旧 `== {G}` に戻す | 59 (正例 certificate / bound / unbound、interval positive、lineage rejected の cause、journal 負例の対照 (i = C 前提)) | 現物 topology (i = C) が拒否される |

**final (`mutation/mutation-spec-final.json`、sha256 `827324bc…`、probe の観測 node を完全集合として KILLED 登録、M0 は SURVIVED 登録、23:15〜02:55 JST):**
**baseline PASSED (293 s)、M0 SURVIVED、M1〜M14 = 14/14 KILLED、期待 node 完全一致 15/15、MISMATCH 0** (`mutation/mutation-final-summary.json`、原本 sha256 `49fa7d41…`)。
1 走の所要は 268〜944 s (計算ノード混雑の queue 待ちを含む、runner 報告値)。集計上の注意 (RA-1、DW-M03 / M08): M12 の KILLED は「拒否段階 / cause の契約」の検出で
受理集合の防壁の証拠ではない (段階 7 が別 cause で拒否する)。M13 は helper 単体試験による重複検査の KILLED。M4 の受理集合の証拠は `both` 4 node で、単独 event
8 node は cause の契約差分。独立した受理集合の防壁として数えるのは M1〜M11 (M4 は `both`) と M14。

### 6.3 受入・provenance・docs 検査

- provenance range 監査 (`check_ai_provenance.py --range 800178b39..HEAD`、記録 commit 1 の tip): **4 件、違反なし** (実装 3 + 記録 1、`provenance-range-1.log`)。
  land 時の全史監査は `dev_wave_land.py` が DW-O25 で自ら行う。
- `check_docs` 違反なし (記録 commit 1 / 2 の前に各 1 回)、`git diff --check` 緑 (統合・fix1・fix2)、`spool_fold.py --dry-run` rc=0。
- 三軸走査 (`s8b_holdout_freeze search`、記録 commit 1 直前): hit は既知の official 成果物 4 file × 2 holdout のみ (本 wave の docs / insight に新 hit なし、
  `three-axis-scan-1.log`)。
- 受入: 記録 commit 2 と段 8 の commit の tip で待ち手経由の全走 (`dev_wave_wait.py acceptance`、3 shard) を門番 loop から投入する。結果は本 README には書かず
  受領証 (job dir `acceptance-receipt-<tag>.json`) と land の記録が持つ。child-green でなければ land しない。

## 7. 到達範囲と非保証

- 本 wave の完了主張は **「validator の互換性修復」と「新 main の historical reverify (`reverify_published_freeze`) が段階 8 に到達すること」** に限る。
  historical reverify は候補 hit (N3) で失敗のまま、live `launch_validate` は policy 照合 (N1) で拒否のまま。P3 の全 gate 受理 (`allowed: true`) は未達。
- W-4 (spec 承認)・W-5 (実走)・certified 選択・測定値・認証結果は更新しない。launch 成功や W-4 / W-5 の開始許可を示すものではない。
- 旧 pin 固定 checkout への修正の移植・実測は未実施・未確認 (A-2)。brief の「旧 checkout でも同じ結論しか出ない」は撤回した。
- 独立 fixture の `launch_validate` 成功は launch core の証拠で、loader (V1a を含む) 込みの chain 成功の証拠ではない。loader 成功は実 repo で別に実測した (§5 (e))。
- 上限 i ≤ G は段階 3 の G-tree 実在検査と一意導入から従う重複検査 (M13 は helper 単体だけが殺す)。M12 (世代文書 {G}) は削除しても段階 7 が別 cause で拒否するので、
  受理集合の防壁としてではなく「拒否段階 / cause の契約」として数える (RA-1)。
- binding は記録内の整合情報であり PBS job の外部認証ではない。DAG 上の記録順 (C ≤ i ≤ G) は実時間順 (cert 発行と result 走行の順) を保証しない。
- fixture の journal は key 文法と型契約だけが現物と一致し、値 (required_s 等) や perf-preflight の有無は現物と異なる (現物経路は §5 (a) が裏付ける)。

## 8. scope 外 (実装しない、裁定パッケージ候補)

1. **N1 / [T-2812]:** 新 main の live 経路は段階 4 の policy 照合で止まる。policy 照合の除去・`expected_policy=None` の live 導入・receipt 張り替えは D2184 で却下済み。
   移行は T-2812 (② 登録・identity、③ driver pin、⑤ successor protocol、admission の整合)。
2. **N3 候補文書の scan hit:** 第一候補 = 候補 file `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` だけを削除する commit。scan 除外は広げず、B-10 freeze-tree pin
   (`output/s1-freeze` + `output/s8b-freeze`) の対象外、G/A/X・floor_source bytes は不変、`_active_chain_exempt_exact` 不変。帰結: `V2_CANDIDATE_REL` の create-only
   存在拒否が消える (再生成されれば hit が復活)、`_ACTIVATED_G1_REFUSALS` の候補を含む hit 列挙が変わる、削除後に load / reverify をやり直す、候補 bytes と来歴は X2 の
   履歴 blob と世代文書で保持。D2077「痕跡を消してよかったことの証明ではない」に照らし、削除の根拠は別裁定 (候補 path の役割終了を認めるか)。
   **裁定 (第 27 回 /rulings、2026-09-21 00:5x JST「推奨通り」、一次控え `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-21-rulings-full27-verdicts.md` 項 5、
   台帳の D は記録 wave `rulings-all-20260921` の fold 後):** (a) 候補 file だけを削除する commit を本 wave の land 後に別 commit で (scan 除外不変、削除後に load / reverify を
   再実測)。根拠 = 候補 path の役割が批准済み世代 (D2180) へ移って終了。本 wave では実施しない (worklog の新規 T へ AI 手番として起票)。
3. **旧 pin 固定 checkout への修正の移植:** 歴史再開に本修正を使うなら移植した別 checkout の検証が要る。
4. **W-4 spec 承認、W-5 実走・certified 選択:** 不変。

## 9. 段 3 / 段 6 所見と採否

- 段 3 相談 A (`verbatim/s3-consult-A.md`、sol): must-fix 0、should 2 (A-1 binding 無し reservation の多重・順序を無条件に許さない、A-2 旧 checkout への一般化を書かない)、
  nit 1 (A-3 brief 末尾の拒否原因の表記)。信頼の根の循環なし。すべて採用。
- 段 3 相談 B (`verbatim/s3-consult-B.md`、luna): must-fix 3 (B-1 上限は重複検査と明記、B-2 受理集合の一般化を明示、B-3 効能の限定、いずれも文言・記録)、should 3
  (B-4 N3 の削除案の帰結を裁定材料に、B-5 fixture 成功 ≠ loader 込み成功、B-6 runbook へ現在値を再掲しない)。第 4 案 δ を提示 (不採用、§3)。すべて採用。
- 段 6 レビュー A / B、fix1 / fix2、焦点再レビュー: §4。
- 依頼文の「段階 6 を『chain の祖先で cert C より後』へ改める」は現物 (cert C = result 導入) を満たさないため「C ≤ i ≤ G (同一を含む)」として実装した (N4、段 4 裁定)。

## 10. 段 8 — dev-wave 改善候補

- 候補 1 (一次資料 §5 の α 文言「C < 導入 < G」が現物 topology と不一致、N4): brief 前の前提実測 (DW-S01) で発見できたので手順の欠落ではない。記録のみ、docs 変更なし。
- 候補 2 (pin 前進が policy epoch 経由で held 真値 `_ACTIVATED_G1_REFUSALS` を静かに古くし、hold により受入で赤にならなかった): routing 1 (同型再発) として
  failures F10「pin 前進で腐る構造」へ再発追記 (`docs/spool/failures/…-3.md`)。DW-O09 (pin 閉包) への「値 pin は間接依存 (policy sha) でも古くなる」の追記は
  L2 予算の範囲で判断が要るので入口・reference は変えず、memory `ccbench-pin-advance-execution-facts` に「policy epoch を動かす wave は held 真値の再実測を
  帰結に含める」を追記 (恒久対応の実体)。
- F100 再発 (他 worktree へ `cd`) は failures fragment に記録済み。command 入口・reference の変更はゼロ。

## 11. 収録物

- `verbatim/`: 依頼逐語、brief、plan、相談 A / B、段 4 裁定、author 報告、レビュー A / B、fix1 報告。
- `evidence/`: 前提実測 (p3-before-g1、journal-keys-probe、reverify-probe-journal-mutated、reverify-probe-journal-stage6-mutated、selection-identity-before)、
  統合後実測 (reverify-after-impl、p3-after-g1、p3-after-v1、selection-identity-after)。
- `mutation/`: spec (probe / final) と results の要約 (原本は wave artifact dir、sha256 で束縛)。
