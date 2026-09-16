# [T-2724] freeze v2 g1 候補を official 床値 result から生成した — producer の固定 protocol read を index authority へ直し、候補は保存 branch に置いて発効しない

wave `dev-wave-t2724-freeze-v2-g1-candidate`、base = local main `1042a1bc95057fa03117d504cfa2b0fafaae60d0`
(2026-09-17 00:38 JST)。land branch `land-dev-wave-t2724-freeze-v2-g1-candidate` (producer 修正 + docs)、
保存 branch `freeze-g1-chain-t2724` (入力と候補、main には載せない)。

**何が新しいか。** 2026-09-16 に完走した official 床値 result (run `20260916T111925Z-2c8cf9be`、request
`1818.nqsv`) を入力に、既存 producer `s8b_holdout_freeze.py generate-v2-candidate` で freeze v2 g1 の候補
document を初めて実体化した。生成の途中で producer が official result を拒否する実在欠陥 (固定
`floor_protocol.json` の literal read、ccbench pin 前進に未追随) が実測で出たので、campaign 側と同じ
index authority で protocol を解決する形へ直した (D460 型、D589 が deferred していた箇所)。
候補は `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` (sha256 `7e1114068433b40dc459e5e9c5ffcfa9a38cd360fc798904b7a9842382e19c06`、
20,737 bytes) で、世代文書 (`output/s8b-freeze/`)・approvals/・active/ は作っていない = 発効していない。

## 1. 入力と出所

| 項目 | 値 | 出所 |
|---|---|---|
| official result | `output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/result.json`、sha256 `b111831e9d002b523b57b0096a04bf03bb86b9b01fb5418511909f8ed4075620` | [T-2698] 一次資料 `output/insights/2026-09-16/t2698-official-floor-resubmit/README.md` §3・§9 |
| 退避 (D2077 step 2) | `<git common dir>/izanagi/s8b-floor-evacuation/pegasus/` へ `s8b_floor_evacuation evacuate` (root = T-2698 の wave worktree)。run 1 件・5 file、`evidence/evacuate-manifest.json` | 本 wave 01:16 JST。T-2698 の木は古い tip で退避 module を持たないため、main 版 module を `sys.path` 先頭に置く runner (`run_evacuation.py`、job dir) で実行した |
| 再配置 (step 4〜5) | `restore --env-tag pegasus` で chain 木へ namespace 全体を戻し、5 file を commit | `evidence/restore-2.json` |
| budget 入力 | `output/s8b-freeze-budget-inputs/g1.json` = 承認文書 `output/s8b-freeze-budget-approvals/g1.json` (sha256 `05d4d778…` = `BUDGET_APPROVAL_SHA256`) の `budget` を producer と同じ canonical bytes で書いたもの (91 bytes、末尾改行なし)。path は fixture (`s8b_v2_freeze_fixture.py`) と過去計画に合わせた本 wave の保存先で、production 固定規約ではない | job dir `write_budget_input.py` |
| 手動 bundle | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2698-official-floor-resubmit/run-backup/` は参照用に残す。producer も restore も読まない | — |

全 151 worktree を走査した結果 (`evidence/official-namespace-scan.txt`)、official namespace を持つ木は
T-2698 (result 込み 1 run) と T-1851 (`journal.jsonl` + `launch_certificate.json` だけの 3 run、
`result.json` 無し) の 2 本だけだった。T-1851 の 3 run は `_official_earlier_floor_results` が result.json
不在で skip するので最早適格 run の判定に影響しない。その退避は本題外の掃除として裁定パッケージに注記した。

## 2. producer の欠陥と修正 (must-fix C-1、実装面)

- **実測:** chain 木 (入力 commit 済み) で `generate-v2-candidate` は rc=1
  `fails-closed: floor result.protocol_sha256 が固定 protocol hash と不一致` (`evidence/generate-1-refused.log`)。
  固定 `output/s8b-freeze/floor_protocol.json` (ccbench pin `d706650c…`、canonical sha `261cec1c…`) と、official
  走行が index authority で解決した版付き `output/s8b-freeze/floor-protocols/e576e9cd…--511c9538….json`
  (pin `511c9538…`、sha `2c8cf9be…`) は `ccbench_pin` 1 行だけが違う。result は `2c8cf9be…` を記録している。
- **原因:** producer が 2026-08-11 実装のまま固定 path を literal で読み、2026-08-12 の pin 前進 ([T-816]) と
  版付き protocol の解決器 (`resolve_current_floor_protocol`、D460) に追随していなかった。admission 側
  `_authority` は解決 record と producer が渡す protocol 文書の一致も要求するので、hash 比較だけ直しても通らない。
- **既裁定:** D589 (2026-08-20) がこの箇所を「D460 型変換の対象になり得るが、承認 artifact・pin ratify・
  official result の 3 条件が揃わず到達不能」と deferred。3 条件は 2026-09-16 にすべて揃った。
- **修正 (Codex author、commit `3b0b75496ff90e6c4d4a2d76d9fd80a840a7dabb`):** `_validate_floor_inputs` が
  `resolve_current_floor_protocol(root=root)` の record を使い、record の commit OID == captured HEAD と
  解決 path の worktree bytes == HEAD blob を要求する。candidate の `floor_protocol` に解決 path と raw
  sha256 を記録し、`_measurement_closure` の専用 path に解決 path を足す。`FLOOR_PROTOCOL_REL` 定数は不変
  (historical anchor test の pin)。走査除外・allowlist・admission・批准側・既存 test の期待値は変えていない。
  fixture に `versioned_protocol` option、正例 1 本・負例 2 本を追加。設計判断は本 wave の decisions
  fragment (「freeze v2 g1 candidate producer は floor protocol を index authority で解決し…」、着地後に採番) を参照。
- **受理集合の前後 (段 6 レビュー RA-1 の訂正込み):** 旧「固定 protocol と一致する result」→ 新「index
  authority が解決した現行 protocol と一致する result」。本番相当 (anchor + 版付き 1 件、HEAD gitlink が
  版付きを選ぶ) では、旧実装は版付き result を早期 hash 比較で、固定 protocol 対応の result を後段 admission で
  拒否するため受理集合は空だった。新実装は版付き result だけを受理する。
- **段 6 の実測が出した欠陥 2 件:** (i) 段 5 の実装が既存 loop の変数 `record` を影にして末尾で
  `AttributeError` (焦点走 1: 21 failed / 141 passed)、fix 2 巡目で `protocol_record` / `protocol_rel` に改名。
  (ii) 新規負例の `master_seed += 1` は str に int 加算で TypeError (レビュー B)、文字列接尾辞へ。
  レビュー A の指摘で campaign 側の例外文言に依存する書換え分岐と、同じ commit の HEAD blob 同士を比べる
  恒真の比較 (`record.raw_bytes`) を削除した。
- **焦点走 (親が計算ノードで実走):** 変更 test file 単独 **162 passed / 2 skipped / rc=0**、consumer 11 file
  (`test_s8b_protocol_builder` / `test_official_perf_closure` / `test_ccbench_spawn_sites` / `test_s8b_floor_stats` /
  `test_s8b_ratified_freeze` / `test_s8b_ratified_verify` / `test_s8b_oracle_manifest` / `test_s8b_freeze_io` /
  `test_s8b_floor_evacuation` / `test_s8b_predicate_build_proof` / `test_s8b_budget_approval_preflight`)
  **669 passed / 2 skipped / rc=0**。
- **変異 matrix:** baseline PASSED、M1〜M4 = 4/4 KILLED (期待 node 完全一致)、M0 等価 SURVIVED (§7)。

## 3. 候補 (chain の内容と静的検証)

保存 branch `freeze-g1-chain-t2724`: `1042a1bc9` (X0 = main) → `3b0b75496` (P = producer 修正、land branch と共有)
→ `cc82edc8c9f90a9ee659c2d27f71b75b19a56490` (X1' = result 5 file + budget 入力) → `4d8fb93b7c8d5466e9ad91b1bc5b600a2fdd7ac8`
(X2 = 候補 1 file)。

| 検証 (read-only、`evidence/candidate-projection.json`) | 結果 |
|---|---|
| producer の実行 | rc=0、`generated-v2-candidate: output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` (`evidence/generate-2.log`)。通った検査は code 上: v1 固定 hash・schema・holdout 集合、budget 承認 pin / canonical / scope / approver / 日時、budget 本体の canonical 一致、protocol の index 解決・HEAD 一致・canonical hash・freeze 固定参照、result の official path 文法・key 集合・mode・perf evidence・freeze/protocol hash・proto8・header 5 field、binaries の admission 束縛 (12 cell)、sibling manifest / journal との整合、live admission 台帳 (共有 root の claims / consumed / ledger / attempt-ledger / v5 registry replay)、`eligible_for_refreeze` の live 再導出との一致、最早適格 run の identity (namespace に他 run 無し)、launch certificate、measurement closure |
| canonical bytes == raw、top-level key 集合 | 一致 |
| `frozen_at_head` | `cc82edc8c…` = X1' (HEAD) |
| `supersedes_sha256` | `315b1eb8…` = v1 固定 hash |
| `floor_protocol` | 版付き path、sha256 `2c8cf9be…` (解決器の record と一致) |
| `floor_source` | result.json、sha256 `b111831e…` (worktree bytes と一致) |
| `measurement_closure` | 空 (専用 path 以外の hit なし) |
| `generator` | `orchestrator/campaign/s8b_holdout_freeze.py` sha256 `5a8798d4…` (P の blob) |
| 批准側 `_parse_generation_document(raw, 1)` | ok (schema・世代番号までの静的検査、批准検証の代替ではない) |
| `resolve_active_generation` | `RatifiedFreezeError reason=no-active` (未発効) |
| 三軸走査 (`search`、chain 木) | rc=1、hit は両 holdout とも専用 4 path (run_dir の journal / manifest / result + candidate) だけ、陽性対照 183 件。`result.md` と `launch_certificate.json` は非 hit |
| 三軸走査 (land 木、insight・docs 込み) | rc=0 |

**候補全文は repo の land 集合にも本 insight にも複製しない** (v1 の deepcopy で三軸 literal を含む)。
射影 (`evidence/candidate-projection.json`) は path・hash・数値・reason だけを持つ。

## 4. 床の値と意味

| holdout | `scale_ref` (stock 中央値) | `scalar_alt` (床) | 比 | pair 数 |
|---|---:|---:|---:|---:|
| rr20 | 1,193,931.5 | 35,817.945 | 0.0300 | 5 |
| rr80 | 1,535,526.0 | 46,065.78 | 0.0300 | 5 |

- 両 holdout とも床は `wired_min_rel_floor` (0.03) × stock 中央値で決まった。各 pair の実測 `u_noise`
  (rr20 15,859〜28,966、rr80 20,843〜27,543、[T-2698] §3) は下限未満。**これは現行 formula v2 に従った
  この 1 走行の床であり、between-run 変動・誤判定率・検定力は保証しない** (段 3 レンズ B)。
- **この床値は現行 8b oracle の勝敗判定の閾値ではない。** judge は「floor は入力にも argmax の tie-break にも
  使わない」(`s8b_oracle_judge.py`)、D1985 で床値由来の受入 3 述語は撤去済み、D2024 で残るのは driver の
  `floor-null` / `budget-null` 拒否 (存在検査)、budget → 今回走行の資源上限、report の解決経路。したがって
  g1 の発効が変えるのは「driver が floor / budget の null 拒否で止まらなくなる」ことで、床の数値が判定を
  保守化・楽観化することはない。段 1 brief の「差の検出下限」という読みは撤回した。
- 選択規則 D1311 (同一 env / proto8 の最早適格 run) により、**追加の official 走行を取っても床の出所は
  この run から差し替わらない**。追加観測は判断材料の追加であって候補の更新ではない。
  `wired_min_rel_floor` の再検討は protocol の変更 (別件)。

## 5. D2077 step 4 (打ち切り決定) の扱い

本 wave は **step 4 の打ち切り決定を下していない**。依頼が候補生成を明示し、候補生成は step 5〜6
(restore → commit → generate) 無しに機構上不可能なため、restore 以降を base から分岐した保存 branch に隔離して
実施した。これは D2077 の例外新設ではなく、step 7 の帰結 (成果物を持つ checkout では official 床値の起動証明が
赤になる) を main に及ぼさない実施形である。「D2077 を満たした」とは記録しない。両レンズ (A-6 / B-5) が
一致してこの区別を要求し、親は段 4 でそのとおり裁定した。固定退避先の bundle は restore 後も残るので
chain を捨てても入力は再取得できる (可逆性は data の話で、判断の取消しの根拠ではない)。

## 6. W-4 (oracle manifest の production 配線)

`s8b_oracle_manifest.py build-approved --output <path>` CLI が実在し `build_approved_manifest` を呼ぶ
production の入口である (呼び手は test 2 本だけという runbook の記述は stale)。実行主体は operator。
現在は `no-active-ratified-freeze` で止まり、active 成立後も `APPROVED_SPEC_SHA256 = None` で
`no-approved-spec` (T-750 P-1 の人間手番)。発火できる artifact が無いので wrapper は新設しない (DW-G04)。

## 7. 変異 matrix

登録 (段 4 追補で事前登録、段 6 レビューで再分類): M0 等価 (comment のみ、SURVIVED 期待)、M1 固定 anchor の
literal read へ復帰、M2 `floor_protocol.path` を固定 path に、M3 HEAD bytes 比較を削除、M4 result hash 比較を削除。
M5 (freeze 固定参照の検査削除) は本 wave の変更外の既存検査で、期待 node が無く後段 admission にも同種検査が
あるため登録から外した (レビュー A RA-3 / B RB-5)。走行は container 木 (`mut-t2724-freeze-v2-g1-candidate`、
commit P `3b0b75496`) で `test_s8b_holdout_freeze.py -k "v2_candidate or floor_protocol or versioned"`
(68 node)。probe (全件 SURVIVED 期待) で観測 node を集めてから本走 (`evidence/mutation-spec-*.json`、
`evidence/mutation-*-summary.json`。台帳全文は pytest 出力を含むため job dir に置く)。

**本走: baseline PASSED (68 passed)、M1 / M2 / M3 / M4 = KILLED (期待 node 完全一致)、M0 = SURVIVED、rc=0。**

| ID | 赤 node (接頭辞 `test_s8b_holdout_freeze.py::`) | 最初の赤理由 | 意味 |
|---|---|---|---|
| M1 | `test_v2_candidate_build_and_generate_versioned_protocol`、`test_v2_candidate_rejects_legacy_hash_for_versioned_protocol` | 前者は `解決した protocol hash と不一致` (HF の hash 比較)、後者は `proto8 が protocol hash と不一致` (文言差) | 新規検出力 (index 解決の配線)。後段 (proto8 / header / admission) も同じ入力を拒否するので「唯一の層」ではない |
| M2 | `…build_and_generate_versioned_protocol` | `floor_protocol` の path assert | 新規検出力 (記録 path) |
| M3 | 既存 `test_v2_candidate_rejects_worktree_only_floor_protocol_master_seed_mutation` | **DID NOT RAISE** | 段 6 レビュー 2 本は「admission 後段が同じ入力を拒否する冗長 gate」と静的に判定したが、**実測は producer の HEAD bytes 比較だけがこの入力を止めていた**ことを示した。既存 gate の実効性の再確認であり、本 wave の新規検出力ではない |
| M4 | `test_v2_candidate_rejects_legacy_hash_for_versioned_protocol` | **DID NOT RAISE** | 新規検出力 (result hash 比較、v4 fixture では後段の再照合が無い) |

## 8. 到達範囲と非保証

- 候補は未発効。世代文書・approvals/・active/ は作っていない。批准検証 (`_verify_generation_semantics`) は
  実在の世代導入 commit と active resolution を要するため実行していない。
- 「producer の全検査を通った」は code 上の検査項目と rc=0 の事実であり、binary 実体の再 hash や共有台帳の
  再構成攻撃の検出は含まない (D488 の限界と同じ)。
- 候補が main に載ると、それを継承する checkout では official 床値の clean scan が赤になる (D2077 step 7)。
  実 repo 全体に 0 hit を要求する test 2 本 (`test_s8b_repo_scan_invariant.py`、
  `test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan`) は
  growth hold (既定 skip、解除は明示指示のみ) で、解除時は設計どおり赤になる。既定 skip を正しさの合格とは
  数えない。
- closure の除外 assert (新正例) は除外前 hit の実在を示さないので、独立の検出力に数えない (RB-2)。
- guard の静的判定 (evacuation / restore / `git add` / `git commit` は防護対象外) と親 session での実行成功は
  別に記録した: いずれも実行成功。`EnterWorktree(path)` は worktree 152 本・load 50 超で `git worktree list`
  が 10 秒を超え 2 回失敗したため、chain 木 1 本で branch を切り替えて進めた。
- 三軸 literal は本 README・evidence・docs に複製していない (land 木の走査 rc=0)。

## 9. 検査

| 検査 | 結果 |
|---|---|
| `check_wave_startup.py --mode fresh --forbid-worktree-handoff --external-handoff` | rc=0 |
| runbook §2 preflight P1 / P2 / P3 | `511c9538…` 一致 / 5 passed / rc=2 で拒否 `floor-null` `budget-null` の 2 件 exact (`evidence/preflight-p3-gate-check.log`) |
| 焦点走 (変更 test file 単独、fix 2 巡目後) | 162 passed / 2 skipped / rc=0 (計算ノード dispatch) |
| 焦点走 (consumer 11 file) | 669 passed / 2 skipped / rc=0 |
| `check_ai_provenance.py` (P まで) | rc=0 |
| 三軸走査 chain 木 / land 木 | rc=1 (専用 4 path のみ) / rc=0 |
| 変異 matrix (container 木、commit P) | baseline PASSED (68 passed)・M1〜M4 = 4/4 KILLED 期待 node 完全一致・M0 等価 SURVIVED・rc=0 (§7) |
| `check_docs.py`、`spool_fold.py --dry-run`、受入全走 | 記録 commit の後に実走し worklog に書く |

## 10. 収録物

- `package.md` — 裁定パッケージ (人間手番の入口)
- `evidence/candidate-projection.json` — 候補の三軸を含まない射影と静的検証の結果
- `evidence/evacuate-manifest.json` / `evidence/restore-2.json` — 退避・再配置の出力
- `evidence/generate-1-refused.log` / `evidence/generate-2.log` — 修正前の拒否と修正後の生成
- `evidence/official-namespace-scan.txt` — 全 worktree の official namespace 所在
- `evidence/preflight-p3-gate-check.log` — runbook §2 P3
- `verbatim/` — 段 1 brief、段 2 plan、段 3 レンズ 2 本、段 4 裁定 + 追補、段 5 prompt / 報告、段 6 レビュー 2 本 / fix prompt / 報告。
  `verbatim/s2-plan.md` は `git diff --check` 抵触のため行末空白を除去した可逆最小正規化 (可視文字不変): 原文 sha256
  `09a229ed99c54530befce67840385ae534dad89fc4299f2fe6f4d505e451c7f1` (33,642 bytes、行末 2 space の行 9 本) →
  正規化後 `efc9212cc2b887e36ab20bf002f783880c61109a1bfe4f5ca2e56357a310eea6` (33,624 bytes)。復元は当該 9 行
  (Markdown の強制改行) の行末に 2 space を戻す。原文は job dir `artifacts/…/s2-plan.md` に保全。

job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-freeze-v2-g1-candidate/` に runner script、log、受領証、
変異 spec / 台帳、`handoff.md` を保全した。
