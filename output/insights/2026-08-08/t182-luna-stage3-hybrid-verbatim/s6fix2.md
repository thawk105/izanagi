実装は完了しました。docs・git index・merge 状態には触れていません。

- `python3 tools/check_docs.py`: **rc=0**
  - 出力: `check_docs: 違反なし`
- `py_compile` / `git diff --check`: rc=0
- pytest: **実装済み・未実走**
  - 対象: `orchestrator/tests/test_check_docs.py -k dev_wave_model_pin`
  - `tools/run_tests.py` で2回試行しましたが、いずれも `qstat -Q preflight rc=1` による dispatch infrastructure failure（rc=16）で、pytest nodeid は開始されていません。

変更箇所:

- [tools/check_docs.py:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:264)
  - 追加: `DEV_WAVE_DW_O01_MODEL_AUTHORITY_LITERAL/FINDING`
  - 追加: `DEV_WAVE_OPERATIONS_OUTSIDE_DW_O01_MODEL_SLUG_ABSENCE_FINDING`
  - 追加: `DEV_WAVE_COMMAND_MODEL_SLUG_ABSENCE_FINDING`
  - 変更: `DEV_WAVE_WORKERS_MODEL_SLUG_ABSENCE_FINDING`
  - 削除: `CODEX_DEV_WAVE_STAGE_MODEL_LITERAL/LENS_LITERAL`
  - 削除: `CODEX_DEV_WAVE_STAGE_MODEL_FINDING/LENS_FINDING`
  - 削除: `DEV_WAVE_OPERATIONS_MODEL_SLUG_ABSENCE_FINDING`
- [_check_dev_wave_model_pins](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:3415) を新契約へ変更。呼び出し位置は [tools/check_docs.py:3670](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/tools/check_docs.py:3670)。
- [_write_command_guard_docs](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/tests/test_check_docs.py:432) で最小 fixture の権威行を `DW-O01` へ移設。
- model-pin テスト群は [test_check_docs.py:5147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/tests/test_check_docs.py:5147) 以降を更新。旧 dispatcher/lens テストを `DW-O01` authority テストへ改名し、command slug、O01 外 slug、O01 重複、最小 repo positive を追加しました。

Pin E の安全性については、`DW-O01` 外を別途走査するだけでなく、`DW-O01` 全体から権威 literal を除いた残余にも slug がないことを検査します。したがって節内で許されるのは、権威 literal に含まれる3出現だけで、本文への追記・見出しへの追加も Pin A 違反になります。

## 総括

- model 権威 pin を command から `DW-O01` へ移設した。
- workers、`DW-O01` 外、command の slug 不在を独立 pin にした。
- 指定された7 negative と節内追加・節重複を exact finding 1件で固定した。
- 最小 repo／現行 docs の positive を追加し、`check_docs` は rc=0。