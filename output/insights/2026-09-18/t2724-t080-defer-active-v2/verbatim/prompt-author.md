単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2

あなたは段 5 の実装子 (Codex `role=author`) である。作業 worktree は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-t080-author` (branch `impl-dev-wave-t2724-t080-defer-active-v2`、基点 = wave branch tip = local main `24ede1d11`、chain 無し)。コードとテストだけを編集する。

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/s4-adjudication.md` — **親の段 4 裁定 (確定仕様の正本)**。所見の採否、plan v2 の骨格、変異事前登録、分割
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/artifacts/dev-wave-t2724-t080-defer-active-v2/s2-plan.md` — 段 2 plan (file:line 粒度の設計。段 4 で修正された点は s4 が優先)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/artifacts/dev-wave-t2724-t080-defer-active-v2/s3-a.md` — レンズ A (正しさ境界) の所見。A-1 (鮮度)、A-2 (変異の帰属表)、A-3 (adapter)、A-4 (draft 負例)、A-6 (走査範囲)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/artifacts/dev-wave-t2724-t080-defer-active-v2/s3-b.md` — レンズ B (実効性) の所見。B-1 (接続 fixture の障害と材料表)、B-2 (serialization の literal consumer 2 本)、memo consumer の検算表、floor clone の 3 段 assertion、新負例の配置 path
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/s1-brief.md` — 親の段 1 brief (不変条件)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-t080-defer-active-v2/rulings-verbatim.md` — 確定済みユーザー裁定の逐語

repo 内の現物は作業 worktree `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-t080-author` で読む (plan / 所見の行番号はこの木と同じ基点 `24ede1d11` のもの)。**大きい file を全文 `cat` しない。** `grep -n` で位置を出し `sed -n` で 200 行以内ずつ読む。chain 有り木の現物は `git show 229982652:<path>` で読める (X1' の run_dir 5 file と G の世代文書。候補 X2 は無い)。

## 確定仕様 (s4 の plan v2 を要約。矛盾したら s4 が優先)

### A. production (3 file)

1. `orchestrator/campaign/s8b_ratified_freeze.py`: `LaunchValidatedFreeze` と `ReverifiedFreeze` に `validation_root: Path` (resolve 済み) と `search_report: Mapping` (deep-freeze 済みの full scan report) を追加し、`_launch_validate` の C2-4 完全一致・陽性対照・artifact 再捕捉が成功した後に埋める。`_enumeration_digest`、`EXCLUDED_PATHS`、`exempt_exact` 導出、完全一致検査は変えない。受理側 default で互換化しない (直接 constructor 7 箇所は test 側で追随する)。
2. `orchestrator/campaign/t080_freeze_migration.py`: `_verify_holdout_live_scan` の直前に局所 helper `_holdout_layer2_delegation(*, root, validation_head, launch_validated) -> Optional[Mapping]` を置く。委譲可能なら検証済み report、条件外は `None` (predicate が評価できない場合も `None`。通常検査の例外は握り潰さない)。発火条件は**すべて**: (1) `type(launch_validated) is s8b_ratified_freeze.LaunchValidatedFreeze` (subclass / duck 型 / `ReverifiedFreeze` は不可)、(2) `launch_validated.validation_root == Path(root).resolve()`、(3) `launch_validated.activation_head == validation_head == _capture_head(root)`、(4) `launch_validated.ratified.activation_head` も同じ、(5) 同じ root で `s8b_ratified_freeze.resolve_active_generation(root)` が成功し、その `activation_head` / `generation_sha256` / `generation_number` / `generation_commit` が `launch_validated.ratified` の値と一致、(6) `launch_validated.search_digest == s8b_ratified_freeze._enumeration_digest(root)`、(7) 凍結 doc 束縛 (rr80/rr20 集合、`match_convention`、各 `candidate_id`、各 `unknownness_check.expressions`) を report に掛けて通る。`_verify_holdout_live_scan(root, holdout_doc, *, delegate_to=None, validation_head=None)`: `delegate_to` があり helper が report を返したときだけ、その report に束縛検査 (7) を掛け **`_assert_search_pass` (zero-hit) を課さない**。それ以外は従来どおり `search_repository(root)` → 束縛検査 → `_assert_search_pass`。`verify_receipt(*, root, path, launch_validated=None)` は捕捉した `head` を `validation_head` として渡す。`static_gate_adapter(*, resolution, known_raw, holdout_raw, root, launch_validated=None)` も independent 列で同じ helper・同じ条件を使う (`resolution.validation_head` を渡す)。refusal は既存の正規化 (`holdout-freeze-verify: [holdout.unknownness_layer2] …`) のまま。`ReceiptResolution` / observation / `held_checks` に新 field を足さない。
3. `orchestrator/campaign/s8b_oracle_driver.py`: `_resolve_t080_receipt(*, root, launch_validated=None)` (指定時だけ migration へ渡す。token なしの既存呼出しは `verify_receipt(root=root)` の形を維持)。**P3' (解決 1 回化)**: `gate_check` は freeze 読込み・v1/v2 判定・loader・`launch_validate` の後で receipt を 1 回解決する — v2 成功経路は token 付き、loader / launch 失敗経路と `ratified_error` 経路と v1 経路は token なし。早期 return で解決を省かず、全 refusal return に resolution を渡す (新しい refusal return を増やさない — 既存の 15 refusal-return pin を保つ)。`run_block` も同じ: `load_ratified_freeze` / `launch_validate` の後で 1 回 (成功 = token 付き)、`_gate_check_validated` / `_campaign_t080_value` にその resolution を渡す。**campaign-start 前 (現 `:1527` 付近)**: `launch_validate(ratified, root)` を**再実行**して新鮮な token を得て、gate 時 token と `ratified.sha256` / `activation_head` / `search_digest` が一致しなければ `v2-execution: launch-validate:` 系の既存 prefix で refuse (新 return を増やさず既存 factory 経路へ寄せる)、一致すれば新鮮 token で委譲付きに再解決し `_t080_epoch_identity` の 4 要素を比較 (既存)。`_t080_epoch_identity` の要素は変えない。`_t080_adapter_refusals` / `_gate_check_core` へ token を転送しない (v1 発火時に token は存在しない、A-3)。成功経路の `_resolve_t080_receipt` 呼出し回数は 2 (gate 後 1 + campaign-start 前 1) を維持する。

### B. test (境界 test、既存 file へ追記、新規 test file は作らない)

s2-plan「境界 test の設計」の表の名前を使う。少なくとも:

- `orchestrator/tests/test_t080_freeze_migration.py`: `test_layer2_delegation_rejects_wrong_activation_head` (本物 token から `dataclasses.replace` で **outer** `activation_head` だけ変える)、`test_layer2_delegation_rejects_foreign_root` (別 root、同 HEAD・同名集合の clone の 2 ケース)、`test_layer2_delegation_rejects_enumeration_drift` (token 取得後に namespace 外・非 ignored の通常 file を追加)、`test_layer2_delegation_rejects_nonlaunch_type` (`ReverifiedFreeze` / duck 型 / subclass)、`test_layer2_delegation_rejects_stale_generation_token` (HEAD field だけ現行値にした旧世代 token、または namespace dirty)、`test_delegated_scan_keeps_frozen_document_bindings[expressions|match_convention|candidate_id|candidate_set]` (本物 token と report、入力 doc 側を 1 項目ずつ変更 → 層 2 reason で拒否)。これらは `test_s8b_ratified_freeze.py` の emitter fixture (`_prepare_emitter_base` / `build_production_emitter_g1`) から**実 `load_ratified_freeze` → 実 `launch_validate`** で token を得る (`search_repository` / `_assert_search_pass` / `launch_validate` は monkeypatch しない、DW-O14)。
- `orchestrator/tests/test_s8b_ratified_freeze.py`: `test_launch_token_retains_immutable_scan_and_root` (root・digest・report の内容と不変性、`ReverifiedFreeze` は admission へ昇格しない)。
- `orchestrator/tests/test_s8b_oracle_driver.py`: 接続正例 `test_t080_active_v2_delegation_accepts_full_receipt` (下の C)、`test_t080_unactivated_chain_hit_is_invalid` (R 後・G まで・A/X 無し・合成 official hit → exact 層 2 refusal)、`test_t080_failed_launch_preserves_receipt_refusal` (closure 外の合成 hit → 実 launch が `closure-hit-mismatch`、公開 gate が launch refusal と receipt 層 2 refusal の両方を保持)、`test_t080_active_v2_preserves_nonlayer2_receipt_refusal` (launch 成功 + R trailer 不正 → 拒否・無副作用)、`test_t080_delegated_campaign_start_rechecks_receipt` (gate 後 campaign-start 前に receipt 改変 / 削除 → epoch 拒否、WAL / evaluate 不発火)、`test_t080_delegated_campaign_start_rejects_late_hit` (gate 後に namespace 外の合成 hit を追加 → campaign-start の再 launch で拒否)、`test_v1_gate_does_not_delegate_with_active_v2` (批准済み fixture でも v1 path 指定では従来拒否)。draft 側負例 (A-4): 切り離し後の stub-free fixture に S 外の走査対象 path へ合成 hit を置き、実 draft (`_draft_reconstruct_holdout`) が層 2 で拒否する。

### C. 接続正例の fixture (B-1)

`_build_t080_stub_free_e2e_repo` (test_s8b_oracle_driver.py:1364) の T-080 発行済み履歴の上に、emitter 系 helper で G / A / X を積んで、実 `load_ratified_freeze` → 実 `launch_validate` → 実 `verify_receipt(launch_validated=token)` が `active-valid` (refusals 空) になる repo を作る。B-1 の障害を**初期 commit 前に**避ける: この正例 fixture の base には実 root の `output/s8b-freeze/holdout_freeze.v2.g1.json`・`output/s8b-freeze-budget-inputs/g1.json`・selector 証拠 (`output/s8b-freeze/selector_predictions.json`、`output/s8b-freeze/selector-runs/`) を複製しない (chain 有り木で `history-mutated` / selector 祖先不成立になるため)。selector 材料は fixture repo 自身の seed commit に束縛して `_install_emitter_selector_prediction` で合成する。順序 `basis → R → … → C (certificate) → G → A → X`、`G^ == frozen_at_head`。`_prepare_emitter_base` / `_make_fixed_ccbench` を再実行せず、既存 ccbench pin を protocol に渡す (hold 下、`_freeze_hold.HELD` は True)。**45 node 用の削除集合 S はこの fixture の除外と別物で、広げない。** 接続できなければ「実装済み・未達」と正直に書き、分離 test で示せた範囲と障害の現物 (どの検査が何を拒否したか) を報告する。検査を stub / monkeypatch して active-valid を作ってはならない。

### D. 4 経路 45 node の切り離し (T-2776)

削除集合 `S(H) = H の output/env/pegasus/calibration/s8b-floor-official/ 配下の全 path ∪ ({V2_CANDIDATE_REL} ∩ paths(H))` (候補は exact file 1 つ、候補 directory 全体は削除しない。走査結果を見て S を広げない)。

- (i) `_copy_git_visible_output` (test_s8b_oracle_driver.py:827): 除外集合に S の Git-visible 部分を足し、ancestor 集合も削除後の集合から作る。copy 契約 test (1660〜1714) に official 配下・候補 exact file・候補 dir 内の無関係 file を追加し、copy 後の差分が「receipt・draft・宣言 S」だけで残存 file の bytes が同一であることを独立に検査。consumer pin (1284、11 node) は純増があれば明示追随。
- (ii) `test_s8b_floor_campaign.py`: `_clone_committed_head_with_ccbench` (2291) と `_protocol_binding_public_preflight` の直接 clone (15609〜15625) の**両経路**に、S の tracked path を `git rm` + commit で外す局所 helper (`_remove_post_seal_floor_protocols_from_replay` と同型、S 空なら commit しない)。履歴 assertion は 3 段 (source HEAD 捕捉 / gitlink commit の親と diff / S 非空なら削除 commit の親と D 集合と残存 tree の mode・OID) に分離し、単純に `HEAD^^` へ変えない。5 node の期待値・hash drift 拒否文字列・`bypass_drift_gate=True` 対照は維持。新負例 `test_clean_scan_rejects_synthetic_chain_artifacts[official|candidate|both]`: clean clone に `output/env/pegasus/calibration/s8b-floor-official/synthetic-chain/result.json` と `V2_CANDIDATE_REL` へ `s8b_v2_freeze_fixture._holdout_hit_text` の合成 bytes を通常 file として置き (chain / G の実 bytes は使わない)、**report の `conjunction_hits` に投入 path が載ることを確認したうえで** 実 `clean_scan_digest` の拒否を要求。無害 bytes の対照は正しい allowlist で通る。
- (iii) `_run` (2951) の既定を `_never_issued_resolution()` の合成 resolution へ切替え (`_run_with_real_manifest_gate` と同型)。直接 memo を使う 3 関数 (3345 の CLI 欠落 root、5160 の validated 再利用、5240 の manifest 一回検証) も同様。`memo_receipt=False` の opt-out 2 関数 3 node は維持。登録簿を追随: conftest `RECEIPT_MEMO_CONSUMER_NODES` (712)、`test_real_repo_serialization.py` の `_RECEIPT_MEMO_CONSUMERS_GOLDEN` (503)、`:2853` の導出 (直接 memo 呼出しを数え、opt-out 検出は独立に維持)、`:2906〜2907` の 34/37 → 8/8、**B-2 の literal 2 本** (`test_receipt_memo_prewarm_wiring_is_controller_only_and_lazy` 4963 付近、`test_receipt_memo_real_xdist_order_has_no_worker_payer` 5485 付近) を残存 consumer 名へ。残る 8 = driver 4 (`test_real_freeze_gate_lists_floor_and_budget_null` / `test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing` / `test_nonnull_floor_without_active_generation_is_refused` / `test_active_resolution_and_manifest_structure_refusals_are_aggregated`) + driftguard 4。growth hold は変えない。
- (iv) `test_never_issued_generator_tamper_reaches_public_driver_gate_g7` (4753) の exact refusal 集合は不変 (chain 由来の走査拒否を期待集合へ足さない)。

### E. 追随 pin

- `orchestrator/tests/test_ccbench_spawn_sites.py:3382` の driver evaluate sink 行番号 (現在 1788) を、同じ sink であることを確認して新行番号へ (allowlist 拡大・分類緩和はしない)。
- `LaunchValidatedFreeze(` の直接 constructor 7 箇所 (driver test 2835 / 2847 / 4112 / 4993、`test_s8b_oracle_report.py:477`、`test_s8b_gate_core_exact_launch_validated.py:50`、`test_s8b_holdout_admission.py:547`) に新 field を渡す。偽 token は委譲不能な root / report を明示する。
- 既存 `test_run_block_resolves_receipt_once_and_propagates_observation_to_wal_and_result` (3636 付近) の `call_count == 2` と epoch drift test (3677 付近) の 2 要素 side effect 列は P3' で維持できるはず — 変えずに通ることを確かめる。
- migration の例外正規化 test (563 付近) の root-only lambda が引数変更で TypeError にならないこと。

## 禁止 (必ず守る)

- **`git add` / `git commit` / `git stash` / `git checkout` / `git reset` を実行しない。commit は親が行う。** git は読取り (`log` / `show` / `diff` / `status` / `ls-tree`) だけ。
- **docs を編集しない** (`docs/` 配下、`docs/handoff/` への file 作成、README、runbook を含む)。insight・fragment も書かない。
- `output/s8b-freeze/` 配下と `output/` 配下の tracked file を書かない・消さない。走査除外 (`EXCLUDED_PATHS`、`exempt_exact` 導出)、growth hold (`orchestrator/tests/growth_test_holds.py`)、allowlist、`clean_scan_digest` の拒否、`_make_gate_decision` の集約、`_campaign_t080_value` の拒否、`launch_validate` の C2-4 とその他の層、`_t080_epoch_identity` の要素を変えない。skip flag / 環境変数 / 引数で層 2 を無条件免除する経路を作らない。
- **既存 test の期待値を緩めない** (反転・緩和・skip・削除・xfail 化を禁ずる)。赤なら実装側が誤り。期待値が誤りと考えるなら実装を変えず報告して止まる。登録簿の pin 追随 (34/37 → 8/8 等) は「実 consumer 集合の変更に対する exact pin 追随」だけに限る。
- 検査対象の機構 (`search_repository`、`_assert_search_pass`、`launch_validate`、`resolve_active_generation`、`verify_receipt` の内部) を monkeypatch しない。既存の外側 seam (`_gate_check_validated`、`_prepare_v2_execution`、`evaluate_fn` 等) は既存用途の範囲で使ってよい。fixture へ現行 hash を差し込んでテストを甘くしない。期待値に揮発 payload (tree hash 等) を焼き込まない。
- 新規 test file を作らない。gate・検査・台帳・tool の新設や一般化、互換層を足さない。指示外の受理集合変更をしない。
- 三軸の値 (holdout の workload 定義) を出力や test の literal に逐語で書かない (`_holdout_hit_text` 等の既存 helper を使う)。
- pytest / `tools/run_tests.py` を走らせられない (sandbox が socket を拒否)。走らせていない結果を緑と書かない。

## 自己検証 (pytest の代わりに必ず行う)

実走できないので、最低限 (1) 変更した各 test module を import して対象 test 関数を直接呼び出し (`tmp_path` は `tempfile.mkdtemp()` で代用)、fixture が成立するか確かめる、(2) 委譲 predicate の各負例について、実行時に対象の比較を一時的に除去 (process 内の属性差替え) して期待どおり赤化するか確かめる (反実仮想)。接続正例 (C) は実際に `active-valid` が得られたかを直接呼出しで確かめ、結果 (`DIRECT_CALL_PASS` / 失敗した検査名と detail) を報告に載せる。所有外の caller・共有 fixture・consumer test への波及を静的に列挙する (`grep -rn` で `LaunchValidatedFreeze(`、`verify_receipt(`、`_resolve_t080_receipt`、`patch_driver_resolver`、`RECEIPT_MEMO_CONSUMER_NODES` を引く)。

**実走と報告を最優先にし、残り時間が少ないと感じたらその時点の結論を出力形式どおりに書いて終わる。無出力が最悪。** 未完の部分は「実装済み・未実走」「未着手」を区別して書く。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。見出しはすべて `##` (H2)、最後の節は必ず `## 総括`。

節の順:

## 実装した変更 (file ごと、関数名と要点)
## 委譲 predicate の署名と発火条件 (現物の逐語)
## driver の呼出し順 (gate_check / run_block / campaign-start 前)
## 接続正例 fixture の結果 (active-valid に到達したか、障害の現物)
## 4 経路の切り離し (S、各経路の変更、登録簿の追随)
## 追加・変更した test の nodeid 一覧 (正例 / 負例 / 対照の別)
## 自己検証の結果 (直接呼出し・反実仮想)
## 所有外への波及 (静的列挙)
## 変異事前登録への対応 (s4 の m0〜m11 それぞれの anchor 位置 = file と old 逐語の候補)
## 未完・未実走・懸念
## 総括
