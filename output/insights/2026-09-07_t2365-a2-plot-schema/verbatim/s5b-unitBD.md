## 総括

単位 BD を所有対象 3 ファイルだけに実装した。  
Lustre の `EINVAL` を create-only hard link へ退避し、既存宛先の拒否と非 `EINVAL` の送出を維持した。  
policy の新しい bytes hash は `67dce5a785dfc52d5df9b773f7a65905a030b7bd61ab7706704e2ed8e85a0487`。独立再計算と一致した。  
`protocol_sha256` は従来どおり `136b823e60a4b43e07dbbb4e3f8b5be48964226c955e143d59955325f0e0d9f4`。

## 変更点

- [paper_story_a2_certification.py:939](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-unit-bd/orchestrator/campaign/paper_story_a2_certification.py:939): `_rename_noreplace` が `EINVAL` の場合だけ、同一 directory の `os.link` による create-only 公開と staging unlink を実行するよう変更。
- [paper_story_a2_certification.v2.json:9](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-unit-bd/orchestrator/campaign/paper_story_a2_certification.v2.json:9): `tracked_destination` を `output/insights/2026-09-07_t2364-paper-story-a2-certification` へ変更。
- [test_paper_story_a2_certification.py:987](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-unit-bd/orchestrator/tests/test_paper_story_a2_certification.py:987): 共有 policy fixture の宛先を live policy と同期。
- [test_paper_story_a2_certification.py:1763](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-unit-bd/orchestrator/tests/test_paper_story_a2_certification.py:1763): policy bytes hash の assertion 2 箇所だけを張り直し。protocol golden は未変更。
- [test_paper_story_a2_certification.py:3711](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2365-unit-bd/orchestrator/tests/test_paper_story_a2_certification.py:3711): EINVAL 正例、既存名衝突の負例、非 EINVAL の負例を追加。

変更前の受理・拒否挙動: 完全な staging file は `RENAME_NOREPLACE` 成功時だけ受理され、既存名は拒否されたが、Lustre の `EINVAL` もそのまま送出され受領証を公開できなかった。  
変更後の受理・拒否挙動: `EINVAL` 時だけ hard link で完全な bytes を受理し、既存名は `EEXIST`、その他の errno は従来どおり送出して拒否する。

## 実走した検査

自走 harness、11 node 相当、すべて PASS:

- `test_condition_receipt_publish_is_atomic_noreplace_and_durable`
- `test_atomic_write_bytes_noreplace_einval_uses_create_only_hard_link`
- `test_atomic_write_bytes_noreplace_einval_hard_link_refuses_existing_name`
- `test_atomic_write_bytes_noreplace_non_einval_is_not_fallback`
- `test_p1_a2_default_policy_bytes_and_protocol_are_unchanged`
- `test_m11_materializer_stages_marker_before_single_noreplace_rename`
- `test_materialize_einval_uses_exclusive_claim_and_flags_zero_rename`
- `test_materialize_einval_refuses_destination_created_before_recheck`
- `test_materialize_einval_fails_closed_on_publish_claim_collision`
- `test_materialize_non_einval_publish_error_does_not_enter_fallback`
- `test_materialize_noreplace_success_does_not_enter_fallback`

加えて、worktree filesystem 上の無加工 `RENAME_NOREPLACE` 経路を実走し、hard-link fallback での初回公開と、再公開時の `EEXIST` 拒否・既存 bytes 保持を確認した。Python 構文、JSON parse、policy SHA-256 再計算も PASS。

test file 全体および repository 全体: 実装済み・未実走。指定された sandbox 制約に従い pytest CLI は使っていない。

## 所有外への波及

- `run_workload` は変更した writer を通じ、Lustre 上でも condition-gate receipt を生成できる。
- raw manifest 検証・materialize は同 receipt bytes を従来どおり消費する。directory 用 claim fallback は変更していない。
- 別単位の plotter は、新 leaf に materialize された condition receipt を consumer として読む可能性がある。
- 共有 `_policy` fixture を使う materialize 系 test の生成先が新 leaf に変わるが、fresh-leaf・既存先拒否の意味は不変。
- submitter/job wrapper、凍結済み insight、figures、results、plotter 本体・test には変更を加えていない。

## 未了・申し送り

親で test file 全体・関連全走・変異 M1/M2/M7 を実走し、修正済み固定 submit tree から新 attempt `t2364-20260907b` を投入する必要がある。commit・`git add`・docs 更新は行っていない。