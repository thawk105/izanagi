## 変更した内容

- [paper_story_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-author/orchestrator/campaign/paper_story_a2_certification.py:49)
  - 世代 ID と、独立した `frozenset` literal 2 個の世代表を追加しました（49–151）。
  - 公開 `load_policy(path=POLICY_PATH)` の署名を維持し、private 共通 loader へ分離しました（384–405）。
  - private 歴史 loader は exact `str` と登録済み世代を要求し、未知値へ fallback しません（389–401）。
  - 世代別 configure key 集合を完全 loader に渡し、FetchContent 値検査はその key を持つ世代だけに適用します（488–526）。

- [plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-author/tools/plotting/plot_a2_certification.py:57)
  - `HISTORICAL_CURRENT_POLICY_VIEWS` の値を世代 ID のみに置換しました。主 key は引き続き cert/policy SHA-256 pair です。
  - `_historical_policy_view` を全削除し、exact pair 一致時だけ producer の private 歴史 loaderへ渡します（168–215）。
  - `protocol_schema` と再計算済み `protocol_sha256` は共通 identity 検査が同値に照合します（219–222）。

- [test_plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-author/orchestrator/tests/test_plot_a2_certification.py:33)
  - 世代表 fixture、literal AST 検査、公開署名、未知・非文字列世代、実 t2364 統合を追加・更新しました（346–647）。
  - cert hash、policy hash、不正 `tracked_destination`、歴史側 `source_binding_status` の各負例を独立させました（658–736）。
  - `observe(path, **kwargs)` とし、未知 pair が引数なしの公開 current loaderへ流れることを固定しました（739–758）。
  - 指定された既存 test 名を含め、test の改名はありません。最終 `git status` はこの3 fileのみで、commit・add・新規 file はありません。

## 現行の受理・拒否挙動と、変更後の差

| 経路 | 変更前 | 変更後 |
|---|---|---|
| 公開 `load_policy()`、現行7-key policy | 受理 | 同じ文法で受理 |
| 公開 `load_policy()`、6-key policy | FetchContent key 欠落で拒否 | 同じ理由で拒否 |
| 公開 `load_policy(..., generation=...)` | 未対応 | 引き続き未対応。署名不変 |
| t2364 exact hash pair | 手書き3検査の歴史 view で受理 | producer の完全な歴史文法で受理 |
| cert hash または policy hash が異なる pair | current 文法へ流れて拒否 | 同じく拒否 |
| 未知・非 `str` 世代 | entry point なし | private entry point が `CertificationError` で拒否 |
| 登録済み歴史文法の不正 `tracked_destination` | 手書き parser 層では検出しない | 完全 loader が拒否 |
| 非 `bound` の歴史 cell | 後段で拒否 | 同じ後段で拒否 |

広がった受理は、新設したprivate entry pointが登録済み旧世代の正しい6-key policyを解析できる点だけです。公開 loader と production consumer の artifact 受理集合は広がっておらず、consumerからは登録済み exact hash pair の場合だけ到達できます。

## 実走結果

実装済み・pytest 未実走です。

- `tools/run_tests.py` で新設・変更した13 base nodeid、16 casesを要求しましたが、`qstat -Q` の認証エラーで rc=16、`child_started=false` でした。
- 許可された直接 pytest fallbackも Pegasus hook に拒否されました。pytest 内訳は緑0、赤0、未起動16 casesです。
- 制約 meta-testとして以下を洗い出して直接実走を試みましたが、同じ hook に拒否されました。
  - `test_update_acceptance_duration_ledger.py::test_g7e_checked_in_ledger_has_valid_schema_and_finite_durations`
  - `test_update_acceptance_duration_ledger.py::test_t1574_changed_suite_ledger_node_delta_is_exact`
- collect-only は [test_plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-author/orchestrator/tests/test_plot_a2_certification.py:1) 全体で77 casesの収集に成功しました。
- 非 pytest smoke は exit 0でした。現行 A-2/A-6 policy 2本、t2364歴史 policy、overrideなし実 root full load（4 cells、12 external inputs）を確認しました。
- 3 fileの構文、公開署名のAST、旧 adapter不在、`git diff --check` は成功しています。揮発 source hashは期待値に含めず、変更後 sourceのままcanonical実成果物を読めることも確認しました。

## 所有外への波及可能性

- producer CLI の current callerは [paper_story_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-author/orchestrator/campaign/paper_story_a2_certification.py:4970) のみで、引き続き公開 path-only loaderを使います。
- [test_paper_story_a2_job_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-author/orchestrator/tests/test_paper_story_a2_job_contract.py:604) の共有 `load_fixture_policy(path=...)` は署名上影響しませんが、未実走です。
- [test_paper_story_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-author/orchestrator/tests/test_paper_story_a2_certification.py:1813) のA-2 bytes/protocol pin、同 [A-6 loader検査](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2421-author/orchestrator/tests/test_paper_story_a2_certification.py:1954) は共有 loader 回帰先です。
- `perf_config_for_cell`、`_genome_for_cell`、`_exact_trace0_configure_argv`、`collect_results` は世代を保持しません。歴史 `Policy` は現状plot専用private経路からしか得られませんが、将来その戻り値をproducer実行へ流用してはなりません。
- 歴史 `Policy.path` は削除済み一時 fileを指します。現plot consumerは未使用ですが、新consumer追加時の注意点です。
- configure key以外のschema・値制約・protocol preimageは世代共有です。将来そこが締まればt2364が再び読めなくなる限界は残ります。

## 総括

裁定プランv2を指定3 fileへ実装し、裁定からの逸脱はありません。  
公開 loader の署名と現行受理集合、canonical hash、shipped policy bytesは維持しました。  
pytestは実行基盤に拒否されたため、成果は「実装済み・pytest未実走」です。  
段6ではplot test全体、producer policy test、job-contract test、上記meta-testを実走し、共有文法の将来ドリフト限界も確認してください。