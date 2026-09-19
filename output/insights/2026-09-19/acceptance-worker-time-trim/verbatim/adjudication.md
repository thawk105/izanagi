# 段 4 裁定 — [{{T:acceptance-worker-time-trim}}] (2026-09-19 22:45 JST 頃、親)

一次資料: brief.md、plan-out.md、consult-a-out.md (正しさ境界)、consult-b-out.md (実効性・過剰)、tmp/stage1c/prof_summary_pointer.md。

## 1. 所見の裁定 (real / refuted、採否)

| # | 出所 | 所見 | 裁定 | 採否・処置 |
|---|---|---|---|---|
| A1 | consult A must-fix | memo から copy した fixture では、builder の `_assert_no_root_bytes` (F:1277–1281) の needle が copy 先 root だけになり、構築元 root の絶対 path 漏洩 (production `_portable_argv` :4819 の相対化退行) を検出できない | **real** (現物 F:1277 の needles は `tmp_path/root/out_root` の 3 本) | 採用。memo metadata に構築時の `tmp_path/root/out_root` 文字列を保存し、copy 後の検査で構築元 + copy 先の両方を needle にする。変異 M3 で検出維持を実証 |
| A2/B3 | consult A/B must-fix | plan の「module fixture を `_clean_runner_env` (function scope) に依存」は ScopeMismatch | **real** | 採用。U3/R は **function scope** で小 repo を作る (module base は作らない)。小 repo 構築は git init + 1 commit で軽く、19 回で十分安い |
| A3 | consult A should | R:2314 `test_previous_full_cap_estimate_dispatches_without_local_scope` は fingerprint に到達せず、`_REPO` 差替えで RuleOps 検査経路 (`tools/ruleops.py` 不在) に落ちる | **real** | 採用。対象から外す。author は各対象 node の経路を静的に追い、`_REPO` が fingerprint 以外で使われる node を対象から外す |
| A4/B2/B7 | consult A should / B must-fix・should | U2 digest 共有は (a) 読取り失敗の fail-closed を共有 hit で隠す、(b) 共有構築の待機を差し引くと純利得の符号が不明 (11 node が同時到着すると相殺)、(c) 提案変異 2 件は cache 条件を攻撃しない | **real** | **U2 は実装しない**。floor_campaign は本 wave では無変更。残る律速として報告 (下記 §3) |
| B1 | consult B must-fix | brief の「real-repo 登録 node は 1 worker 直列」は誤り。`conftest.py:2161` が process-memo 集合 (t1259 30 関数 + oracle_driver 一部) 以外の `@real-repo` を外す。codex_ab / floor の登録 node は分散する | **real** (現物 :2161–2175、:670–701 で確認) | brief の前提を訂正。t1259 の「単一 worker 直列」は正しいが codex_ab/floor には当たらない。設計は変わらない (U3/A・U4 は別理由で不採用) |
| B4 | consult B should | U1 の全 worker 共有 (flock + 最後の退出者削除) は必須ではない。worker 専用 disk memo でも fork 子を越えて再利用できる。copy 量は 280 file / 1.14 MB (残存標本) | **real (部分)** | 採用 (設計の単純化): memo の置き場は **pytest の session basetemp 直下** (`tmp_path` から `pytest-N` 直下へ遡る)。同 session の全 worker から見え、fork 子でも消えず、削除は pytest の basetemp 保持規則に委ねる (自前の寿命管理・最後の退出者削除を作らない)。key ごとの構築は flock 1 本で直列化 (T-080 先例の `get` と同じ complete marker 方式) |
| B5 | consult B should | U4/P は 7 tree、段 1 の該当 3 node は 43.4 秒 (台帳 109 秒)。配置により削減 0、上限でも 4 構築分 | **real** | **U4 は実装しない** (配置依存で見積り不能、`validate_exact_replacements` の維持で複雑) |
| B6 | consult B must-fix | 親の ab_compute.sh は file 別起動・`rm -rf /tmp/pytest-of-*`・pyc 読込み許容・順序が AB/BA/AB | **real** | 採用。A/B script を書き直す: 6 file を 1 回の run_tests に渡す、走ごとの TMPDIR/`--basetemp`/`PYTHONPYCACHEPREFIX` scratch、`IZANAGI_TASK_RUN_AUTO_RECORD=0`、warmup A/B の後 AB/BA/BA/AB の 4 対、片付けは自分の scratch だけ |
| A(表) | consult A | `benchmark_snapshots` を session scope にすると serialization test の literal 閉包が赤 | **real** | U3/A の不採用理由に追加 |
| A(mask 表) | consult A | 変異が memo に隠れる経路 (構築側の変異、fork 前 import、失敗構築の再利用、process cache の残留) | **real** | 変異 harness は走ごとに fresh worktree + fresh session (memo は session basetemp 下なので毎走 fresh)。構築側変異 M3/M4 を matrix に入れる。失敗構築は complete marker を書かない |
| B(見積り) | consult B | 12 worker の比を 48 worker へ外挿しない。削減式は待機・copy・cleanup 込み | **real** | 報告は A/B 条件の実測値 (file 別・6 file 合計、対差の中央値と幅) と、受入 receipt の実測を並べて書く。外挿しない |
| P2 | 親 brief | before を module scope に | **refuted** (plan・両 consult) | 不採用 |
| P4 | 親 brief | codex_ab の完成 fixture を copy | **refuted** | 不採用 (絶対 path、submodule gitdir、oracle 再束縛が要り 120〜200 行、純利得の符号未確認) → **U3/A は実装しない** |
| P5 | 親 brief | p3_b4 / t1259 に局所候補なし | **部分 refuted** (p3_b4 は 7 tree に候補あり) | ただし B5 で不採用。t1259 は plan/両 consult とも無変更 |
| P6 | 親 brief | 12 worker の比が 48 worker へ転移 | **refuted** | 外挿しない |

## 2. plan v2 (実装する scope)

**U1 — s8b builder の disk memo (所有: test_s8b_ratified_freeze.py、test_s8b_ratified_verify.py)**
- 切断点: F:1085 `_run_official_fixture_campaign` 返却直後、F:1102 `selector_extra_files` 適用の前。memo = `root` 配下の木全体 (`.git`、`external/ccbench`、`output/` を含む) + metadata JSON (base、checkpoint["C"]、ccbench_pin、design_raw/generator_raw、run_dir の相対 path、構築時の `tmp_path`/`root`/`out_root` 文字列、構築時 `git status --porcelain` (root と内側 ccbench)、file 数・bytes、記録用 key)。
- key = (実 worktree root の realpath、`now.isoformat()`、`selector_valid_cell`、`selector_payload_hit`、`perf_available`、`compiler_input_rel`、`cert_at_generation`)。`receipt_root is not None` は memo を迂回し現行処理。`selector_valid_cell=True` または `selector_payload_hit=True` は決定性未確認のため memo を迂回する (現行処理)。
- 置き場: `tmp_path` から遡った pytest session basetemp 直下 (`<basetemp>/izanagi-emitter-memo/<key sha256>/`)。同 session の worker・fork 子で共有、pytest の basetemp 規則で消える。key dir の構築は `<key>.lock` の `flock(LOCK_EX)` 内で行い、`complete.json` を最後に `os.replace` で公開。marker 不在で dir があれば残骸として消して作り直す。構築失敗時は marker を書かない。
- hit 時: `shutil.copytree(memo_repo, root, symlinks=True)` → root と `root/external/ccbench` で `git update-index --refresh -q` (rc は無視せず、`git status --porcelain` が構築時の記録と byte 一致することを assert) → `_fixed_prepare.ccbench_dir` / `cache_root` を copy 先で設定し直す → F:1102 以降を従来どおり実行。needles に構築時文字列を加える (A1)。
- `load_emitter_g1` / `_assert_emitter_baseline` は builder の共有を受けるだけで、`M.load_ratified_freeze` / `launch_validate` / assertion は各呼出しで実行 (判定を memo しない)。`build_valid_semantic_g1`、`_build_independent_launch_repo`、`append_production_emitter_g2` は変更しない。signature と返却 tuple は不変。
- 機構の正例: F に **新 test 1 node** `test_emitter_memo_copy_matches_fresh_build` を足す。同 key で fresh 構築 (memo 迂回) と memo copy を作り、git HEAD SHA、`git status --porcelain`、tracked file の bytes、返却 tuple (root 以外) が一致することを assert。さらに memo dir を壊した (marker なし) 状態から再構築できることを assert。**追加 node はこの 1 本だけ** (成分粒度の変更はこれに限る)。
- 変異 harness では走ごとに fresh worktree + fresh session なので memo は毎走 fresh。

**U3/R — preflight の小 repo 入力 (所有: test_run_tests_preflight.py)**
- function scope fixture `_small_login_repo(tmp_path, monkeypatch, _clean_runner_env)`: `_tracked_repo` (R:81) 相当の小 git repo (git init + tracked file 1 つ + commit、submodule なし) を作り、`monkeypatch.setattr(RT, "_REPO", str(repo))` で注入。fingerprint 関数・5 command はそのまま実行される (DW-O14: 外側の入力 seam)。
- 対象: plan の 11 関数のうち、`RT.main(site=PEGASUS_LOGIN)` で local scope に入り fingerprint に到達し、かつ `_REPO` が他の preflight (RuleOps/submodule/unstaged deletions) で使われない node。R:2314 は外す。author は各 node の経路を静的に追い、対象表 (node / 到達経路 / `_REPO` の他用途なし) を報告に書く。既存 fingerprint mock の 5 箇所は変えない。
- 機構の正例: **新 test 1 node** `test_small_login_repo_fixture_yields_real_fingerprint`: 小 repo で `RT._tree_and_submodules_fingerprint(Path(RT._REPO))` が非 None・digest 64 hex・summary 5 要素で、tracked file を書き換えると digest が変わることを assert (実物の関数が走っている正例)。

**実装しない (残る律速として報告)**: U2 (floor: production 二乗 ledger 回復 90 × 5.8 s、snapshot 2 回/test は失敗集合の意味、digest 共有は純利得の符号不明 + 読取り失敗の fail-closed)、U3/A (codex_ab: 絶対 path/submodule gitdir/oracle 再束縛、純利得未確認)、U4 (p3_b4: 配置依存、production ScratchTree と run_tests subprocess は検査対象)、t1259 (既に module memo、process-memo group で構築 1 回)。

## 3. 変異 matrix の事前登録 (DW-M01、production 側、修正前 = base 657e1e5a7、修正後 = wave tip)

runner argv (両側同一): `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_s8b_ratified_freeze.py orchestrator/tests/test_s8b_ratified_verify.py orchestrator/tests/test_run_tests_preflight.py -q -rf`

| id | category | file:置換 | 期待 (両側同一) |
|---|---|---|---|
| M1-frozen-head | negative | `orchestrator/campaign/s8b_ratified_freeze.py` `if parents[0] != frozen:` → `if False:` | V の frozen-at-head 拒否を観測する node が KILLED |
| M2-closure-sha | negative | 同 `if _sha256_hex(g_blob) != sha:` (closure、:1042) → `if False:` | V の closure-sha-mismatch 観測 node が KILLED |
| M3-argv-root-leak | negative (構築側) | `orchestrator/campaign/s8b_floor_campaign.py:4819` `token = _replace_root_component(token, root, placeholder)` → `token = token` | builder の `_assert_no_root_bytes` で F/V の builder 利用 node が KILLED (新側は構築元 needle 込みで同一集合) |
| M4-launch-start-sha | negative (構築側) | 同 :7611 `"launch_certificate_sha256": launch_certificate_sha256,` (launch-start event) → `"launch_certificate_sha256": "0" * 64,` | F/V で journal の launch-start sha を観測する node が KILLED (無ければ両側 SURVIVED で同一) |
| M5-child-rc | negative | `tools/run_tests.py:2560` `return scope_result.child_rc` → `return 0` | R:1837 等 child rc を観測する node が KILLED |
| M6-fingerprint-compare | negative | 同 :2571 `or tree_before != tree_after` → `or False` | R:1885 等 fingerprint 変化時の拒否を観測する node が KILLED |
| P0-equivalent | positive | `orchestrator/campaign/s8b_ratified_freeze.py:1011` `if len(parents) != 1:` → `if 1 != len(parents):` | SURVIVED (harness の正例) |

- 手順: (1) 修正前 (base) を **probe 走** (全件 SURVIVED 期待・expected_nodes 空) で観測 node 集合を採る (DW-M08 の「確定できない場合に限り初回を probe と明記」に該当。理由: 3 file の parametrize 展開後の完全集合を静的に確定できない)。(2) 観測集合を expected_nodes に登録した spec で **修正後 (tip) を KILLED 期待走** (完全一致だけを KILLED)。(3) 修正前の観測集合 == 修正後の登録集合 (KILLED) をもって「kill 集合が修正前と同一」とする。M3/M4 は新側で追加 node (正例 1 本ずつ) の分だけ集合が増えうる → 新 test node は期待集合に加えるが、旧集合との比較は既存 node に限って行い、差分は追加 node だけであることを示す。
- 単一理由性 (F820) は probe の失敗本文で確認する。
- 所要見積り: 1 走 ≈ F+V+R (段 1 の wall 75 + 25 + F 未計測 ≈ 150 s) + dispatch 往復。8 走 × 2 側。

## 4. A/B (段 6)
- 同 job (generic task)、A = ab-base worktree (657e1e5a7、修正前)、B = wave tip。6 file を 1 回の `run_tests.py` に渡し `-n 12 --dist=loadgroup -p no:cacheprovider --junitxml`。走ごとに `TMPDIR`/`--basetemp`/`PYTHONPYCACHEPREFIX` を新 scratch、`PYTHONDONTWRITEBYTECODE=1`、`IZANAGI_TASK_RUN_AUTO_RECORD=0`。warmup A, B の後 **AB / BA / BA / AB の 4 対**。片付けは自分の scratch だけ。指標 = junit testcase time の file 別合計と 6 file 合計、外側 wall、対差の中央値・全値・幅。12 worker の比を 48 worker へ外挿しない。受入 receipt (48 worker) は別に実測値として並べる。

## 5. 所有分割 (段 5、並列 2 本)
- author-U1: `orchestrator/tests/test_s8b_ratified_freeze.py`、`orchestrator/tests/test_s8b_ratified_verify.py`
- author-U3R: `orchestrator/tests/test_run_tests_preflight.py`
- 誰も触らない: production、conftest.py、他 test file。commit は親。
