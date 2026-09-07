## 実装した内容

- [paper_story_a2_certification.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2198-author/orchestrator/campaign/paper_story_a2_certification.py)
  - FetchContent 4-prefix の loader 検査と closed argv 文法を追加。
  - staged 3依存の S8b verifier、condition gate の offline 化、receipt 観測、5値 forwarding を実装。
  - `--third-party-source-root` と qsub env key を必須化。
- [A-2 policy](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2198-author/orchestrator/campaign/paper_story_a2_certification.v2.json) / [A-6 policy](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2198-author/orchestrator/campaign/paper_story_a6_certification.v2.json)
  - ordered 4-prefix grammar を指定位置へ追加。
- [submitter](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2198-author/tools/pegasus/submit_paper_story_a2_certification.sh)
  - hydrate 配置 `<root>/{masstree,mimalloc,googletest}` を検証。
  - unsafe 値、symlink、欠落 directory を拒否し、qsub と receipt に同一 env 値を記録。
- [compute job](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2198-author/tools/pegasus/paper_story_a2_certification.sh)
  - 3依存を job-local `<name>-src` へ exact copyし、`run-workload` へ渡すよう変更。
- [certification tests](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2198-author/orchestrator/tests/test_paper_story_a2_certification.py) / [job contract tests](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2198-author/orchestrator/tests/test_paper_story_a2_job_contract.py)
  - A-2/A-6 exact grammar、5箇所の golden、全5直接 caller、M1〜M16 対応 test、runtime kwargs・順序・copy 契約を更新。

docs、insight、README、凍結記録は未編集です。commit、push、branch 作成も行っていません。

## 実走結果

- `orchestrator/tests/test_paper_story_a2_certification.py`: rc=0、154 passed。
  - `::test_policy_loader_rejects_each_malformed_fetchcontent_prefix_list[*]`
  - `::test_condition_gate_uses_exact_offline_fetchcontent_argv`
  - `::test_run_workload_verifies_staged_sources_before_condition_gate`
  - `::test_official_run_observes_dependency_receipt_after_condition_prebuild`
  - `::test_official_run_forwards_exact_fetchcontent_five_tuple`
  - `::test_submission_rejects_missing_or_changed_third_party_source_root[*]`
  - trace0 の prefix、順序、短い segment、closed grammar 各 nodeidを含め全 PASS。
- `orchestrator/tests/test_paper_story_a2_job_contract.py`: rc=0、56 passed。
  - `::test_job_body_stages_exact_three_src_suffixed_dependencies` PASS。
- `orchestrator/tests/test_buildcache_v2.py`: rc=0、216 passed。指定された2つの FetchContent transport nodeidも PASS。
- `orchestrator/tests/test_official_perf_closure.py`: rc=0、7 passed。
- `orchestrator/tests/test_ccbench_spawn_sites.py`: rc=0、44 passed。
- `orchestrator/tests/test_hooks.py`: rc=0、474 passed、1 skipped。
- `test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed` は PASS。その後、既存自走 runner の fixtureなし実行による所有外エラーが続いたため全走は rc=130 で停止。
- `test_p3_s4_loop.py` の指定3 nodeidは実装済み・未実走。既存自走 runner が pytest fixture/parametrize を介さず直接呼び、対象到達前に `TypeError` となったため rc=130 で停止。
- `py_compile`、`bash -n`、`git diff --check`: rc=0。

## 導出した golden

編集後の各 policy に対して `hashlib.sha256(path.read_bytes()).hexdigest()` と `load_policy(path).protocol_sha256` を実行しました。

- A-2 bytes: `2e97d69b60b73a1395d6b5efdc0198ee0cfbf84cfb48cabed442e705e64f41ea`
- A-2 protocol: `d99f08bcc50c605d24d443d387a2c3144c16b9e670c9b9e247227c5db1be7f9c`
- A-6 bytes: `8969a7e4ee740a94ec12084c89ef88a37ebd255073cfb0122245113a295b87a8`
- A-6 protocol: `21427e71793ea744777d11bd90429ce2db1a8d3333ea9e2e0f227ecf377c25dc`

最終状態でも再導出し、test literal と一致することを確認しました。

## 現行の受理・拒否挙動の変化

- trace0 は dependency prefix、FetchContent base、source 3本、controlled defines の exact 順序だけを受理します。
- FetchContent 4値は非空の絶対 path が必須です。欠落、追加、並べ替え、prefix 改変、相対 path、`FULLY_DISCONNECTED` は拒否します。
- 旧 FetchContent token なし argv は新 protocol では拒否されます。
- submitter は hydrate の末尾 `-src` なし配置を受理し、compute job が `-src` 配置へ変換します。
- staged dependency の pin・clean・Git root 検査失敗は `CertificationError`、verifier 固定引数の `ValueError` は未変換で上がります。
- 新 env key を欠く旧 submission receipt は現行 exact qsub 契約では拒否されます。

## 波及の静的列挙

- 所有外 consumer は既存の `loop.run_campaign`、`pipeline.evaluate`、`buildcache` の5値 seam。変更せず利用しています。
- A-2/A-6 は同じ submitter、job body、env keyを共有します。
- 共有 fixture `_positive_results`、`_write_receipt_bundle`、submitter/compute harness を新契約へ更新しました。
- consumer inventory は `test_campaign.py`、`test_ccbench_spawn_sites.py`、`test_official_perf_closure.py`、`test_hooks.py`。
- policy bytes/protocol hash と job-body hash が変わるため、過去の receipt/provenance は現行契約へ再選択されません。歴史記録は未変更です。

## 未了・停止した項目

- M1〜M16 の kill-target test baseline は緑ですが、mutation injection 自体は指定された自走 harness の範囲外のため未実走です。
- `test_p3_s4_loop.py` の指定3 nodeidと `test_campaign.py` 全体は、上記の既存自走 runner 制約により closed を申告しません。
- 3依存 copy の実サイズ、scratch 容量、所要時間は段4裁定どおり未実測です。
- D1693 の insight・台帳・旧結果注記は親の所有範囲です。

## 総括

A-2/A-6 の測定 build を、閉じた trace0 文法を保ったままオフライン依存へ配線しました。
hydrate 配置から job-local `-src` 配置への実行経路を閉じています。
主要2 harness は合計210件すべて PASSし、関連 consumer harness も緑です。
変更は許可されたコード、test、policy、shellの7 fileだけに残しています。
commit と docs 更新は行っていません。