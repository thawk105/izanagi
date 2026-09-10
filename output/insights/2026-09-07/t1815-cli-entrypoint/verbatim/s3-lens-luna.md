## 時間予算の所見と代替設計

所見 1: 4 case の原案は 5 分上限を満たさない  
深刻度: blocker  
根拠 (file:line): `s2-plan.md:81-82,101,147-153` では各 case が in-process と subprocess の full 評価を各1回行う。追補の 39.17〜118.74 秒を8回へ外挿すると 313〜950 秒（5.2〜15.8分）。自走 harness は直列なので、楽観端でも5分を超える。既存基準は `acceptance_duration_ledger.json:15627` の「2評価で41秒」。  
推奨: 4 case full 評価案は却下する。xdist の偶然の並列性を上限根拠にしてはならない。

所見 2: 支配項は多数の git subprocess と到達可能 Python blob の AST 解析である  
深刻度: must-fix  
根拠 (file:line): `s8c_preregistration.py:1071-1098,1108-1152,1859-1924`。top-level resolve＋3 module blob＋source blobだけで概ね28回、freeze 検査を含め registry 到達前に約42回以上の git 呼出しになる。freeze は15 generationを含む17 pathを path-limited履歴へ掛ける (`:1597-1610`)。evaluator は14 unique evidence path（うち11 Python）に加え import 到達先を blob 単位で読み (`s8c_preregistration_evidence.py:683-706,742-803`)、最大512 module・16 MiB (`:430-458`) を AST 解析する。  
推奨: 追補の「campaign 全 blob を列挙」は不正確で、実体は lazy reachability 読取である。ただし、present blobごとの `batch-check`＋`cat-file` と AST parse が支配次数なのは確かであり、full 評価回数を減らすべきである。

所見 3: full 評価を新設せず、実プロセスで module identity を直接観測できる  
深刻度: must-fix  
根拠 (file:line): 欠陥の必要十分な観測点は `s8c_preregistration.py:1739-1755,1769-1777` と `s8c_preregistration_evidence.py:18,1473-1483` の型 identity。受理意味は既存 `test_s8c_gate_report.py:464-513` が real repo の library full 評価2回で検査済み。  
推奨: 新規テストは次の3 nodeに絞る。(1) path、(2) `-m` をそれぞれ `--help` で実プロセス起動し、tmp `sitecustomize.py` の `atexit` から `sys.modules[canonical] is sys.modules["__main__"]` と `PredicateResult` identity を出力・検査する2 parameter、(3) gate のファイル直接起動へ `--definitely-invalid` を渡し canonical JSON・rc=2・stderr空を検査する。現行 core は両 identity case が偽、現行 gate-path は ImportError なので恒真ではない。新規 full 評価は0回になる。

所見 4: 新規 nodeid は所要台帳へ事後登録が必要である  
深刻度: must-fix  
根拠 (file:line): ledger は scheduler へ読み込まれる (`conftest.py:893-907,1513-1554,1578-1627`) が、未知 node は既知分布の代替値になり、未登録を拒否しない。schema meta-testも完全性は検査しない (`test_update_acceptance_duration_ledger.py:306-325`)。更新器は未登録 node の実測追加を提供する (`tools/update_acceptance_duration_ledger.py:83-95,245-282`)。  
推奨: nodeid確定後、親が最初の post-commit focused run の JUnit を取得し、その実測を実装 author へ返す。author が `--add-only --coverage-against <collect出力>` で全3 nodeを ledgerへ追加し、親が再検査する。事前の推定値は書かない。

## 実行環境と meta-test の所見

所見 5: `cwd=_ROOT` により `PYTHONPATH` なしでも `-m` は解決する  
深刻度: nit  
根拠 (file:line): `_ROOT` と cwd は `test_s8c_gate_report.py:14-16,434-445`。CPython 3.10 は `-m` のコードを既存 `sys.modules["__main__"]` の辞書で実行する (`/usr/lib/python3.10/runpy.py:171-197`)。`env -u PYTHONPATH python3 -m site` の静的環境probeでも `sys.path[0]` は `_ROOT` だった。[CPython 3.10 `-m` 文書](https://docs.python.org/3.10/using/cmdline.html#cmdoption-m)  
推奨: `cwd=_ROOT` を固定すれば pytest の起動 directory/rootdir は子 process に影響しない。直接パス起動では `sys.path[0]` が script directoryになるため、production bootstrap は引き続き必要。

所見 6: 原案の full 評価 node は xdist 資源管理から漏れる  
深刻度: must-fix  
根拠 (file:line): real-repo lock/group は exact inventory の nodeだけへ付与される (`conftest.py:258-260,702-711,1995-2012,2080-2097`)。新規 `test_s8c_cli_entrypoints.py` は inventoryに無く、4 parameter subprocess が他の reader/writerと競合する。汎用 `serial` markerはない。  
推奨: 上記の構造観測案なら git full 評価をしないため分類追加は不要。full 評価を1件でも残すなら、base functionを `conftest.py` の parent-read inventoryと `test_real_repo_serialization.py:1501-1535` の独立 goldenへ追加すること。

所見 7: 新規 file を拾う meta-test はあるが、ledger/resource 漏れを自動検出するものではない  
深刻度: must-fix  
根拠 (file:line): `test_plain_runner_coverage.py:44-86` は全 `test_*.py` を列挙し、自走 harnessまたはallowlistを要求するため、計画の末尾 harnessなら通る。bootstrap形は `test_campaign_import_invariant.py:874-948,1002-1044,1226-1229` がtracked＋untracked campaign sourceを検査する。一方、hold collectionは登録済みkeyのstaleだけを見る (`conftest.py:2032-2064`)。duration ledgerにも全collection一致の常時meta-testはない。  
推奨: focused走へ `test_plain_runner_coverage.py`、`test_campaign_import_invariant.py`、ledger更新後の `test_update_acceptance_duration_ledger.py` を追加する。

所見 8: bootstrap位置、future import、coverage、import順に実害は見つからない  
深刻度: nit  
根拠 (file:line): future importは既に全通常importより前 (`s8c_preregistration.py:17-34`, `s8c_gate_report.py:8-16`)。新しい alias block は定数・class定義前だが、evaluator importは完全初期化後の `s8c_preregistration.py:1769-1777` まで起きず、通常importでは条件が偽。canonical bootstrap文字列自体も `test_campaign_import_invariant.py:41-43` が `# pragma: no cover` 込みで要求する。`pytest.ini:1-14` にcoverage gateはなく、ruff/isort/flake8設定も見当たらない。  
推奨: 計画の位置と `import sys` 順序でよい。pragmaは現行 subprocess coverageを緩めないが、将来childへcoverageを伝播する場合だけ再評価する。

## 焦点走対象集合の是正

所見 9: 11 file 集合は bootstrap meta-test を漏らしている  
深刻度: must-fix  
根拠 (file:line): 原集合は `s2-plan.md:217-231`。`s8c_gate_report.py` は relative importを持つmain-guard moduleなので、exact bootstrapを全campaign fileへ強制する `test_campaign_import_invariant.py:931-947,1226-1229` の直接対象になる。  
推奨: `orchestrator/tests/test_campaign_import_invariant.py` を必ず追加する。構造観測案なら `test_plain_runner_coverage.py` と、ledger更新後の `test_update_acceptance_duration_ledger.py` も追加する。

所見 10: enforcement/drift検査の漏れはないが、一部consumer fileは過剰である  
深刻度: nit  
根拠 (file:line): coreは現行・歴史closure双方に含まれる (`campaign_lock.py:49-68,117-142`)。`test_t671_source_binding.py:235-264,528-608` と `test_artifact_admission.py:2463-2470` がclosure/driftを閉じており、原集合に両方ある。一方 `p3_autonomous_workload_trial.py:52,954-973`、`trial_registry.py:43,4108-4137` は通常import consumerで、新しい `if __name__ == "__main__"` は実行しない。  
推奨: 最小焦点集合は新規file、`test_s8c_gate_report.py`、core/predicate/invariantの3 file、`test_campaign_import_invariant.py`、`test_t671_source_binding.py`、`test_artifact_admission.py`、plain-runner/ledger meta-test。`test_p3_autonomous_workload_trial.py`、`test_reflux_origin_binding.py`、`test_trial_registry.py` の全file走は安全な上乗せだが、今回差分への直接性は弱い。`test_ccbench_spawn_sites.py` も subprocess site数不変なので任意。

## 親 brief の前提判定 (P1〜P5)

所見 11: P1 は real  
深刻度: must-fix  
根拠 (file:line): canonical importは `s8c_preregistration.py:1769-1777`、相手側の再importは `s8c_preregistration_evidence.py:18`。返却型は同file `:1473-1483`、拒否はcore `:1739-1755`、握り潰しは `:1841-1856`。  
推奨: `_normalize_predicate_results` は変更せず、CLI `__main__` をcanonical keyへ直接代入する。

所見 12: P2 は real  
深刻度: must-fix  
根拠 (file:line): CPython 3.10の `-m` は対象codeを `sys.modules["__main__"].__dict__` で実行する (`/usr/lib/python3.10/runpy.py:171-197`)。現行 bootstrapは `__package__` が空のときしか動かない (`s8c_preregistration.py:36-38`)。  
推奨: alias blockはpackage bootstrapの外に置き、pathとmoduleのidentity subprocessを別parameterで検査する。

所見 13: P3 は一部 refuted  
深刻度: must-fix  
根拠 (file:line): g15はmodule blob keyを持たず、受理意味不変なのでDECIDER bump不要 (`condition-freeze.v1.g15.json:1`, `s8c_preregistration.py:41-55`)。しかしclosureにあるのはcoreだけ (`campaign_lock.py:64-66,132-134`) で、gate reportはない。実disk/HEAD drift拒否は `contract_loader_binding.py:348-382`。core自身もdirty bytesを `core-blob-mismatch` にする (`s8c_preregistration.py:1895-1904`)。  
推奨: 「coreのみHEAD blob束縛、gate reportは非closure」と訂正する。実rootのbinding/activationを踏む検査はcommit後に走らせるが、選択した全testが必ず `contract-loader-drift` になるという主張まではしない。

所見 14: P4 は real  
深刻度: nit  
根拠 (file:line): `_default_registry_results` は全例外を12件の `evaluator-exception` に変換する (`s8c_preregistration.py:1841-1856`)。今回の原因修正には不要。  
推奨: scope外のままでよい。診断改善と型検査緩和を混ぜない。

所見 15: P5 は real  
深刻度: blocker  
根拠 (file:line): 追補実測は39.17/114.16/118.74秒 (`brief-addendum.md:6-13`)。原案は8 full評価 (`s2-plan.md:81-82,101,147-153`) で、直列下限でも5分超。  
推奨: 所見3の構造観測案を採用し、新規 full評価を0回にする。どうしてもE2Eを残す場合でもcoreの1 invocationだけにし、他3 surfaceは構造/引数エラー検査へ落とす。

## 変異の提案と帰属

所見 16: core aliasをpackage bootstrap内へ戻す変異は単一帰属になる  
深刻度: must-fix  
根拠 (file:line): 変更予定位置 `s8c_preregistration.py:36-40`。pathでは `__package__` が空なのでaliasされるが、`-m` では空でなくaliasされない。  
推奨: 期待赤を `test_prereg_cli_main_is_canonical[module]` の1 nodeだけに固定して登録する。赤理由はcanonical/main identity不一致。

所見 17: gateの `__package__` 代入削除は単一帰属になる  
深刻度: must-fix  
根拠 (file:line): 変更予定位置 `s8c_gate_report.py:10-16`、相対importは現行 `:16`。代入を消すと直接パスだけがrelative ImportErrorとなり、`-m` は影響を受けない。  
推奨: 期待赤を `test_gate_path_invalid_arg_is_json_exit_two` の1 nodeに固定して登録する。

所見 18: `setdefault` とtest-file自身の変異は現設計では登録すべきでない  
深刻度: nit  
根拠 (file:line): `s2-plan.md:40` のとおり、clean subprocessではcanonical keyが空なので `setdefault` でも通り、既存instanceがある特殊経路だけで差が出る。また新規testのassertion反転はproduction欠陥ではなくtest自身の破壊である。  
推奨: preloaded canonical instanceを作る独立negative controlがない限り `setdefault` mutantは帰属不能として登録しない。test-file mutantもmutation matrixのproduction kill対象へ登録しない。

## 総括

所見 19: production修正は妥当だが、段2テスト計画はそのまま承認できない  
深刻度: blocker  
根拠 (file:line): core/gate bootstrap案は `s2-plan.md:17-61` で原因に整合する一方、4×2評価案は `:73-186` と追補 `brief-addendum.md:29-44` の時間制約に反する。焦点集合もcampaign bootstrap meta-testを欠く。  
推奨: production 2 fileの修正は維持し、新規testをidentity観測2 case＋gate invalid-arg 1 caseへ差し替える。focused集合とduration ledgerを補正する。pytestは実走しておらず、workspaceへの変更も行っていない。