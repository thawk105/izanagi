静的レビュー結論は **NO-GO** です。pytest・変異は実走しておらず、以下の「赤」はコード経路からの静的予測です。

## M1〜M6 の検出 node

- **M1: script executor 集合を空にする**
  - 赤: `orchestrator/tests/test_hooks.py::test_bash_login_script_executor_modules_classify_their_target`
  - 実装の集合は [guard_bash.py:333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:333)、テストは [test_hooks.py:740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:740)。
  - 判定: **KILL 可能**。

- **M2: `-m` 後の位置引数を再び候補にする**
  - 赤: `orchestrator/tests/test_hooks.py::test_bash_login_module_identity_and_borrow_matrix`
  - `-qmpytest tools/run_tests.py` 等が sanctioned path を借りて ALLOW へ反転する。[test_hooks.py:726](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:726)
  - 判定: **KILL 可能**。

- **M3: `exec_calibrate.py` を `local-ok` にする**
  - 静的に赤になる node は少なくとも次の 9 本。
    - `test_bash_pegasus_registry_schema_and_fixed_classes`
    - `test_bash_pegasus_registry_login_and_suspect_bits_are_pinned`
    - `test_bash_sanctioned_pegasus_paths_are_derived_from_registry`
    - `test_bash_login_blocks_attached_and_bundled_python_modules`
    - `test_bash_login_script_executor_modules_classify_their_target`
    - `test_bash_login_interpreter_prefix_value_options_reveal_scripts`
    - `test_bash_login_retokenizes_env_split_and_skips_exec_argv0`
    - `test_bash_login_sanctioned_entries_are_exact`
    - `test_bash_login_resolves_python_modules_to_exact_repo_paths`
  - 独立 class oracle は [test_hooks.py:985](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:985)、既存 anti-glob pin は [test_hooks.py:1175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:1175)。
  - 裁定が登録した 1 node だけではない。[s4-ruling.md:101](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s4-ruling.md:101)
  - 判定: **KILL 可能だが、期待 node 集合が未更新**。

- **M4: interpreter option の値消費を外す**
  - 赤: `orchestrator/tests/test_hooks.py::test_bash_login_interpreter_prefix_value_options_reveal_scripts`
  - `-W ignore <compute-only>` が path を失って ALLOW になる。[test_hooks.py:769](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:769)
  - 判定: **KILL 可能**。

- **M5: registry から 1 entry 削除**
  - 全場合に赤:
    - `test_bash_pegasus_registry_schema_and_fixed_classes`
    - `test_bash_pegasus_execution_inventory_is_synchronized`
  - `dispatch-required` / `unknown` entry を削除するなら runtime は未登録 DENYへ移るため、behavior test は赤くならない。
  - `local-ok` entry を削除するなら、さらに次が赤:
    - `test_bash_pegasus_registry_login_and_suspect_bits_are_pinned`
    - `test_bash_sanctioned_pegasus_paths_are_derived_from_registry`
    - `dispatch_compute.py` または submit 3 本なら `test_bash_login_sanctioned_entries_are_exact`
    - `fetch_third_party.py` なら `test_bash_login_allows_fetch_third_party_sanctioned_spellings` と `test_bash_login_fetch_third_party_entry_is_exact`
  - 判定: **削除 path 未指定のため、期待 node と単一理由性を一意に定められない**。

- **M6: 全 entry を `dispatch-required` にする**
  - 赤:
    - `test_bash_pegasus_registry_schema_and_fixed_classes`
    - `test_bash_pegasus_registry_login_and_suspect_bits_are_pinned`
    - `test_bash_sanctioned_pegasus_paths_are_derived_from_registry`
    - `test_bash_login_allows_fetch_third_party_sanctioned_spellings`
    - `test_bash_login_fetch_third_party_entry_is_exact`
    - `test_bash_login_sanctioned_entries_are_exact`
  - 判定: **過剰拒否を検出可能**。ただし裁定の期待 node 記述より実際の赤集合が広い。

## 所見

### 1. real — M5 の変異が path 未指定で、単一理由性を満たさない

- (a) 根拠: [s4-ruling.md:103](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s4-ruling.md:103)、local-ok 集合は [guard_bash.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:202) 以降。
- (b) 具体例: `collect_receipt.py` 削除なら構造 test だけ、`fetch_third_party.py` 削除なら LOGIN の ALLOW→DENY も検出される。
- (c) 修正案: M5 の対象を非 `local-ok` の exact path、例えば `collect_t126_qualification.py` に固定し、期待 node を上記 2 構造 node として登録する。あるいは local-ok 削除変異を別 ID に分離する。
- (d) 未修正なら、同じ「M5 killed」が registry 参照だけの変化と LOGIN 受理集合縮小の両方を表し、変異台帳の意味が非一意になる。

### 2. real — “再帰 execution inventory” が実行可能な `.pbs` を取りこぼす

- (a) 根拠: inventory は `.py` / `.sh` または `os.access(..., X_OK)` だけを採用する [test_hooks.py:1071](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:1071)。一方、mode 0644 の [t293_perf_site_probe.pbs:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/probes/t293_perf_site_probe.pbs:1) と [t419_probe_causality.pbs:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/probes/t419_probe_causality.pbs:1) は `#!/bin/bash` で、`bash <path>` として実行可能だが registry にない。
- (b) 具体例: mode 0644 の `tools/pegasus/probes/future_probe.pbs` を追加しても inventory test は赤くならない。runtime は未登録として DENY するため、同期保証だけが恒真化する。
- (c) 修正案: `.pbs`・shebang を inventory 条件へ含めるか、保証名と実装報告を「`.py`/`.sh`/実行 bit inventory」に狭める。実行 bit 判定は環境依存の `os.access` より Git mode または `stat` mode を使う。
- (d) 未修正なら受理 bit は DENY のままだが、registry の inventory 参照から実行可能 job body が欠落する。
- 実装報告の「新しい Pegasus 実行体は未登録なら inventory meta-test 赤」もこの例では偽。[s5-impl.md:69](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s5-impl.md:69)

### 3. real — 未列挙 `-m` executor の DENY→ALLOW が、テストにも受理集合報告にもない

- (a) 根拠: executor は固定列挙 [guard_bash.py:333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:333) に無い module なら空を返す [guard_bash.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:701)。新 `_script_target` はその位置引数を候補にしない [guard_bash.py:774](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:774)。旧実装は全 Python 形の最初の位置引数を候補にしていた [s5-impl.patch:425](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s5-impl.patch:425)。
- (b) 具体例: `python3 -munittest tools/pegasus/exec_calibrate.py` は旧 blanket 判定では DENY、新実装では `unittest` が閉集合外なので ALLOW。テスト matrix [test_hooks.py:740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:740) にもない。
- (c) 修正案: `unittest` / `doctest` 等、位置引数を読み込み・実行する module grammar を追加し、独立した DENY test を置く。閉集合の完全性を立証できないなら、Pegasus path を data として許す module 側を狭い allowlist に反転する。
- (d) 未修正なら LOGIN 受理集合へ、以前拒否されていた Pegasus path を module runner 経由で渡す綴りが追加される。
- この反転は実装報告の DENY→ALLOW 一覧 [s5-impl.md:38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s5-impl.md:38) にない。

### 4. real — 「19関数 PASS」の実走範囲が再現不能

- (a) 根拠: [s5-impl.md:49](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s5-impl.md:49) は「追加テストと主要既存 pin、19関数」としか書かず、関数名・driver・範囲を列挙していない。一方 pytest は nodeid 0 件と正直に記録している [s5-impl.md:56](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s5-impl.md:56)。
- (b) 具体例: M1〜M6 のどの node が軽量直接呼出しに含まれたか、報告から確認できない。
- (c) 修正案: 19 関数の完全な qualified name と呼出し driver、checkout を追記する。列挙できなければ PASS 主張を削り「非 pytest の spot check、範囲不明」とする。
- (d) 未修正なら、実走証拠集合に特定不能な「19 PASS」が残り、後続 wave が未実走 node を closed と誤認できる。

## 恒真性・独立性の判定

新 registry test は、現 revision では実装から期待値を生成していません。

- 独立 golden: `_PEGASUS_EXPECTED_CLASSES` [test_hooks.py:985](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:985)、`expected_local_evidence` [test_hooks.py:1026](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:1026)。
- 独立 behavior oracle: LOGIN/SUSPECT の expected bit は上の test-side class から算出し、production registry からは算出しない。[test_hooks.py:1043](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:1043)
- 外部 oracle: inventory test は working tree を走査する。
- 実装の写しで検出力ゼロの新 acceptance test: **なし**。ただし test-side golden を実装と同時更新すれば検出力を意図的に弱められる。

危険な `.py` と `local-ok` registry 行だけを同時追加した場合、inventory test 自体は緑のままですが、`test_bash_pegasus_registry_schema_and_fixed_classes` が key 集合と local evidence 集合の差で赤になります。さらに `_PEGASUS_EXPECTED_CLASSES` と `expected_local_evidence` まで同時更新すれば全 generic test は通り得ます。その場合、class の安全性は自己申告文字列しか検査されません。inventory docstringは「class/evidence/runtime を保証しない」と明記しており [test_hooks.py:1066](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:1066)、文言自体は正直です。

## 既存テストと fixture

- test patch は **198 行追加、削除 0**。期待値反転・緩和・skip・削除はない。[s5-impl.patch:482](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s5-impl.patch:482)
- `test_bash_login_sanctioned_entries_are_exact` の `exec_calibrate.py` 個別拒否 pin は維持。[test_hooks.py:1153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:1153)
- `test_bash_login_fetch_third_party_does_not_sanction_siblings` も無変更。ただし元から `exec_calibrate.py` は含まず、controls は `certify_calibration.sh` と `run_probe.py`。[test_hooks.py:1113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/tests/test_hooks.py:1113)  
  これは削除回帰ではないため **nit**。成果物影響なし。
- working-tree hash・固定件数は焼き込まれていない。完全 path 集合は意図的な policy oracle。ただし `os.access(X_OK)` と suffix 判定の境界は所見 2 のとおり不安定。

実装報告は pytest の指定範囲、要求コマンド、rc=16、実走 nodeid 0 件を明記し、`closed` や全緑を申告していません。この部分は正直です。こちらでも pytest は走らせておらず、緑は主張しません。

## 総括

**real 所見は 4 件**です。最重要 3 件は次のとおりです。

1. 未列挙 `-m` executor による未テスト・未報告の DENY→ALLOW。
2. M5 が削除 path 未指定で、meta-only と behavior-changing の二通りに分岐する。
3. inventory meta-test が mode 0644 の `.pbs` 実行体を取りこぼし、報告の保証範囲も過大。

**land 判定: 不可。** 上記 3 件の修正、M1〜M6 の exact anchor・期待 node 更新、計算ノードでの pytest と変異 matrix 実走が必要です。