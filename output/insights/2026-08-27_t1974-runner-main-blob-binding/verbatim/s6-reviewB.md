所見は 5 件です。すべて must-fix です。pytest は未実走で、以下は静的検査結果です。

- **所見 1: M1 と M4 は独立変異になっておらず、M4 は確実に生き残る**
- 種別: must-fix
- 根拠: 裁定は M1 を件数だけの違反、M4 を `set` 比較への緩和として登録していますが、M1 の `(0,1,2,0)` は件数と multiset の両方を破ります。[test_acceptance_launcher.py:472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_acceptance_launcher.py:472) 現実装は index 検査を `len(reports) == expected_k` で抑制して M1 を人工的に単独化しています。[acceptance_launcher.py:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/acceptance_launcher.py:347) 一方、M4 の `[0,0,2]` は `set` 化後も `{0,2} != {0,1,2}` なので同じ例外を送り、期待 node は成功したままです。[test_acceptance_launcher.py:502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_acceptance_launcher.py:502) 一般に「件数 exact K」と「index の set が K 個すべて」を同時要求すれば multiset equality と同値になるため、M4 は同値変異です。
- 反証条件: index 比較を実際に `set(...) != set(range(expected_k))` へ変え、`test_binding_reports_require_exact_index_multiset[dup]` が失敗すること。現 fixture では失敗しないはずです。
- 成果物影響: baseline の受領証値は変わりませんが、変異台帳は M4 を `SURVIVED` または `EQUIVALENT` とする必要があります。`12/12 KILLED` を根拠に land できません。

- **所見 2: M9 は現行 manifest に存在しない期待 digest の転記を要求しており、登録変異を構成できない**
- 種別: must-fix
- 根拠: 裁定自身が `runner_binding` を `tested_main / nonce / shard_count / shard_index` のみに限定し、「期待 digest を読み込まない」としています。[s4-adjudication.md:208](/home/SFC/tanab/.claude/jobs/b26675fa/tmp/wave-t1974/s4-adjudication.md:208) それにもかかわらず M9 は「manifest 期待値の転記」です。[s4-adjudication.md:232](/home/SFC/tanab/.claude/jobs/b26675fa/tmp/wave-t1974/s4-adjudication.md:232) 対応テストの binding にも期待 digest はなく、`subprocess.run` を全面 mock して source hash と stdin の object identity を別々に確認するだけです。[test_pegasus_dispatch_compute.py:4156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_pegasus_dispatch_compute.py:4156)
- 反証条件: request schema を変えずにコンパイル可能な M9 の exact patch を提示し、その patch が例外や欠落 key ではなく digest の受理差だけで期待 node を失敗させること。
- 成果物影響: M9 は現状 `KILLED` ではなく `INVALID` です。別 buffer や pathname bytes を hash する実在可能な変異へ事前登録を直さない限り、変異台帳と land 根拠が成立しません。

- **所見 3: M7 と M11 は単純な guard 削除だと受理集合不変の診断だけの赤になる**
- 種別: must-fix
- 根拠: M7 で shard guard を削除すると `int(None)` の `TypeError` になり、runner は起動しません。[acceptance_launcher.py:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/acceptance_launcher.py:136) テストは `LauncherFailure` と文言を要求するため赤になりますが、受理集合は広がりません。[test_acceptance_launcher.py:554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_acceptance_launcher.py:554) M11 も completeness guard の単純削除では、欠落 FD の添字参照が `KeyError` になります。[dispatch_compute.py:783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/pegasus/dispatch_compute.py:783) 対応 node は `ValueError("incomplete")` を pin しているので、scheduler 未到達のまま赤です。[test_pegasus_dispatch_compute.py:4265](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_pegasus_dispatch_compute.py:4265)
- 反証条件: M7 を未設定時に有効な既定 K を返す patch、M11 を部分 manifest を unbound として通す patchとして exact に固定し、それぞれ runner または scheduler 到達だけで node が失敗すること。
- 成果物影響:単純 line deletion を使うと M7、M11 が偽の `KILLED` になります。受入受領証が出ないままなのに台帳だけ kill と記録されるため、land 判定が誤ります。

- **所見 4: compute の bound request 検証から result 申告生成までを通るテストがない**
- 種別: must-fix
- 根拠: production の重要 seam は `_job_run` が request を検証し、main blob helper を呼び、`runner_report` を result payload に載せる箇所です。[dispatch_compute.py:1214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/pegasus/dispatch_compute.py:1214) [dispatch_compute.py:1256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/tools/pegasus/dispatch_compute.py:1256) しかし M8 は helper を直接呼び、M9 は `subprocess.run` を全面置換しています。login 側テストでは fake scheduler 自身が request を読み、production `_job_run` を通さず申告を合成しています。[test_pegasus_dispatch_compute.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_pegasus_dispatch_compute.py:151) したがって `_validated_runner_binding`、`_runner_binding_report`、result optional field のいずれを壊しても新規テスト群が検出しない経路があります。
- 反証条件: 完全な bound request を `_job_run` に渡すテストで、実 site/envelope 以外は最小限しか差し替えず、result の exact report を確認すること。特に lines 1221 または 1256 を削除した変異がその node だけで失敗する必要があります。
- 成果物影響: この seam が壊れると dispatcher 単体テストは通っても launcher が申告 0 件で拒否し、v5 受入受領証が生成されません。land は不可能になります。

- **所見 5: 差分外の real Git resume E2E は新契約と衝突し、baseline 全走を赤にする**
- 種別: must-fix
- 根拠: `test_resume_gate_then_postclaim_merge_runs_runner_once` は実 launcher を repo へ copy して実行します。[test_resume_gate_acceptance_boundary.py:248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_resume_gate_acceptance_boundary.py:248) しかし環境には shard K がなく、synthetic runner も fd 申告を書きません。[test_resume_gate_acceptance_boundary.py:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_resume_gate_acceptance_boundary.py:116) [test_resume_gate_acceptance_boundary.py:204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_resume_gate_acceptance_boundary.py:204) それでも rc 0、runner 1 回、receipt 成功を要求しています。[test_resume_gate_acceptance_boundary.py:379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_resume_gate_acceptance_boundary.py:379) 同型全走査では、ほかの real launcher positive E2E は共通 `_write_exact_runner` と明示 K=1 で更新済みでした。
- 反証条件: 外部から shard 環境を偶然継承しない隔離環境でこの node が rc 0となり、正規申告を観測できること。
- 成果物影響: baseline 全走が成立せず、変異 matrix 全体が無効です。受入受領証は出ず、land と台帳確定の双方を止めます。

## 軸別照合

M1 から M12 の期待 node 名は裁定表と逐語一致しています。M4 の `[dup]` を含め、新規 parametrize id は ASCII のみです。

単一理由性は、M2、M3、M5、M6、M8、M10、M12 は成立、M1 は実装上の条件分岐に依存、M4 は不成立、M9 は変異不能、M7 と M11 は exact mutation patch 次第です。診断文言だけの変更でも、各 `pytest.raises(..., match=...)` は赤になりますが、これは kill に数えられません。

実 launcher を copy し、positive path で走らせる test は次です。

- `test_dev_wave_wait.py`: `test_real_git_self_report_allows_main_only_implementation_merge`、`test_default_wiring_with_real_git_and_lease_helper`、`test_real_waiter_process_accepts_merged_tip_with_same_waiter_bytes`、`test_default_wiring_second_acceptance_reuses_self_held_lease`、signal 2 本。
- `test_resume_gate_acceptance_boundary.py`: 所見 5 の 1 本。

preflight や provenance で launcher 前に止まる copy-only test は、untracked、`PYTEST_ADDOPTS`、malformed provenance、combined self-report、waiter bytes mismatch の 5 本です。

request schema 全 key 集合を exact equality で pin する既存 test はありません。近い consumer は `test_pegasus_dispatch_compute.py` の request environment、canonical request hash、provenance/tests task field の各検査、`test_run_tests_preflight.py:829`、`test_mutation_harness.py:169` の synthetic v2 request です。いずれも manifest 無しでは optional `runner_binding` が増えないため、静的には衝突しません。

dispatcher 内容走査は `test_pegasus_dispatch_compute.py` の infra-return AST と qdel caller scan、`test_check_docs.py` の実 TASKS parser、`test_site_policy.py` の future import、さらに repo 全体を読む build-authority、certified-writer、login-headroom、submission-receipt call-site scan です。追加コードは各対象 predicateに触れておらず、静的な新衝突は見つかりませんでした。

既存 assert の削除、反転、緩和、skip はありません。K=1 の明示で自動 shard 注入を見なくなった部分は、専用の注入 test が [test_dev_wave_wait.py:3392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1974-runner-main-blob-binding/orchestrator/tests/test_dev_wave_wait.py:3392) 以降に残っているため、元の検出力低下とは判定しません。

新規 test file はありません。file 集合を見るのは `test_plain_runner_coverage.py` と verifier/oracle 名を走査する `test_pytest_collection_config.py:423` です。前者では変更済み launcher test の自走 harness が残り、追加 parametrize test も default 引数で自走可能です。揮発する hash、時刻、pid、固定絶対 path の新規焼き込みもありません。

## 総括

最重所見は、M1 と M4 が論理的に独立せず、M4 が同値変異として生き残ることです。  
親が最初に測るべきものは M4 の exact `set` 変異と期待 nodeで、成功のままなら `SURVIVED` が確定します。  
次に resume E2E を単独 baseline で測り、新契約用 fixture 更新を scope に入れる必要があります。  
pytest は本レビューでは実走していません。