## 実装した内容

- plan v2 1: [_canonical_full_report](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4736) を追加。authority 検査後、旧 full collector 分岐を同一ロジックで再利用可能にした。
- plan v2 2: [_collect_command](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4778) の full 分岐を canonicalizer 呼び出しへ置換。
- plan v2 3–4: [_validate_certification_result](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4526) の既存 full 検査後に、v4 限定の acquisition 再読・report 再導出・完全一致検査を追加。canonical evidence を返す。`materialize` 本体・schema・成果物形は不変。
- plan v2 5: [_full_materializer_forgery_case](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:2998) と、指定された偽 status・偽 effects・偽 driver_rcs/indeterminate の3負例を追加。既存正例にも [canonicalizer 同一性検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:2432) を追加。
- plan v2 6: synthetic 正例はそのまま通ったため構築変更なし。

## 現行挙動と変更後挙動

変更前の full v4 は、shape・identity・schema chain・request IDs・固定 field・cells・historical/indeterminate 形を検査していたが、正の acquisition に対する偽 status、偽 effects、偽 driver_rcs と整合する indeterminate report を受理していた。

変更後は既存検査を同じ evidence に対して全て終えた後、acquisition を読み直して full report 全体を再導出する。不一致は `certification result differs from evidence re-derivation` で拒否され、成果物は作られない。正常 report は従来どおり受理され、receipt bytes は canonical evidence から materialize される。

legacy v3 full、legacy v1 partial、v2 partial の受理・拒否挙動は変更していない。

## 実走した検査

- 自走 harness 全範囲:
  `PYTHONPATH=. python3 orchestrator/tests/test_paper_story_a2_certification.py`
  - rc=0
  - 173 passed / 0 failed
  - 範囲: `orchestrator/tests/test_paper_story_a2_certification.py` 全 node

- 新規3 node、最終状態:
  - `...::test_full_materializer_rejects_forged_status_from_positive_evidence`
  - `...::test_full_materializer_rejects_forged_effects_from_positive_evidence`
  - `...::test_full_materializer_rejects_indeterminate_report_from_full_success_acquisition`
  - rc=0、3 passed / 0 failed

- 変更前挙動 probe:
  - 新しい v4 再導出条件だけを一時的に到達不能にして同3 node を実行。
  - rc=1、3 failed。全件が `DID NOT RAISE CertificationError` となり、旧挙動では materialize が成功することを確認。
  - 直後に変更を復元し、上記3 passed を再確認済み。

- meta-test:
  - `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
  - `test_allowlist_has_no_stale_or_self_runnable_entries`
  - `test_every_test_file_is_self_runnable_or_allowlisted`
  - rc=0、3 passed / 0 failed

- `git diff --check`: rc=0
- 対象2ファイルの AST parse: rc=0
- `python3 -m pytest`、`tools/run_tests.py`、repository 全体 suite は実行していない。

## 波及可能性

- production の直接 caller は同ファイル内の `_collect_command` のみ。full `collect` CLI は正常入力で二度目の acquisition 読み直しを行う。
- 指定2ファイル外に `materialize`、`_validate_certification_result`、`_canonical_full_report` の直接 caller は見つからなかった。
- `tools/plotting/plot_a2_certification.py` と `test_plot_a2_certification.py` は producer の policy/cell 検査を利用するが、materializer は呼ばない。
- `test_paper_story_a2_job_contract.py` と Pegasus wrapper は同 module の preregister・実行・finish 経路を使うが、静的には full collect/materialize の直接 consumer ではない。
- test-local共有 fixture `_policy`、`_write_receipt_bundle` は新規3負例から利用するが変更していない。

## 未了・判断を仰ぐ点

plan の「既存 identity/schema 検査を canonical evidence へ切り替える」案は裁定と衝突するため採用せず、既存検査を渡された evidence に据え置いた。その後にだけ再読・再導出を追加した。

acceptance duration ledger は指示どおり編集していない。新規3 node の add-only 登録は親の段7作業として残る。判断を仰ぐ実装上の点はない。

## 総括

full v4 materializer に acquisition 再読・canonical report 再導出・完全一致拒否を追加した。  
既存検査順、legacy/partial 経路、schema、成果物形式は維持した。  
新規3負例は旧挙動で materialize 成功、最終実装で全件拒否されることを実測した。  
変更は指定された2ファイルのみで、commit は作成していない。