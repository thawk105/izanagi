# [T-1222] 成長比例母集合の未閉包を閉じ、item2 の test 側欠陥を実装で解消した

wave: `T-1222-population-closure` (2026-08-20〜21)、branch
`worktree-T-1222-population-closure`、base main `66fdf68c`、commit `6e707b61`。

## 背景

2026-08-16 wave (`dev-wave-t1222-growth-hold-sweep`) の段2 全件走査は文字列検索プリミティブ
ベースで、production の重い関数を同一プロセス内で呼ぶ `module.func(ROOT)` 型 in-process 呼び出しを、
import 文が非標準な形のときに構造的に取りこぼした。既知漏れは最低11 top-level node:
`test_codex_agents.py` 7 (項目1) / `test_dev_waves_integration.py` 1 (項目2) /
`test_s8c_preregistration_invariant.py` 1 (項目3) / `test_check_ai_provenance.py` 2 (項目4)。

2026-08-17 wave (`dev-wave-t1222-growth-leak-fix`) のユーザー裁定 (`/rulings` 全件第4回) が
「4件を恒久保留へ登録する案を却下、test側/target側を判定して直す」と確定させた。判定結果:
項目1=neither (欠陥なし)、項目2=test側欠陥は実在 (未実装、ユーザー裁定へ返す)、項目3=target側
(同wave実装済み)、項目4=未実装・ユーザー裁定へ返す。その後 D499 (2026-08-17、
`docs/decisions.md:20690`) が項目2/4 を処分: 項目4 は全史走査を仕様として受容 (再訪は所要90秒超)、
項目2 は恒久保留 (解除はユーザー明示命令のみ)。D499 は「残件は母集合の未閉包のみ」と明記していた。

本 wave の command 引数は、`test_codex_agents.py`/`test_dev_waves_integration.py`/
`test_s8c_preregistration_invariant.py`/`test_check_ai_provenance.py` を起点に母集団を再走査し
「欠陥を恒久保留へ登録しない」ことを明示的に求めた。

## 段1 brief の P1 判定と裁定

command 原文は item4 だけを「accepted full-history scan の範囲を保ったまま」と明記して保護し、
item2 (test_dev_waves_integration.py) は保護しなかった。段1 brief はこれを「本 command が
D499 の item2 disposition (修正保留) を解除する明示指示」と provisional に解釈し (P1)、段3 で
攻撃対象にした。

段3 lens A (正しさ境界) は (P1) を「blocker 級の懸念、段4 裁定なしに保留解除・実装へ進む危険」と
指摘した。lens B (整合・scope) は「実装しない」を推奨したが、自ら示した判定基準
(「command 原文に item2/test_dev_waves_integration.py を直接指定する文言があれば有効」) は、
実際の command 原文 (test_dev_waves_integration.py を名指しし修正を要求、恒久保留を明示的に禁止)
に照らすと満たされていた。

段4 裁定は「実装する」を採用した。根拠は `docs/spool/decisions/` fragment
({{D:t1222-item2-launcher-fix-supersedes-d499}}、fold 後の実番号は worklog 参照) に記録した
とおり: (1) command 原文の非対称な保護と明示的な恒久保留禁止、(2) 起票者が D499 を含む両方の
archive を正本として引用しており認識した上での起票と判断できること、(3) D499(2) の理由
(「変異による検証が構造的に不能」) を覆す D452 適合の新設 static assertion 設計を段2 codex
plan が示したこと。

## 母集団再走査: 11 → 12 (新規発見1件、既存11件は不変)

08-16 wave の穴 (import idiom の非網羅性) を修正するため、4 種類の idiom
(package-relative import / `sys.path` hack / `importlib.util.spec_from_file_location` 動的
ロード / `runpy`) で `tools/*.py` 全 **38** stem (brief 起草時「37」は親のカウント誤り、段4で
訂正) を `orchestrator/tests/` 全体 (209 file) と横断照合した。D463 の成長比例基準を実際に
満たす stem は `check_docs.py`・`check_ai_provenance.py`・`check_codex_agents.py` の3つと当初
結論したが、段3 lens B の敵対的指摘により **4つ目 `check_subprocess_bytecode_guard.py` を
見落としていた**と判明した。

### 新規発見: `test_check_subprocess_bytecode_guard.py::test_real_repo_clean`

- `tools/check_subprocess_bytecode_guard.py:64-72` の `iter_python_files()` が `orchestrator/`
  + `tools/` 配下の全 `.py` を `rglob` する (D463(b) 型)。
- `test_real_repo_clean` (`orchestrator/tests/test_check_subprocess_bytecode_guard.py:223`) が
  `checker.main(["--repo", str(_REPO)])` を実 ROOT (`_REPO = Path(__file__).resolve().parents[2]`)
  に対して in-process 呼び出しする。
- 親が実測: **8.232 秒** (`site=OTHER`相当の直接呼び出し、Pegasus dispatch を経由しない
  ローカル計測)。同ファイル内の他5 test node はすべて `tmp_path` synthetic のみで実 ROOT 非接触。
- `_scan_file()` (`:339-345`) は対象 file を1回 `read_text` + 1回 `ast.parse` するのみで、item3
  (check_docs.py) 型の冗長読取バグは無い。
- **分類: neither (欠陥なし)。恒久保留へは登録しない。** 安全ガードとして source tree 全体を
  毎回静的走査するのは設計上必然であり、item4 (全史走査) と同型の precedent。D451 (防壁を守る
  最後の走行 node には保留を掛けない) の趣旨にも合致する。

### 段3 lens B の別指摘 (refuted、既に登録済みと確認)

`test_s1_known_axes_freeze.py` の `test_generate_selects_registered_expected_points`
(旧行86付近) と `test_build_document_is_self_consistent_and_detects_tamper` (旧行486付近) を
新規候補として指摘されたが、`growth_test_holds.py:231,211` で**既に登録済み**と確認した
(GROWTH_TEST_HOLDS 現在59件は不変)。false positive として refuted。

その他、`tools/audit_dangling_commits.py` (全 test node が `tmp_path` synthetic のみ)、
`tools/run_tests.py` 系 (`test_growth_test_holds_contract.py`/`test_pegasus_dispatch_compute.py`
の呼び出しはいずれも合成引数または `monkeypatch` で dispatch 自体を mock 化)、`sys.path` hack を
使う残り3 file (`test_check_workflow_models.py`/`test_check_worktree_occupancy.py`/
`test_s8b_selector_output.py`、いずれも単一設定検証・synthetic tmp_path・スキーマ検証で実ROOT非接触)
を個別に確認し、非該当と判定した。

**母集団は12 node (既知11 + 新規1) で閉じている。**

## item1/3/4 の再確認 (現状維持、追加実装なし)

- **item1** (`test_codex_agents.py` 7 node、行 121,127,164,216,233,511,1300、現在まで drift
  なしと直接 Read 確認): `git ls-tree -r -l HEAD` で `.claude/agents` 13f/86,524B、
  `.codex/role-adapters` 13f/175,395B、`orchestrator/codex_roles` 8f/236,206B (HEAD `66fdf68c`)。
  08-16/17 時点から file 数不変、bytes 微増のみ。「第3区分」の分類は今も妥当。
- **item3** (`test_s8c_preregistration_invariant.py`、in-process `check_docs.main()` 呼び出しは
  現在行712、旧行257から大幅 drift): 08-17 wave の実装 (`check_docs._safe_read_text` の
  monkeypatch 方式) が現存することを確認した。
- **item4** (`test_check_ai_provenance.py` 実repo 2 node、`test_empty_registry_restores_all_thirty_real_findings`
  行3018-3115、`test_ledgered_3f2c43d7580b_is_known_and_rc0` 行3118-3134): D499 の再訪条件
  (90秒超) を `site=site_policy.OTHER` で Pegasus dispatch を回避し実測: `main()`=0.173秒、
  `_audit_history()`=0.137秒、政策epoch pickaxe (`_scope_policy_commit`/
  `_implementation_policy_commit`) 各0.029秒。決定時実測 (約45秒) からむしろ改善しており、
  **premise は健在** (90秒に遠く及ばない)。

**環境上の注意 (今後の再測定のために記録):** `tools/check_ai_provenance.py` の生 CLI
(`--range` のみ、`site` 未指定) は Pegasus LOGIN の headroom/queue 判定を経由し、本 wave の
測定時は120秒超でも完走しなかった (queue 混雑によるものと推定、計算コストではない)。
`site=site_policy.OTHER` で dispatch 自体を回避する測定方法でなければ、D499 型の閾値再測定は
queue 待ち時間を計算コストと誤認する。

## item2 の実装: self-import launcher を専用 helper へ切り出す

### 欠陥

`test_dev_waves_integration.py` の `_run_contained_serve_child()` が fresh subprocess から
自ファイル (2,729行、増加中) を毎回 re-import しており、ファイル成長に比例して起動コストが増える
test 側欠陥。

### 設計 (段2 codex plan → 段3 lens A の5 major 所見を反映 → 段5 実装)

child 実行経路一式 (`_profile`/`_supervisor`/`_request`/`_best_effort_wait_cleanup`/
`_wait_terminal`/`_sandbox_permits_short_alias_bind`/`_Serve*` classes/
`_run_long_path_serve_harness`/`_serve_child_payload`/`_serve_child_main`) を新設
`orchestrator/tests/_dev_waves_serve_child.py` へ移設した。fixture (`_ServeRepo`) は
main/fake/fake_digest/runtime の4フィールドのみを持つ軽量 dataclass とし、親が
`_temporary_repo()`で生成した実体を argv 経由で子へ渡す (`_serve_repo_from_argv()`)。

親側 `_run_contained_serve_child()` は「repo生成 → 108-byte assert →
`_bootstrap_supervisor = _supervisor(repo)` (runtime dir 作成の副作用のためだけに構築、破棄) →
`_sandbox_permits_short_alias_bind` probe → 子プロセス起動」の順序を保持し、旧コードの
コメント「probe より前に Supervisor を作る」の意図を維持した。launcher script は
module-level 定数化:

```python
_SERVE_CHILD_SCRIPT = (
    "from orchestrator.tests import _dev_waves_serve_child as target;"
    "raise SystemExit(target._serve_child_main())"
)
```

D452 適合の新設 static assertion (`test_contained_serve_child_uses_dedicated_helper_entrypoint`、
`xdist_group` 非所属) が `_SERVE_CHILD_SCRIPT` の import 対象を検査する。既存 socket roundtrip
test (`test_socket_roundtrip_works_beyond_108_byte_repository_path`) の marker・本体・受理集合は
不変。`test_growth_test_holds_contract.py` の self-load 検出器 fixture を更新し、
`test_dev_waves_integration.py` エントリの期待値を `(True, ())` → `(False, ())` へ変更する一方、
無関係な `test_s8b_floor_campaign.py` の positive control (`(True, ())`) は維持した。

### 段6 レビュー・親検証・fix

敵対レビュー2本 (正しさ・実装忠実性 / 受理集合・波及) はいずれも blocker/major/minor ゼロ
(review A は報告文の順序記述に関する nit 1件のみ、機能上の欠陥ではない)。

**親の実機検証で新規 real 欠陥1件を発見。** codex 実装子・fix 子とも sandbox 制約で pytest を
実走できず (`qstat -Q: NQSconnect: Can't create socket`)、親が `tools/run_tests.py` 経由で検証
したところ、`test_socket_roundtrip_works_beyond_108_byte_repository_path` が
`ModuleNotFoundError: No module named 'pytest'` で失敗した。`git diff`/`git checkout --` による
安全な新旧比較 (patch を `backup/` へ退避 → 旧コードへ一時復元 → 同一テストを再実行 → 実装を
`git apply` で復元し `diff` で完全一致確認、DW-O19 準拠) で、新コード2/2 失敗・旧コード1/1 PASS
(失敗の sha256 完全一致で決定的) と確認し、実装由来の regression と特定した。

根本原因: probe を親側へ移した結果、child 側 `_run_long_path_serve_harness` はもう
`pytest.skip(...)` を送出する経路を持たないのに、`_serve_child_main()` の
`except pytest.skip.Exception` と `import pytest` が到達不能な死んだコードとして残存していた。
一部 Pegasus compute node で `sys.executable` から `pytest` (per-user pip install
`~/.local/lib/...`) が解決できず、この死んだ経路が生きた `ModuleNotFoundError` を誘発した
(ノードごとの環境差の根本原因は未特定 — 同一 login node からの直接検証では常に失敗したが、
実際の compute node dispatch では新コードのみ2/2失敗・旧コード1/1成功という非対称な結果が出た。
不要な import を削除する修正で問題自体は解消したため、これ以上の追跡はしていない)。

fix: 該当 import/except 節を除去し、child は PASS/FAIL の2値のみ返す形にした (SKIP は既に
親側の `pytest.skip(...)` で決着しており child には到達しない)。fix 後、焦点走 (
`test_dev_waves_integration.py` + `test_growth_test_holds_contract.py` +
`test_dev_waves_isolation_contract.py`、177 test) は全 PASS。

### 変異事前登録 (DW-M01)

当初2件登録 (`mutation-spec-probe.json`)。

| ID | 変異 | 結果 |
|---|---|---|
| M1 | `_SERVE_CHILD_SCRIPT` の import 対象を旧 module 名へ戻す | **MISMATCH** (下記) |
| M2 | growth contract の期待値を旧 (self-load 有) へ戻す | 初回 `PARSE_ERROR` (rc=16、dispatch artifact 収集失敗) |

M1 は期待 node (`test_contained_serve_child_uses_dedicated_helper_entrypoint`) に加え、
`test_socket_roundtrip_works_beyond_108_byte_repository_path@dev-waves-runtime` も副作用で
失敗した (`_SERVE_CHILD_SCRIPT` は静的 assertion と実 subprocess 起動の両方が参照する同一定数
であるため、変異は必然的に両方に影響する)。後者は `xdist_group("dev-waves-runtime")` 所属で
D452 条件 (c) を満たさず expected_nodes に加えられない。probe の生出力
(`mutation-ledger-probe.json` 内 `M1-*.artifact.stdout`) で静的 assertion 単体の
`AssertionError: assert '_dev_waves_serve_child' in 'from orchestrator.tests import
test_dev_waves_integration as target;...'` を親が直接確認し、D452 の代替条項 (「満たすnodeへ
実効gateを再照準するか、登録せず親の直接実測で裏取りする」) に従い、**M1 は正式な mutation matrix
から除外し、親の直接実測で裏取りした事実として本 insight に記録する。**

M2 は dispatch のアーティファクト収集失敗 (`receipt scheduler_logs.stdout.path がない`、
実テスト結果ではない) で1回目 rc=16。`mutation-spec-final.json` (M2 のみ) で再投入し
`mutation-ledger-final.json`: baseline PASSED (174 test)、**M2 KILLED、期待どおり単一 node、
matches_expectation=true。**

## 段7 遵守漏れ確認

親の遵守漏れ (F1 型の推定報告等) は今回ゼロ — 進捗報告はすべて実測値 (テスト結果・変異結果・
sha256・秒数) を実際に取得してから書いた。

## ファイル

- `verbatim/s2-plan.md` — 段2 codex plan
- `verbatim/s3-lensA.md`, `verbatim/s3-lensB.md` — 段3 敵対相談2レンズ
- `verbatim/s6-reviewA.md`, `verbatim/s6-reviewB.md` — 段6 敵対レビュー2本
- `verbatim/s6-fix.md` — 段6 fix 子の報告
- `mutation-spec-probe.json`, `mutation-ledger-probe.json` — 初回2件 (M1 MISMATCH, M2 rc=16)
- `mutation-spec-final.json`, `mutation-ledger-final.json` — M2 単独再走 (KILLED)
