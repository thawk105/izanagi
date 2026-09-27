## 変更点 (file:line)

- [tools/check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/tools/check_trace0_preprocess_identity.py:674): `_h_sources` は mode `160000`・type `commit` の gitlink を展開と file・blob 照合から除外し、旧新の path と commit OID の一致を確認します。symlink など他の非 regular file は従来どおり拒否します。
- [tools/check_trace0_preprocess_identity.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/tools/check_trace0_preprocess_identity.py:1051): gitlink の path と commit OID を `header_rule.gitlinks` に列挙します。
- [orchestrator/tests/test_check_trace0_header_rule.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/orchestrator/tests/test_check_trace0_header_rule.py:138): 一時 repo の index に gitlink を作る正例と、OID 変更が既存の diff 検証で拒否される負例を追加しました。

## 自走した確認と変異の赤化確認

header test の全 14 関数と指定の F7 consumer test を直接呼び出し、全件通過しました（計 **16.56 秒**）。gitlink 除外を一時的に外すと新しい正例は判定 job と同じ拒否理由で赤化しました（0.53 秒）。除外を戻し、`git diff` と `git diff --check` で一時変異が残っていないことを確認しました。

## 未実走・懸念

実 CCBench の判定 job と本体 build は未実走です。実機での通過結果はまだ確認していません。

## 波及の静的列挙

所有外では、[既存の `.cc` checker test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/orchestrator/tests/test_check_trace0_preprocess_identity.py:19)、[MOCC job contract test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/orchestrator/tests/test_mocc_trace_job_contract.py:28)、[MOCC pair test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/orchestrator/tests/test_mocc_trace_pair.py:404)、[checker を起動する pilot](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/tools/pegasus/mocc_trace_pilot.sh:1900) が関連します。指定の F7 test 以外は今回未実走です。header 引数なしの経路と `check()` の辞書 literal の `return` は変更していません。

## 総括

指定の 2 ファイルだけを編集し、gitlink が一致する header 差分を比較に進める修正と検証を完了しました。commit は作成していません。