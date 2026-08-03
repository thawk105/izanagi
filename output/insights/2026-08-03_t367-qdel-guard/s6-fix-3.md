4件すべて対応しました。編集は指定された2ファイルのみで、commit は作成していません。

| 項目 | 状態 | 対応 |
|---|---|---|
| H1 | closed | field 別に既存 parser の語彙を適用。[dispatch_compute.py:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:241)、交差形3件の qdel ゼロテストを追加。[test_pegasus_dispatch_compute.py:888](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:888) |
| H2 | closed | qdel 結果固定後の `_capture` 例外から outer `except` へ入り、once-only guard が再 claim を防ぐテストを追加。[dispatch_compute.py:1425](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1425)、[test_pegasus_dispatch_compute.py:1362](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1362) |
| H3 | closed | default argument の scoped alias と単純 tuple/list unpacking の伝播を scanner に追加し、両 synthetic shape を固定。[test_pegasus_dispatch_compute.py:1407](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1407) |
| H4 | closed | `\s` を含む docstring を raw string 化。[dispatch_compute.py:271](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:271)。2ファイルを warning-as-error の in-memory compile で確認し、invalid escape warning はありませんでした。 |

前回 fix からの受理集合差は明確に縮小方向です。全 field 共通だった語彙を既存 parser の field 別語彙へ限定し、少なくとも `Request State=Queued`、`Request State=Waiting`、`Current State=QUE` は `UNKNOWN` となり qdel を発行しません。新たな受理形は追加していません。

pytest・変異テストは実行しておらず、緑は主張しません。親が走らせるべき focused nodeid は以下です。

- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_fresh_qstat_gate_rejects_state_vocabulary_from_wrong_field`
- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_fresh_qstat_gate_accepts_que_hld_and_stg_snapshots`
- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_fresh_qstat_gate_accepts_current_state_only_snapshots`
- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_cleanup_claim_latch_survives_post_qdel_capture_exception`
- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_best_effort_qdel_reference_scanner_covers_bypass_shapes`
- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_best_effort_qdel_production_caller_is_only_fresh_gate`

## 総括

H1〜H4 はすべて closed。裁定外だった state 文法を縮小し、M11 と alias scanner の検出穴を回帰テストで固定しました。所見2の receipt 永続化競合窓には触れていません。