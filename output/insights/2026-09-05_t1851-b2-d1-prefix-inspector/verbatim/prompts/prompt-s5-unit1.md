単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s4-adjudication.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s4-adjudication.md` — 親の段 4 裁定。**plan v2 節・変異事前登録・不変 pin 表が本作業の契約**であり、段 2 plan と食い違う点はこちらが正しい
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s2-plan.md` — 段 2 plan。1〜3 節 (B2-a / inspection / D1-b)、8 節 (テスト計画)、9 節 ((P3) 到達可能性) が unit 1 の土台
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s3-lens-a.md` と `s3-lens-b.md` — 段 3 の敵対所見。裁定で「採用」とされた所見の (d) 修正案を実装に反映する
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s1-brief.md` — 親 brief (件数は裁定末尾の訂正が優先)
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/decisions-verbatim.md` — 確定裁定の逐語 (特に D1337 / D1522 / D1533)

作業 repository は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-b2-d1-unit1` (branch `impl-dev-wave-t1851-b2-d1-unit1`、base `50dbf9158`) である。コードはすべてこの worktree の中で読み書きする。

## 所有 path (これ以外は 1 byte も変更しない)

- `orchestrator/campaign/attempt_registry_core.py`
- `orchestrator/campaign/s8b_attempt_registry.py`
- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py`
- `orchestrator/tests/test_s8b_attempt_registry.py`

`s8b_holdout_admission.py`、`s8b_floor_contract.py`、`s8b_floor_stats.py`、docs、他の test file は所有外である。所有外に必要な変更が見つかったら実装せず完了報告に書け。docs の編集と commit はしない。

## 依頼 — unit 1: D1-b (proof 型) → B2-a (read-only prefix inspector)

裁定の plan v2 節 1〜4 と 8 節を実装する。順序は D1-b → B2-a。

### D1-b (`attempt_registry_core.py`)

- `ATTEMPT_REGISTRY_PREFIX_PROOF_SCHEMA = "s8b-floor-attempt-registry-proof/v1"`、`ATTEMPT_REGISTRY_PREFIX_PROOF_KEYS` (exact 7 key)、
  `validate_attempt_registry_prefix_proof(value: object) -> dict[str, object]` を chain primitive の近傍に置く。
- 検査: Mapping かつ exact 7 key、`schema` は proof literal、`registry_schema` は **exact literal** (v2 registry schema 定数。core は
  `s8b_attempt_profile` を import できないので、literal は引数 `expected_registry_schema` で受けるか、core に定数を置いて profile 側が参照する形の
  どちらかを選び、理由を報告に書け。呼び手が任意の文字列を通せる形にはしない)、4 digest は lowercase hex64、`row_count` は bool を除く正整数、
  `chain_head_sha256` は zero SHA ではない。fresh な plain dict を固定順で返す。
- 等値 (`chain_head_sha256 == rows[N-1].event_sha256`) は validator の保証にしない。

### B2-a (`s8b_attempt_registry.py`)

- `capture_attempt_registry_prefix(repo_root, *, expected_binding)` と
  `inspect_attempt_registry_prefix(repo_root, *, expected_binding, row_count, chain_head_sha256)` を公開 API として置く。戻り値は exact 7 key の proof dict。
- **root:** `admission.shared_admission_root(repo_root)` だけで解決する。root / lock inode が無ければ作らず
  `FloorHoldoutEvidenceError(category="unverifiable", reason="attempt-registry-root-unavailable")` で拒否する。
  `_entry_paths` / `provision_shared_admission_root` / `admission._locked` / fsync helper を**呼ばない**。lock は `admission._locked_readonly(root)`。
- **path:** `_relative_registry_path(freeze, protocol_sha256=protocol)` で exact 2 段 path を解決し、`admission._assert_no_symlink_components` と
  lstat (regular file、no-follow) を通してから `_read_regular_bytes` で読む。**兄弟世代を列挙しない** (`_registry_generation_paths_locked` を呼ばない)。
- **replay:** genesis を peek し `schema_version` が v2 でなければ `mismatch` / `attempt-registry-generation-unsupported`。
  `_profile_and_binding_for_generation` で profile と binding を構築し、genesis の binding が `expected_binding` と一致しなければ `mismatch` /
  `attempt-registry-binding-mismatch`。`core.load_attempt_registry(payload, profile=..., expected_binding=...)` で**その世代の全行**を replay する。
  他世代の予算 count は seed しない。docstring に「他世代の予算超過は検査しない (writer の防壁)。台帳の削除後同一 bytes 再作成は防がない (D1533)」を書く。
- **inspection:** full replay 成功後だけ `len(rows) >= row_count` (`mismatch` / `attempt-registry-prefix-too-short`) と
  `rows[row_count - 1]["event_sha256"] == chain_head_sha256` (`mismatch` / `attempt-registry-prefix-head-mismatch`)。`rows[-1]` は使わない。
  戻り値の `row_count` / `chain_head_sha256` は reported 値を保持する。capture は `len(rows)` と `rows[-1]["event_sha256"]` を返す。
- core / adapter の例外は `FloorHoldoutEvidenceError(category="mismatch", reason="attempt-registry-replay-invalid")` へ写す。read 失敗は `unverifiable` / `attempt-registry-read-unavailable`。
- 既存 symbol (`read_attempt_registry`、`_entry_paths`、v1 reader / writer、recovery 経路) は変えない。

### テスト (裁定の変異事前登録 M1〜M6、M8〜M10、M17、M18 を観測する node を必ず置く)

`test_attempt_registry_core_s8b_profile.py` (D1-b 直接、16 node 目安): 正例、field 欠落、余分 key、各 7 field の型違反、row_count 0、bool、hex 不正 4、zero head、wrong proof schema、wrong registry schema。

`test_s8b_attempt_registry.py` (B2-a、既存 helper `_v2_registry_capability_case()` / `_reserve_v2()` を使う):

- 正例: N=1 (genesis-only)、N=3 (reserve 後: start + pre-observation-seal)、N=4 (classification 後)、N=5 (observation-start 後) の capture と inspection。
  valid append: N=3 の proof を取った後に classification を積み、inspection が受理する (M9 の観測 node)。
- 正例: unsafe な兄弟世代 (symlink または registry 欠落の 64hex directory) を同じ freeze 配下に置いても current prefix の inspection が通る。
- 負例 (各負例は valid な v2 path、valid な proof shape、正しい他 binding を維持し、対象 gate 以外では拒否されない形にする):
  N 以後 invalid JSON (M5)、N 以後 chain 切断 (M6)、reported head 改竄 — **改変後に N 以後まで全 hash を再計算した入力** (M8)、
  N 行内の未再計算改変 (`_assert_chain` が拒否する診断 node、別 node にする)、`N > len(rows)`、
  exact 2 段 path に置いた合成 v1 (genesis schema v1) が `attempt-registry-generation-unsupported` で拒否される (M10)、
  freeze / protocol / schedule の各 binding 差替え (genesis の binding と `expected_binding` の不一致)。
- read-only: `provision_shared_admission_root` / `_entry_paths` / `admission._locked` を monkeypatch で tripwire (呼ばれたら失敗) にして inspection が通る node (M18)、
  および inspection 前後で root 配下の全 file の bytes と inode (`os.lstat` の st_ino / st_mtime_ns) が不変である node。root 不在で `unverifiable` になる node。
- D1522: 上流が拒否する形でも、下層 (core validator、replay helper) の実体を名指しする直接検査を置き、差し替えが実際に呼ばれたことを assert し、
  差し替えなしで成功する正例対照を同じ test に置く。

## 検査・報告 (DW-S05-C)

- 実走できる範囲で `python3 -m pytest orchestrator/tests/test_attempt_registry_core_s8b_profile.py orchestrator/tests/test_s8b_attempt_registry.py -q` を走らせ、
  緑には実走 nodeid・範囲を併記する。実走不能なら `closed` と申告せず「実装済み・未実走」と書く。sandbox の都合で走らないなら、その理由を書け。
- テスト新設の単位は、親の名指しを網羅と見なさず制約 meta-test (`test_s8b_attempt_registry.py:1729-1775` の direct import 禁止、file 列挙 meta-test、
  `test_check_docs` 系) を自ら洗い出して走らせる。新規 test file は作らない。
- fixture へ現行 hash を差し込むなど、テストを甘くして緑にしない。機構の正例・負例は実体を名指しし依存先を stub しない (tripwire は例外)。
- 期待値へ揮発 payload を焼き込まない。
- 完了報告に、所有外 caller・共有 fixture・consumer test の波及可能性を静的列挙する。
- 指示外の受理集合変更をしない。scope 前の受理・拒否挙動 (v1 不変、v2 terminal の二層拒否不変、既存 reader 不変) を報告に明記する。
- 不変 pin 表 (裁定) の node は 1 行も変えない。
- commit しない。docs を編集しない。

## 制約

- 出力へ結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力の最後に `## 総括` 節を置き、変更 file と行数、新設 test node 数、実走結果 (nodeid 範囲と passed / failed 件数)、所有外への波及、未実装項目を 10 行以内で書け。
