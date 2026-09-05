# [T-1851] 段 4 裁定 — B2 (prefix inspector) と D1 (契約・proof 型) の非 terminal 部分

親裁定。tip `50dbf9158`。材料 = 段 1 brief、段 2 plan (`artifacts/t1851-b2-d1/s2-plan.md`)、
段 3 レンズ A (`s3-lens-a.md`、blocker 4 / must-fix 4 / nit 1) とレンズ B (`s3-lens-b.md`、blocker 4 / must-fix 6 / nit 1)、
親の独立検算 (下記)。

## 結論 — 実装する。1 wave、実装子 2 本 (file 所有は素)、plan v2 は本裁定で確定する

段 5・6 へ進む。D1341 により本 wave は land しない (unlanded checkpoint)。

## 親の独立検算 (レンズが依拠した現物を親が読んだ)

- `_entry_paths()` (`s8b_attempt_registry.py:520-543`) は `provision_shared_admission_root()` と fsync を必ず実行する。
  read-only API がこれを再利用すると書込みになる (A-3 / B-2 は real)。非 provisioning の `shared_admission_root()` は `:620` に実在する。
- pure verifier `verify_floor_artifact` (`s8b_floor_stats.py:682-1033`) は artifact の `freeze_sha256` / `protocol_sha256` を
  どの外部値とも比較していない (A-1 / B-3 は real)。
- `_registry_generation_paths_locked()` (`:649-724`) は freeze 配下の 64hex 兄弟をすべて lstat し、1 つでも symlink / 非 directory /
  registry 欠落なら `_fail` する (B-1 は real)。exact path は `_relative_registry_path(freeze, protocol)` (`:531`) で解決できる。
- 既存の production reader `read_attempt_registry()` (`:1631-1654`) は current generation だけを `core.load_attempt_registry()` へ渡し、
  他世代の予算 count を seed しない。他世代 seed は writer 側 `_atomic_update_locked` の経路 (`:1392`) だけである。
- `result_keys_for_mode(` の呼出し式は orchestrator 配下で 12 件 (production 3 / test 9)。brief の 22 件は insight 文書を含めた誤り。
- `_reserve_v2()` (`test_s8b_attempt_registry.py:288-313`) は B1 capability を渡して production adapter で start を積む。
  実アンカー表の行番号は両レンズとも全件一致と判定した。

## 所見の real / refuted と採否

### レンズ A

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A-1 | proof と artifact header (freeze / protocol) の相互束縛が無い | **real / blocker** | 採用。v5 pure verifier は `proof.freeze_sha256 == artifact.freeze_sha256`、`proof.protocol_sha256 == artifact.protocol_sha256` を先に検査する。schedule は artifact に同名 field が無いので wrapper が外部 schedule から再計算した digest との比較だけ。header 単独改変の負例 2 node |
| A-2 | M14 は別世代台帳への差替えを殺せない | **real / blocker** | 採用。同じ root に有効な v2 世代 A / B を作り、artifact / proof は B、wrapper の外部引数は A とする実台帳 test を M14 の観測 node にする。**この test は unit 1 の実装が要るので段 6 (統合後) に fix 子が足す。** 段 5 の unit 2 は fake inspector 版 (B-9 の形) を先に置く |
| A-3 | read-only API の root 解決が未規定で `_entry_paths` は書く | **real / blocker** | 採用。root は `admission.shared_admission_root(repo_root)` だけで解決し、root / lock 不在は作らず `unverifiable`。`provision_shared_admission_root` / `_entry_paths` / `admission._locked` / fsync helper を tripwire にした test と、呼出し前後で tree が byte-for-byte・inode 不変の test を置く |
| A-4 | D1340 の世代横断予算 replay が inspector から落ちている | **real だが本 wave では refuted as blocker** | **不採用 (scope 外)。** D1340 は予算を数える writer の規則であり、既存 production reader も他世代を seed しない。D1337 が定める proof の identity は世代別台帳の `{N, head_at_N}` である。検証時に freeze-wide 予算を再導出する gate は確定裁定が要求しておらず、DW-G05 の「要求外の gate を足さない」に当たる。**inspector の docstring と README に「他世代の予算超過は検査しない (writer の防壁)」を非保証として明記し (D1533 の形)、裁定パッケージへ送る** |
| A-5 | N 行内改変の拒否理由が誤っている (再 chain すると full replay は通る) | **real / must-fix** | 採用。負例を 2 つに分ける。未再計算改変 → `_assert_chain` が拒否 (診断 node、変異の観測に使わない)。genesis を含む改変後に N 以後まで全 hash を再計算した入力 → `rows[N-1] == reported head` だけが拒否 (M8 の観測 node) |
| A-6 | (P3) の到達可能な v2 行集合が狭すぎる | **real / must-fix** | 採用。正例を N=1 (genesis)、N=3 (reserve: start + pre-observation-seal)、N=4 (classification)、N=5 (observation-start) に広げる。valid append は N=3 の proof の後に classification を積んで検査する。terminal は正例に入れない。**(P3) は値域を訂正して採用** |
| A-7 | v4 の直接下層検査が D1522 を満たさない | **real / must-fix** | 採用。contract test で pilot / official × perf の各 v4 key set を直接取得し `"attempt_registry" not in keys` を literal で固定する。変異 M15 (v4 key set へ field 追加) を登録する |
| A-8 | 単位 C が supersede する pin の一覧が無い | **real / must-fix** | 採用。移行表を本裁定 (下記) と insight README に固定する。本 wave では fixture を変えない |
| A-9 | brief の件数誤り (22 → 12、6 file → 意味的 5 file、`output/` は「result JSON bytes 0 件」) | **real / nit** | 採用。brief 訂正として本裁定に記録 |
| A-10 | coverage の exact signature を C より先に固定できない | **real / 裁定パッケージ候補** | 採用。plan 6 節の coverage signature は「意味要件」に格下げし、exact signature は固定しない |
| A-11 | D1533 の非保証範囲を成果物へ載せる所有者が無い | **real / 裁定パッケージ候補** | 採用。単位 C の brief へ送る |

### レンズ B

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| B-1 | 全世代列挙は無関係な兄弟世代の破損で current prefix を拒否する | **real / blocker** | 採用。inspector は `expected_binding` の freeze / protocol から exact 2 段 path を `_relative_registry_path` で解決し、`_assert_no_symlink_components` + lstat regular file で**その file だけ**を読む。全世代列挙は使わない。unsafe な兄弟世代を置いても current prefix が通る正例を追加する |
| B-2 | read-only の root 解決 | **real / blocker** | A-3 と同一。採用 |
| B-3 | proof と artifact header の相互束縛 | **real / blocker** | A-1 と同一。採用 |
| B-4 | 1 wave・実装子 1 本・fix 3 巡は支持できない | **real (実装子 1 本の前提) / 分割は不採用** | **(P5) は条件付き採用。** plan どおり実装子 2 本を並列に投入する (file 所有は素)。段 6 で unit 2 (契約 / verifier) が fix 3 巡で閉じなければ、unit 1 (proof 型 + inspector) だけを checkpoint にし unit 2 を次 wave へ送る。これは plan の安定境界 `D1-b + B2-a` → `D1-a + c + d` と同じであり、事前に 2 wave へ割る必要は無い |
| B-5 | 回帰 consumer 閉包を 84 node と一般化できない | **real / must-fix (報告)** | 採用。84 は「直接 focus node」。`_run_campaign()` 105 / `candidate_repository()` 31 / `_build_independent_launch_repo()` 9 / G1 emitter 3 / `build_floor_admission_evidence()` 8 の fixture family を回帰閉包として別計上する。焦点走 file 集合は段 1 baseline の 20 file (campaign / holdout_freeze / ratified を含む) をそのまま使う |
| B-6 | supersede 禁止 pin が S5 (core) と v2 空集合 pin を落としている | **real / must-fix** | 採用。不変 pin 表 (下記) に追加 |
| B-7 | proof validator が `registry_schema` の literal を閉じていない | **real / must-fix** | 採用。`registry_schema` を exact literal (`s8b_attempt_profile` の v2 schema 定数) にする。wrong proof schema / wrong registry schema / v5 で expected None / v4 で expected 非 None の直接 node を追加。変異 M17 |
| B-8 | (P3) の値域が過小 (N=1, 3, 4, 5) | **real / must-fix** | A-6 と同一。採用。consumption marker は行ではない |
| B-9 | 変異候補 4 組の帰属不成立 (M1 / M7 / M10 / M14) | **real / must-fix** | 採用。M1 は extra-key node だけを KILL 期待、missing-key は診断。**M7 は単一理由に絞れないので登録しない** (`N > len(rows)` の負例は test として残す)。M10 は expected protocol の exact 2 段 path に置いた合成 v1 (genesis schema v1) を使う。M12 は pure verifier 直接。M14 は A-2 の実台帳 2 世代 test (段 6) を正とし、段 5 では fake inspector 版で呼出しと binding の向きを固定する |
| B-10 | brief の件数一般化の誤り、実アンカー・merge 主張は正しい | **real / nit** | 採用 (A-9 と同一) |
| B-11 | import graph の辺 (`registry → admission → ratified → stats`) | **real / nit** | 採用。stats wrapper 内で `from . import s8b_attempt_registry` を局所 import。test は module 属性を monkeypatch し「1 回呼ばれた」を assert。admission には import を足さない |
| B-裁定候補 1 | D2 の v5-only 化で fixture 2 件が transitive に赤 | **real / 裁定パッケージ候補** | 採用 (D2 所有)。本 wave は fixture を変えない |
| B-裁定候補 2 | 単位 C は基準 hunk を取り直す | **real / 記録** | 採用 |

## plan v2 (段 2 plan を次で上書きする。他は plan のまま)

1. **root と path (A-3 / B-1 / B-2):** `root = admission.shared_admission_root(repo_root)`。root / lock inode が無ければ作らず
   `FloorHoldoutEvidenceError(category="unverifiable", reason="attempt-registry-root-unavailable")`。lock は `_locked_readonly(root)`。
   registry path は `root.joinpath(*_relative_registry_path(freeze, protocol_sha256=protocol).parts)` を `_assert_no_symlink_components` と
   lstat (regular file、no-follow) で検査してから `_read_regular_bytes` で読む。**兄弟世代は列挙しない。** `_entry_paths` /
   `provision_shared_admission_root` / `admission._locked` / fsync helper を呼ばない。
2. **replay:** genesis peek → `schema_version == S8B_V2_ATTEMPT_REGISTRY_SCHEMA_VERSION` でなければ `mismatch` /
   `attempt-registry-generation-unsupported` → `_profile_and_binding_for_generation` → `core.load_attempt_registry(payload, profile, expected_binding)`
   で**その世代の全行**を replay。他世代の予算 count は seed しない (非保証として docstring に明記)。
3. **inspection:** full replay 成功後だけ `len(rows) >= row_count` (`mismatch` / `attempt-registry-prefix-too-short`) と
   `rows[row_count - 1]["event_sha256"] == chain_head_sha256` (`mismatch` / `attempt-registry-prefix-head-mismatch`)。`rows[-1]` は使わない。
   戻り値は reported の N / head を保持した exact 7 key (plan 1 節)。
4. **proof validator (D1-b):** exact 7 key。`schema` と `registry_schema` は**両方 exact literal**。4 digest は lowercase hex64、
   `row_count` は bool を除く正整数、head は zero SHA ではない。等値の実体は B2-a だけが保証する。
5. **pure verifier (D1-c):** v5 は `attempt_registry` を D1-b で検査 → `proof.freeze_sha256 == artifact["freeze_sha256"]`、
   `proof.protocol_sha256 == artifact["protocol_sha256"]` → `expected_attempt_registry` (非 None 必須、同 validator を通す) と
   `reported == expected` の 7 field 等値。v4 では `expected_attempt_registry` 非 None を caller 契約違反として拒否し、
   top-level `attempt_registry` は既存 exact key 経路で拒否。v3 等は既存 error 文字列を保存。
6. **live wrapper (D1-d):** schema が v5 のときだけ局所 import した `s8b_attempt_registry.inspect_attempt_registry_prefix` を呼ぶ。
   expected binding は外部引数だけから (freeze = 引数、protocol = `canonical_protocol_sha256(protocol)`、
   schedule = `sha256(canonical_json_bytes(list(schedule)))`)。reported proof の binding を path 選択にも expected にも使わない。
7. **契約 (D1-a):** plan 4 節のとおり。`RESULT_SCHEMA` の値は v4 のまま (P1)、`schema` kw-only default = legacy v4 (P4)。
   v4 key set を直接 literal で pin する test (A-7)。
8. **coverage (実装しない):** plan 6 節の signature は「意味要件 (result attempt identity ↔ prefix 内 sealed terminal ↔ schedule / admission 由来の
   authoritative 集合の全単射)」だけを残し、exact signature は固定しない (A-10)。

## 不変 pin 表 (supersede 禁止)

`test_s8b_floor_contract.py:180` (v4 pin)、`test_s8b_floor_stats.py:596, 1321-1325`、`test_attempt_registry_core_s8b_profile.py:2206, 2251-2294`
(core S5 と v2 retryable 空集合)、`test_s8b_attempt_registry.py:3000-3104` (adapter S6)。本 wave で supersede してよい pin は無い。

## 単位 C / D2 への移行表 (A-8。今は変えない)

| pin / fixture | 誰が・どう変えるか |
|---|---|
| `test_s8b_floor_contract.py:180` `RESULT_SCHEMA == v4` | 単位 C が producer を v5 へ切り替える commit で v5 へ supersede |
| `test_s8b_floor_stats.py:596` honest v4 fixture | legacy v4 正例として維持 (変えない) |
| `s8b_v2_freeze_fixture.py:340`、`test_s8b_ratified_verify.py:460` (動的に `RESULT_SCHEMA` を参照) | D2 が `LEGACY_RESULT_SCHEMA` へ固定するか v5 proof を組み立てるかを決める (裁定パッケージ) |
| `test_s8b_floor_campaign.py:6552` | 単位 C の producer v5 正例へ追従 |

## 変異事前登録 (DW-M01)

実装前に登録する。単一理由性は実装後に親が確認し、成立しない候補は登録から外して再照準する。

| ID | 位置 | 変異 | KILLED 期待 node | 単一理由 |
|---|---|---|---|---|
| M1 | core validator | exact key 検査を削除 | `..._prefix_proof_rejects_extra_key` | extra key は他の field 検査に掛からない |
| M2 | core validator | field 型検査を truthy へ緩和 | `..._prefix_proof_rejects_each_field_type[...]` | core 直接呼出し |
| M3 | core validator | `row_count > 0` → `>= 0` | `..._prefix_proof_rejects_zero_row_count` | 他 field は valid |
| M4 | core validator | zero head 拒否を削除 | `..._prefix_proof_rejects_zero_head` | zero は hex64 として valid |
| M5 | replay helper | live bytes を先頭 N 行へ切ってから replay | `..._rejects_malformed_tail_after_n` | 先頭 N と proof は一致 |
| M6 | replay helper | chain 検証なしの JSON decode だけ | `..._rejects_broken_chain_after_n` | tail は canonical JSON かつ shape valid |
| M8 | inspection | `rows[N-1]` の head 比較を削除 | `..._rejects_reported_head_tamper` (再 chain 済み入力) | full replay は通る |
| M9 | inspection | `rows[N-1]` → `rows[-1]` | `..._accepts_valid_later_append` | append 後の全行は core-valid |
| M10 | replay helper | v2 schema guard を削除 | `..._rejects_synthetic_v1_at_generation_path` | 合成 v1 は exact 2 段 path にあり path gate を通る |
| M11 | contract | v5 key set から `attempt_registry` を落とす | contract test (v5 = v4 ∪ {attempt_registry}) | mode / perf key は正しい |
| M12 | stats pure verifier | reported / expected の等値比較を削除 | `test_v5_rejects_reported_prefix_head_tamper` (pure 直接) | shape / binding / admission は valid |
| M13 | stats wrapper | v5-only guard を削除 | `test_live_v4_does_not_call_attempt_registry_inspector` (tripwire) | 呼出し自体を観測 |
| M14 | stats wrapper | expected binding を reported proof から採る | 段 5: fake inspector 版 (`expected_binding` を assert)。段 6: 実台帳 2 世代 test | 段 6 版だけが受理集合の差を直接観測 |
| M15 | contract | v4 key set へ `attempt_registry` を足す | contract の literal pin (A-7) | 下層直接 |
| M16 | stats pure verifier | `proof.freeze == artifact.freeze` の検査を削除 | `test_v5_rejects_artifact_header_freeze_tamper` | proof / live / admission は valid |
| M17 | core validator | `registry_schema` literal 検査を緩和 | `..._prefix_proof_rejects_wrong_registry_schema` | 他 field は valid |
| M18 | inspector root 解決 | `shared_admission_root` → `_entry_paths` (provisioning) | tripwire test (`provision_shared_admission_root` を呼ぶと失敗) | 呼出し自体を観測 |

登録しない: plan の M7 (長さ検査単独では `IndexError` で拒否が残る。負例 test は残す)。過剰拒否の正例 (DW-M01): v4 artifact の受理不変、
N=1 / 3 / 4 / 5 の正例、valid append、unsafe 兄弟世代下の current prefix 受理。

## 実装子への分割 (DW-S05-A)

| unit | 所有 path | 内容 |
|---|---|---|
| unit 1 | `orchestrator/campaign/attempt_registry_core.py`、`orchestrator/campaign/s8b_attempt_registry.py`、`orchestrator/tests/test_attempt_registry_core_s8b_profile.py`、`orchestrator/tests/test_s8b_attempt_registry.py` | D1-b → B2-a |
| unit 2 | `orchestrator/campaign/s8b_floor_contract.py`、`orchestrator/campaign/s8b_floor_stats.py`、`orchestrator/tests/test_s8b_floor_contract.py`、`orchestrator/tests/test_s8b_floor_stats.py` | D1-a → D1-c → D1-d。unit 1 の API は本裁定の signature を前提にし、wrapper test は module 属性の monkeypatch (`raising=False`) で fake を注入する |

## ユーザーへ返す裁定パッケージ候補 (段 7 で README へ)

1. 検証時に freeze-wide の予算超過を再導出するか (A-4)。本 wave は writer の防壁に委ね、非保証として明記した。
2. coverage の exact signature は単位 C の terminal 証拠契約の後に固定する (A-10)。
3. D1533 の非保証範囲を成果物へ載せる所有者 (単位 C の `result.md`) (A-11)。
4. D2 の v5-only 化に伴う fixture 2 件の扱い (B)。
5. A1' / A2α / A2β から持ち越した裁定パッケージ (合成 2 段 v1 残骸、B1 の 5 件) は未裁定のまま。

## brief の訂正 (A-9 / B-10)

`result_keys_for_mode` は 12 呼出し (production 3 / test 9)。`RESULT_SCHEMA` は raw word で production 7 / test 5 file、意味的な S8B 閉包は
production 5 (定義元含む) / test-support 4 file。`output/` に v4 の result JSON bytes は 0 件、v5 `attempt_registry` を持つ JSON も 0 件。
(P3) の値域は N=1 / 3 / 4 / 5。
