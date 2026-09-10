単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s4-adjudication.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s4-adjudication.md` — 親の段 4 裁定 (plan v2、変異事前登録、不変 pin 表)
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s6-review-a.md` — 段 6 レビュー A (blocker 1 / must-fix 2)
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s6-review-b.md` — 段 6 レビュー B (blocker 1 / must-fix 4 / nit 1、変異帰属表)
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/prompt-s5-unit1.md` と `prompt-s5-unit2.md` — 段 5 実装子の契約 (**全文継承する**: 権限、テスト弱体化禁止、受理集合、波及報告)
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s5-integrated.patch` — 統合後の実装差分 (本 worktree に適用済み)

作業 repository は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-b2-d1-fix1` (branch `fix-dev-wave-t1851-b2-d1-1`、base `50dbf9158` + 統合 patch 適用済み、未 commit) である。

## 所有 path (これ以外は 1 byte も変更しない)

- `orchestrator/tests/test_s8b_floor_stats.py`
- `orchestrator/tests/test_s8b_floor_contract.py`
- `orchestrator/tests/test_s8b_attempt_registry.py`
- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py`

**production 4 file (`attempt_registry_core.py` / `s8b_attempt_registry.py` / `s8b_floor_contract.py` / `s8b_floor_stats.py`) は両レビューが裁定どおりと判定した。変更しない。**
production を変えないと閉じられない所見が見つかったら、実装せず完了報告に書け。docs の編集と commit はしない。

## 依頼 — 段 6 fix 1 (test 側のみ)

親の裁定 (所見ごと) は次のとおり。全件 real / 採用。

### F1 (A-1 / B-1、blocker) — M14 の実台帳 2 世代 test を `test_s8b_floor_stats.py` に追加する

同じ shared admission root に**有効な v2 世代 A と B** (freeze / protocol / schedule のいずれかが異なる binding) を実 API で作る
(`test_s8b_attempt_registry.py` の `_v2_registry_capability_case()` / `_reserve_v2()` と同じ経路。helper を import できないなら最小の同型 helper を stats test 側に置き、
production adapter 経由で行を積む。手書き行は不可)。artifact と reported proof は世代 B の `{N, head}` と binding を持ち、`verify_floor_artifact_with_live_admission` の
外部引数 (freeze_sha256 / protocol / schedule) は世代 A を指す。**正しい実装は A を replay して binding mismatch (または head mismatch) で拒否し、
M14 変異 (expected binding を reported proof から採る) だけが B を replay して受理する**単一理由形にする。同じ test に、外部引数と artifact が共に A を指す**受理正例**を置く。
inspector は monkeypatch しない (実 `inspect_attempt_registry_prefix` を通す)。live wrapper が要求する holdout admission 側の引数
(`verified_freeze_document` / `cells` / `schedule` / `sessions` / mode 等) は既存の live wrapper test (`test_live_verifier_rejects_both_refreeze_mismatch_directions` 等) の
fixture 構成を再利用する。

### F2 (A-2 / B-4、must-fix) — v5 test の validator stub を除去する

`_v5_artifact()` 等の共通 helper が `validate_attempt_registry_prefix_proof` を手書き再実装へ無条件 monkeypatch している (`test_s8b_floor_stats.py:646, 696` 付近)。
統合後は production validator が実在するので、**通常時の monkeypatch を除去し、production literal と production validator で v5 fixture を検証する**。
pure verifier の結合 test は、production validator を包む spy を差し込み、reported と expected の **2 回呼ばれた**ことを assert し、production validator の正例と
malformed 負例 (bool の N / zero head / wrong schema) を同じ test に置く (D1522)。`raising=False` は除去する (属性は実在する)。
fake inspector test (`test_live_v5_calls_inspector_and_compares_reported_to_independent_proof`) では、期待 freeze を artifact からでなく**外部引数から**独立に再導出し、
同じ test 内に live wrapper を通る受理正例を置く。

### F3 (A-3、must-fix) — 不変 pin node を base へ戻す

`test_s8b_floor_contract.py::test_floor_campaign_directly_reexports_shared_leaf_objects` (`:164` 付近) へ追加した 7 行を除去し、node を base (`50dbf9158`) の bytes と完全一致へ戻す。
LEGACY / V5 / readable 集合の assertion は**新規 test node** へ移す。`test_result_v4_key_contract_is_mode_conditional_and_exact` は不変 pin 表に無いので拡張のままでよいが、
既存 assertion を 1 行も削らない。

### F4 (B-2、must-fix) — M10 の再照準

`test_attempt_registry_prefix_rejects_synthetic_v1_at_generation_path` (`test_s8b_attempt_registry.py:3455` 付近) の合成 v1 を、
test 固有の recovery authority ではなく **production の `scheduler.AUTHORITY_ID` / `scheduler.AUTHORITY_POLICY_SHA256`** で作り、v2 schema guard を消したときに
後段 (`_profile_and_binding_for_generation` の recovery digest gate、`core.load_attempt_registry`) まで**成功して受理される**入力にする。
現行 (guard あり) では `attempt-registry-generation-unsupported` で拒否されることを assert し、guard 以外の gate がこの入力を拒否しないことを test 内で示す
(例: guard を monkeypatch で無効化した対照で replay が成功する、または v1 profile での `read_attempt_registry` 相当が通る)。

### F5 (B-3、must-fix) — M13 の再照準

`test_live_v4_does_not_call_attempt_registry_inspector` (`test_s8b_floor_stats.py:848` 付近) で、この test に限り `validate_attempt_registry_prefix_proof` を
「None を受けても有効な proof を返す」seam に差し替え、v5-only guard を消したときだけ inspector tripwire へ到達する形にする。正しい v4 経路の `[]` 正例は維持する。
seam の差し替えが実際に呼ばれうることを (別 node の正例対照で) 示す。

### F6 (B-5、must-fix) — 複数 gate に掛かる負例を診断 node と明記する

`test_attempt_registry_prefix_rejects_genesis_binding_substitution` と `test_v5_rejects_proof_binding_mismatch[freeze|protocol]` は、対象 gate を消しても後段が拒否する。
docstring または名前で**診断 node** (変異の観測に使わない、reason の順序を固定する pin) と明記する。再照準は不要。削除もしない。

### F7 (B-6、nit) — M2 の観測 node

`test_attempt_registry_prefix_proof_rejects_each_field_type` の parametrize id を、digest 4 field / literal 2 field / row_count が区別できる id にする (親が変異台帳で digest parameter だけを M2 に割り当てる)。

## 検査・報告

- 実走できる範囲で `python3 -m pytest orchestrator/tests/test_s8b_floor_stats.py orchestrator/tests/test_s8b_floor_contract.py orchestrator/tests/test_s8b_attempt_registry.py orchestrator/tests/test_attempt_registry_core_s8b_profile.py -q` を走らせ、
  緑には実走 nodeid・範囲を併記する。実走不能なら `closed` と申告せず「実装済み・未実走」と書く。
- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除を禁じる。赤なら実装側が誤りとし、期待値が誤りなら実装を変えず報告して止める。
- 所見ごとの closed / partial / regressed 対応表を完了報告に置く。
- 不変 pin 表の node は F3 で base へ戻す以外 1 行も変えない。
- commit しない。docs を編集しない。

## 制約

- 出力へ結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力の最後に `## 総括` 節を置き、所見 F1〜F7 の closed / partial / regressed、変更 file と行数、実走結果、production 変更が必要と判明した点を 10 行以内で書け。
