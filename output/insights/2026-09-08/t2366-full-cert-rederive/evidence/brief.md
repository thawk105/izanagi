# [T-2366] 段 1 brief — full certification の materializer に exact 再導出を入れる

- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive` (branch `worktree-dev-wave-t2366-full-cert-rederive`、base = local main `34af5a571` = origin/main、clean、submodule 初期化済み、起動 gate fresh rc=0)
- 依頼 (ユーザー、2026-09-08): full certification の materializer に exact 再導出を入れる。partial 側の既存実装を**そのまま射影**し、新しい検査層は作らない。変異で「再導出を外すと赤になる」ことを示し、正例・負例は性質でなく実体を名指しする。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外。規律 2 を緩めない。Codex author = D95。
- 既裁定: D1259 (2026-08-28) が partial 側の「materialize 時に completion / acquisition / manifest から authority・cells・effects・status を再導出して report 全体と比較する」を採用。D1692 (2026-09-07) が「full 側へ同じ再導出を入れる」を既存の非対称として別項 (= 本 T-2366) へ送った。両 D と本依頼に矛盾なし。
- 対象 file (実装面、Codex author): `orchestrator/campaign/paper_story_a2_certification.py` と `orchestrator/tests/test_paper_story_a2_certification.py` の 2 file だけ。

## 現物の非対称 (親が 2026-09-08 に読んで確認、行番号は base 34af5a571)

- partial (v2 report = `PARTIAL_CERTIFICATION_SCHEMA`): `_validate_certification_result` (4364〜) が `evidence["acquisition_path"]` から `validate_acquisition_bundle` (1725) で evidence を**読み直し**、`_canonical_partial_report` (2861) で report を再導出し、`report == expected` でなければ `CertificationError("partial certification result differs from evidence re-derivation")` (4428〜4435)。戻り値は読み直した `canonical_evidence`。legacy v1 は identity 比較のみ (4409〜4427)。
- full (v4 report = `CERTIFICATION_SCHEMA`): 同関数 4437〜4528 は key 集合・identity (study / protocol / policy bytes / attempt_id / current_pin / source_commit) / schema chain / request_ids / 固定 field / cells の形だけを見る。`status`・`cells`・`effects`・`reason` が evidence から導かれるかは**見ない**。よって偽 `status`、改竄 `effects`、失敗 evidence 上の捏造 positive が現行では tracked 成果物として公開される。
- full の report 生成経路は `_collect_command` (4720〜4770) の else 枝だけ: driver 非 0 → `_indeterminate_report` (4688) / manifest 無効 → `_indeterminate_report` / それ以外 → `collect_results` (2712) + `report["source_commit"] = evidence["source_commit"]`、例外 (`CertificationError, OSError, ValueError, TypeError, KeyError, IndexError`) → `_indeterminate_report(reason=str(exc))`、`AuthorityError` は伝播。partial は同じ経路を `_canonical_partial_report` に切り出して collector と validator の両方から呼ぶ。
- 再導出に要る evidence field は `validate_acquisition_bundle` の戻り値 (1806〜1836) に実在する: `acquisition_path`, `attempt_id`, `attempt_root`, `request_ids`, `source_commit`, `driver_rcs`, `raw_manifest_valid`, `raw_manifest_reason`, `raw_results`, `raw_files`。
- 既存の full 正例: `test_p2_a6_full_v3_path_collects_and_materializes` (test 2418)、`test_synthetic_pbs_free_preregister_through_analyze_positive` (test 5275)。partial の負例定型: `test_m7_partial_materializer_rejects_forged_authority_and_status` (2995)、`test_m8_...` (3009)、fixture `_partial_materializer_forgery_case`。
- `_COLLECT_TEST_TOKEN` を渡す既存 test (2106, 2150, 2446, 3544, 3558, 4043) は `collect_results` 止まりで materialize へ進まないので再導出の影響を受けない。
- production の呼び手は `_collect_command` (CLI `collect`) のみ。`materialize` を直接呼ぶ他 module は無い (grep 済み)。

## scope (本体実装)

1. `_collect_command` の else 枝 (4733〜4767) を `_canonical_full_report(policy, evidence, *, attempt_id, current_pin)` に切り出す (partial の `_canonical_partial_report` と同型)。`_collect_command` はそれを呼ぶだけにする。挙動・report bytes は不変。
2. `_validate_certification_result` の v4 full 枝で、既存の形・identity 検査の**後**に partial 側の再導出一致をそのまま射影する: `evidence["acquisition_path"]` から `validate_acquisition_bundle(policy, path, current_pin=report["current_pin"])` で読み直し (P1)、`_canonical_full_report` で expected を作り、`report != expected` なら `CertificationError("certification result differs from evidence re-derivation")`。戻り値は読み直した canonical evidence (partial と同じ)。legacy v3 full は partial legacy v1 と同じく identity 比較のみで据え置く。
3. テスト: 負例は現行コードで**通ってしまう**偽造 report を実体で名指しする — (a) 正の evidence 上で `status` を `observed-positive` → `reject` に書き換え、(b) `effects` の値を書き換え、(c) driver 全成功の evidence に対して `_indeterminate_report` 形 (cells 空・reason 付き) を渡す、いずれも `match="differs from evidence re-derivation"` で拒否され tracked destination が作られないこと。正例は既存 2418 / 5275 が緑のまま (過剰拒否の正例)。
4. 変異 (段 4 で事前登録、段 6 で本走): 「`report != expected` の比較を外す」変異が新負例で KILLED、「常に raise」変異が既存正例で KILLED (過剰拒否の正例)、等価変異 1 件 SURVIVED。

## 不変条件

- 規律 2: 受理集合は縮小のみ。v4 full の report bytes・schema 識別子・`COMPLETE.json` / manifest の形は変えない。既存テストの期待値を緩めない。
- 新しい検査層・gate・台帳・schema 版・一般化を作らない。「partial の関数を full に写す」以上をしない。
- legacy v3 full / legacy v1 partial の identity-only 経路は触らない (D1259 却下案「full も v4 へ移す」と同じ理由で、既存完走 artifact の受理集合を変えない)。
- push 禁止、実装面は Codex author のみ、親は docs だけ。

## 攻撃対象 (provisional 裁定)

- (P1) 再導出の evidence は `materialize` へ渡された dict でなく `acquisition_path` から**読み直す** (partial と同型)。渡された dict を使う案は「凍結 bytes と一致することを別途検査する層」が要るので採らない。
- (P2) test 5275 は `load_raw_results` + `frozen_files` なしで report を作っている。再導出 (evidence["raw_results"] + raw_files + attempt_root) と report が一致せず赤になるなら、期待値でなく report の**構築**を collector と同型 (2418 と同じ) に寄せる。それでも一致しないなら実装の誤りとして止める。
- (P3) `_canonical_full_report` 内の例外 → indeterminate の畳み込みは現行 `_collect_command` と 1 byte も変えない (再導出が collector と同じ report を返すことが一致条件の前提)。
- (P4) `materialize` が書く receipt / manifest bytes は読み直した canonical evidence のものにする (partial と同じ)。渡された evidence の bytes と食い違う入力は、再導出以前に `validate_acquisition_bundle` が sha で拒否する。

## 成果物

- 統合 commit 1 本 (実装 + テスト、Codex author trailer)。段 6 で敵対レビュー 2 本 (A: 正しさ防壁・受理集合、B: 射影の忠実さ・collector との同一性) + 変異 matrix + 受入全走。段 7 で insight `output/insights/2026-09-08_t2366-full-cert-rederive/` と worklog / decisions fragment。
- 分割方針: 実装単位 1 (author 子 1 本、2 file は密結合)。新規 test node を足すので受入所要時間台帳 (`orchestrator/tests/acceptance_duration_ledger.json`) の登録が要る (正本 producer の `--add-only`)。同台帳は稼働中 T-2412 も触るため main 取り込みで和集合合成 (F902 型) を想定。
- 実測環境: テスト・変異・受入は Pegasus login node の `tools/run_tests.py` 自動判定 / dispatch。計算ノード実走なし。
- DW-G05 (成果物影響): 放置すると、A-2 の full certification で status / cells / effects が evidence と食い違う report が tracked 成果物として公開されうる (partial 側は D1259 以降拒否)。本 wave は受理集合を「evidence から再導出した report と一致するもの」へ縮める。
