## 判定

- FIX-10: **partial（実装済み・未実走）**
- FIX-11: **partial（実装済み・未実走）**

環境制約どおり pytest は実行しておらず、緑は主張しません。

### FIX-10

原因は source path の不一致です。

- backoff fixture の既定値は `_SRC_REL = "backoff.hh"` で、従来は一時ディレクトリ直下へ作成していました。[test_p3_s4_loop.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop.py:67)、[test_p3_s4_loop.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop.py:97)
- inner が呼ぶ `quarantine()` の既定値は `SOURCE_REL = "include/backoff.hh"` で、`os.path.join(sub, source_rel)` を直接 `open()` します。[p3_s4_loop.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop.py:88)、[p3_s4_loop.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop.py:185)、[p3_s4_loop.py:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/campaign/p3_s4_loop.py:216)
- sort 版は `_SRC_REL = S.SOURCE_REL` とし、`os.makedirs()` でネストした実パスを作るため、親実走ではこの不一致がありませんでした。[test_p3_s4_loop_sort.py:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_sort.py:57)、[test_p3_s4_loop_sort.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_sort.py:68)

修正後は対象テストが `_mk_template_dir(L.SOURCE_REL)` を渡し、`include/backoff.hh` を事前作成します。[test_p3_s4_loop.py:1142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop.py:1142)  
したがって、従来の `/tmp/.../include/backoff.hh` 不在経路には入りません。

### FIX-11

対象テストを次の形へ変更しました。

- 有効な一時 source tree と制御済み `patchharness.applied` context を使用。[test_p3_s4_loop_trigger_gating.py:1918](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1918)、[test_p3_s4_loop_trigger_gating.py:1955](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1955)
- coder の実 wire から predicate を生成し、その predicate と `_G` から `diffq_variant_id` を計算。[test_p3_s4_loop_trigger_gating.py:1915](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1915)
- digest が実 working diff と一致する `verdict="reject"` auditor に固定。[test_p3_s4_loop_trigger_gating.py:1919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1919)
- 現 seam では WAL bytes 不変、record 列が `[trigger_binding, build_start]` のまま、replay と artifact admission が受理することを直接 assert。[test_p3_s4_loop_trigger_gating.py:1969](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1969)
- identity-only seam をテスト内で実際に注入し、二つ目の binding/start/abort が追記されることを attempt ID まで照合。[test_p3_s4_loop_trigger_gating.py:1984](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1984)、[test_p3_s4_loop_trigger_gating.py:1997](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1997)
- mutant WAL は topology replay と artifact admission の双方が「同一 variant に未終端 attempt」で拒否することを直接 assert。[test_p3_s4_loop_trigger_gating.py:2023](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:2023)

MU-12 の実装変異を当てると、最初に [WAL bytes 不変 assert](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t459-resume-topology/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1969) が赤になります。期待値は seed の2 record bytes のままですが、実値には `trigger_binding → build_start → abort` の3 record が追加されます。続く stage assert でも、期待する2要素 `[binding,start]` に対し実値は5要素 `[binding,start,binding,start,abort]` です。

## 変更範囲と検査

変更したのは以下だけです。

- `test_p3_s4_loop.py::test_inner_run_recovers_reject_start_before_writing_retry_start`
- `test_p3_s4_loop_trigger_gating.py::test_inner_run_reject_start_crash_fails_before_second_start`
- 後者で `ArtifactAdmissionError` の import を追加

本体コード、docs、共有 fixture は変更していません。既存テストへの波及はなく、追加 helper は FIX-11 のテスト関数内だけです。

実施済みの静的検査:

- `python3 -m py_compile`：成功
- `git diff --check`：成功
- `python3 tools/check_codex_agents.py`：成功
- `python3 tools/check_docs.py`：成功
- pytest：**未実走**

## 総括

- FIX-10: partial — 正しい `include/backoff.hh` fixture を作るよう修正済み・未実走。
- FIX-11: partial — 実 predicate、決定的 reject、WAL/topology/admission 差を固定済み・未実走。
- identity-only 変異では2 record が5 recordへ増え、byte不変 assert が直接赤になる。
- 本体コード・docs・共有 fixture は変更していない。
- commit、git add、branch 操作は行っていない。